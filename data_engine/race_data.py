"Use data for Fernando Alonso's fastest lap, FP3, Bahrain GP, 2025"

import fastf1 as f1
import fastf1.plotting
import seaborn as sns
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import warnings
import datetime

from db_utils.supa_db import DriverData, SessionData, StintData, LapData, WeatherData, create_driver_data, create_session_data, create_stint_data, create_lap_data, create_weather_data
from db_utils.database_service import F1Database as db

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

## Fun example code for visualization

def get_lap(year, gp, ses, driver):
    session = f1.get_session(year, gp, ses)
    session.load()
    lap = session.laps.pick_drivers(driver).pick_fastest()
    return lap

def get_lap_segments(lap):
    x = lap.telemetry['X']
    y = lap.telemetry['Y']
    points = np.array([x,y]).T.reshape(-1,1,2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    return segments

def get_fastest_lap_telemetry(year, gp, ses, driver):
    lap = get_lap(year, gp, ses, driver)
    car_data = lap.get_car_data().add_distance()
    telemetry = lap.telemetry.add_distance()
    telemetry.drop('DriverAhead', axis=1, inplace=True)
    telemetry.drop('DistanceToDriverAhead', axis=1, inplace=True)
    return telemetry

## Data code in use

def store_session_stints(year: int, gp: str, driver: str, ses: str):
    """Store session data, stints, and laps directly in database"""
    try:
        session = f1.get_session(year, gp, ses)
    except Exception as e:
        print(f"Exception in retrieving session: {e}")
        return 
    session.load()
    weather_data = session.weather_data
    date = session.date.to_pydatetime()
    event_weather = "wet" if weather_data["Rainfall"].any() else "dry"

    # Store session
    session_data = create_session_data(gp, date, ses, event_weather, year)
    session_response = db.store_session(session_data)
    session_id = session_response["data"][0]["id"] if session_response and session_response["data"] else None
    
    if not session_id:
        print("Failed to store session, aborting...")
        return

    laps = session.laps.pick_drivers(driver)
    laps = filter_laps(laps)
    # Store driver if first session
    if len(laps) == 0:
        print(f"Driver did not take part in {gp, ses, year}")
        return
    driver_number = laps.iloc[0]["DriverNumber"]
    team = laps.iloc[0]["Team"]
    driver_data: DriverData = {
            "driver_name": driver, "driver_number": driver_number, "team": team
    }
    if ses == "FP1":
        driver_response = db.store_driver(driver_data)
        driver_id = driver_response["data"][0]["id"] if driver_response and driver_response.get("data") else None
    else:
        driver_id = db.get_driver_id(driver_data)
    
    laps_by_stint = laps.groupby('Stint')
    for stint_number, stint_laps in laps_by_stint:
        print(f"Processing Stint {stint_number}")
        store_stint(stint_laps, session_id, driver_id, session)

def store_stint(laps, session_id, driver_id, session):
    first_lap = laps.iloc[0]
    stint_data = create_stint_data(session_id, driver_id, first_lap, len(laps))

    print(f"Stint Number: {laps.iloc[0]["Stint"]}")

    stint_response = db.store_stint(stint_data)
    stint_id = stint_response["data"][0]["id"]

    store_laps(laps, session_id, stint_id, session)

def match_and_store_weather(time_of_lap, session_id, session):
    """Match weather and store, return weather_id"""
    if pd.isna(time_of_lap):
        return None
    weather_data = session.weather_data
    time_diffs = abs(weather_data['Time'] - time_of_lap)
    within_minute = time_diffs <= pd.Timedelta(minutes=1)
    if within_minute.any():
        closest_idx = time_diffs[within_minute].idxmin()
        weather_row = weather_data.loc[closest_idx]

        absolute_time = session.date + weather_row["Time"]

        weather_data_dict = create_weather_data(session_id, weather_row, absolute_time)
        
        weather_response = db.store_weather(weather_data_dict)
        return weather_response["data"][0]["id"] if weather_response and weather_response["data"] else None
    return None

def store_laps(laps, session_id, stint_id, session):
    # Process and store each lap directly
    for _, lap_row in laps.iterrows():
    # Get weather_id for this lap
        weather_id = match_and_store_weather(lap_row["Time"], session_id, session)

        lap_data = create_lap_data(stint_id, weather_id, lap_row)
        
        db.store_lap(lap_data)
    
def filter_laps(laps):
    return laps.loc[(laps['Deleted'] == False) &
                         (laps['LapTime'].notna()) &
                         (laps['PitOutTime'].isna()) &
                         (laps['PitInTime'].isna()) &
                         (laps['TrackStatus'] == '1')].copy()

def store_weekend_data(year: int, gp: str, driver: str):
    """Store complete weekend data"""
    store_session_stints(year, gp, driver, "FP1")
    store_session_stints(year, gp, driver, "FP2")
    store_session_stints(year, gp, driver, "FP3")
    store_session_stints(year, gp, driver, "Qualifying")
    store_session_stints(year, gp, driver, "Race")
    print(f"Stored complete weekend data for {driver} at {gp} {year}")

def get_cleaned_stint_data(driver_data, stint):
    cleaned_stint_laps = []
    if stint['num_laps'] < 5:
            return
    laps = db.get_stint_laps(stint['id'])
    lap_times = [lap['lap_time'] for lap in laps]
    
    median_time = np.median(lap_times)
    threshold = 3.0

    for lap in laps:
        lap = add_weather_to_lap(lap)
    prev_lap = laps[0]
    for i in range(1, len(laps)):
        lap = laps[i]
        lap = add_lap_time_delta(lap, prev_lap['lap_time'])
        lap = add_weather_rate_change(lap, prev_lap)
        prev_lap = lap

    selected_laps = [lap for lap in laps if lap['lap_time'] <= median_time + threshold]

    if len(selected_laps) < 2:
        return
    
    for lap in selected_laps:
        lap['stint_number'] = stint['stint_number']
        lap['tyre_compound'] = stint['tyre_compound']
        lap['session_type'] = stint['session_type']
        lap = add_weather_to_lap(lap)
        cleaned_stint_laps.append(lap)
    return cleaned_stint_laps

def get_cleaned_weekend_data(driver_data, event, year):
    all_stints = db.get_driver_stints(driver_data, event, year)
    cleaned_laps = []
    for stint in all_stints:
        cleaned_laps += get_cleaned_stint_data(driver_data, stint)
    return pd.DataFrame(cleaned_laps)

def get_cleaned_session_data(driver_data, event, session, year):
    all_stints = db.get_driver_stints_by_session(driver_data, event, year, session)
    cleaned_laps = []
    for stint in all_stints:
        cleaned_laps += get_cleaned_stint_data(driver_data, stint)
    return pd.DataFrame(cleaned_laps)

def add_lap_time_delta(lap, prev_lap_time):
    lap['lap_time_delta'] = lap['lap_time'] - prev_lap_time
    return lap

def add_weather_rate_change(lap, prev_lap):
    if lap and prev_lap:
        lap['air_temp_change'] = lap['air_temp'] - prev_lap['air_temp']
        lap['track_temp_change'] = lap['track_temp'] - prev_lap['track_temp']
        lap['humidity_change'] = lap['humidity'] - prev_lap['humidity']
    else:
        fields = ['air_temp_change', 'track_temp_change', 'humidity_change']
        for field in fields:
            lap[field] = None
    return lap

def add_weather_to_lap(lap):
    weather_id = lap['weather']
    weather = db.get_lap_weather(weather_id)

    if weather:
        lap['weather_time'] = weather['time']
        lap['air_temp'] = weather['air_temp']
        lap['track_temp'] = weather['track_temp']
        lap['pressure'] = weather['pressure']
        lap['rainfall'] = weather['rainfall']
        lap['humidity'] = weather['humidity']
        lap['wind_direction'] = weather['wind_direction']
        lap['wind_speed'] = weather['wind_speed']
    else:
        weather_fields = ['weather_time', 'air_temp', 'track_temp', 'pressure', 'rainfall', 'humidity', 'wind_direction', 'wind_speed']
        for field in weather_fields:
            lap[field] = None
    return lap

def get_all_weekend_laps(event, year):
    drivers = db.get_all_drivers()
    driver_dfs = []
    for driver in drivers:
        driver_data = create_driver_data(driver['driver_name'], driver['driver_number'], driver['team'])
        driver_dfs.append(get_cleaned_weekend_data(driver_data, event, year))
    all_weekend_laps = pd.concat(driver_dfs, ignore_index=True) ## issue in concatenation: objects are lists and can only concat Series and DFs
    return all_weekend_laps

if __name__ == "__main__":
    
    event = "Australia"
    year = 2025
    driver = create_driver_data("HAM", 44, "Ferrari")

    wknd_laps = get_cleaned_weekend_data(driver, event, year)

""" Stored for NOR, VER, LEC, ALO, SAI, HAM

NOR: Bahrain 2023, Saudi Arabia 2023, Australia 2023, Miami 2023
VER: Bahrain 2023, Saudi Arabia 2023, Australia 2023, Miami 2023
LEC: Bahrain 2023, Saudi Arabia 2023, Australia 2023, Miami 2023
ALO: Bahrain 2023, Saudi Arabia 2023, Australia 2023, Miami 2023
SAI: Bahrain 2023, Saudi Arabia 2023, Australia 2023, Miami 2023

LEC: Australia 2025, China 2025, Japan 2025, Bahrain 2025
HAM: Australia 2025, China 2025, Japan 2025, Bahrain 2025


Target data distribution per weekend:
SOFT compound: 20-25 laps (2-3 stints)
MEDIUM compound: 20-25 laps (2-3 stints)  
HARD compound: 15-20 laps (1-2 stints if available)
Total: 55-70 laps per driver per weekend


"""