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

from supa_db import DriverData, SessionData, StintData, LapData, WeatherData, create_session_data, create_stint_data, create_lap_data, create_weather_data
from database_service import F1Database as db

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
    session = f1.get_session(year, gp, ses)
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
    
    print(f"Successfully stored {len(laps)} laps for {driver} in {gp} {year}")

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
    print(f"Stored complete weekend data for {driver} at {gp} {year}")

def get_cleaned_weekend_data(driver_data, event, year):
    all_stints = db.get_driver_stints(driver_data, event, year)
    cleaned_laps = []
    for stint in all_stints:
        print(stint)
        if stint['num_laps'] < 5:
            continue
        laps = db.get_stint_laps(stint['id'])
        lap_times = [lap['lap_time'] for lap in laps]
        
        median_time = np.median(lap_times)
        threshold = 3.0

        selected_laps = [lap for lap in laps if lap['lap_time'] <= median_time + threshold]

        if len(selected_laps) < 2:
            continue
        
        for lap in selected_laps:
            lap['stint_number'] = stint['stint_number']
            lap['tyre_compound'] = stint['tyre_compound']
            lap['session_type'] = stint['session_type']
            cleaned_laps.append(lap)

    return pd.DataFrame(cleaned_laps)

if __name__ == "__main__":
    year = 2023
    gp = "Saudi Arabia"
    driver = "SAI"
    
    store_weekend_data(year, gp, driver)

# Stored for NOR, VER, LEC, ALO

# NOR: Bahrain 2023, Saudi Arabia 2023
# VER: Bahrain 2023, Saudi Arabia 2023
# LEC: Bahrain 2023, Saudi Arabia 2023
# ALO: Bahrain 2023, Saudi Arabia 2023
# SAI: Bahrain 2023, Saudi Arabia 2023

# Target data distribution per weekend:
# SOFT compound: 20-25 laps (2-3 stints)
# MEDIUM compound: 20-25 laps (2-3 stints)  
# HARD compound: 15-20 laps (1-2 stints if available)
# Total: 55-70 laps per driver per weekend

