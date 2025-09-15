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

from supa_db import DriverData, SessionData, StintData, LapData, WeatherData
from database_service import F1Database as db


# Global variables for now

# Function that gets lap (get_session, race weekend, event), get_driver, get_fastest_lap, etc.
# Functions that get data - telemetry data of lap, weather data, track data
# Visualization functions 

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

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

def track_plot(year, gp, ses, driver):
    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(12,6.75))
    fig.suptitle(f'{gp} {year} {ses} - {driver} - Speed', size=24, y=0.97)

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.12)
    ax.axis("off")

    # create background track line
    lap = get_lap(year, gp, ses, driver)
    ax.plot(lap.telemetry['X'], lap.telemetry['Y'],
            color='black', linestyle='-',
            linewidth=16, zorder=0)
    
    # create continuous norm to map from speed data points to colours
    colour = lap.telemetry['Speed']
    segments = get_lap_segments(lap)
    norm = plt.Normalize(colour.min(), colour.max())
    lc = LineCollection(segments, cmap=mpl.cm.plasma, norm=norm,
                        linestyle='-', linewidth=5)
    
    # set values used for colour mapping
    lc.set_array(colour)
    
    # merge all line segments together
    line = ax.add_collection(lc)

    # create colour bar as legend
    cbaxes = fig.add_axes([0.25, 0.05, 0.5, 0.05])
    normlegend = mpl.colors.Normalize(vmin=colour.min(), vmax=colour.max())
    legend = mpl.colorbar.ColorbarBase(cbaxes, norm=normlegend, cmap=mpl.cm.plasma, orientation="horizontal")

    plt.show()

def telemetry_plot(year, gp, ses, driver):
    fig, ax = plt.subplots(figsize=(8,5))
    lap = get_lap(year, gp, ses, driver)
    car_data = lap.get_car_data().add_distance()
    ax.plot(car_data['Distance'], car_data['Speed'], label=driver)    
    ax.set_xlabel("Distance")
    ax.set_ylabel("Speed")
    ax.legend()
    plt.show()

def get_fastest_lap_telemetry(year, gp, ses, driver):
    lap = get_lap(year, gp, ses, driver)
    car_data = lap.get_car_data().add_distance()
    telemetry = lap.telemetry.add_distance()
    telemetry.drop('DriverAhead', axis=1, inplace=True)
    telemetry.drop('DistanceToDriverAhead', axis=1, inplace=True)
    return telemetry

def store_session_stints(year: int, gp: str, driver: str, ses: str):
    """Store session data, stints, and laps directly in database"""
    session = f1.get_session(year, gp, ses)
    session.load()
    weather_data = session.weather_data
    date = session.date.to_pydatetime()
    event_weather = "wet" if weather_data["Rainfall"].any() else "dry"

    # Store session
    session_data: SessionData = {
        "event": gp, 
        "date": date.isoformat(), 
        "session_type": ses, 
        "weather_type": event_weather,
        "year": year
    }
    print(type(gp))
    print(type(date.isoformat()))
    print(type(ses))
    print(type(event_weather))
    session_response = db.store_session(session_data)
    session_id = session_response["data"][0]["id"] if session_response and session_response["data"] else None
    
    if not session_id:
        print("Failed to store session, aborting...")
        return

    laps = session.laps.pick_drivers(driver)
    laps = laps[laps["Deleted"] == False]

    # Store driver if first session
    driver_number = laps.iloc[0]["DriverNumber"]
    team = laps.iloc[0]["Team"]
    driver_data: DriverData = {
            "driver_name": driver, "driver_number": driver_number, "team": team
    }
    if ses == "FP1":
        driver_response = db.store_driver(driver_data)
        driver_id = driver_response["data"][0]["id"] if driver_response and driver_response.get("data") else None
        # Get driver_id for stint/lap relationships
    else:
        driver_id = db.get_driver_id(driver_data)
    
    laps_by_stint = laps.groupby('Stint')
    for stint_number, stint_laps in laps_by_stint:
        print(f"Processing Stint {stint_number}")
        store_stint(stint_laps, session_id, driver_id, session)


def store_stint(laps, session_id, driver_id, session):
    compound = laps.iloc[0]["Compound"]
    init_age = int(laps.iloc[0]["TyreLife"])
    stint_number = int(laps.iloc[0]["Stint"])
    
    stint_data: StintData = {
        "session_id": int(session_id),
        "driver_id": int(driver_id),
        "stint_number": stint_number,
        "tyre_compound": compound,
        "initial_tyre_age": init_age
    }

    print(f"Stint Number: {stint_number}")

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
        
        weather_data_dict: WeatherData = {
            "session_id": int(session_id),
            "time": absolute_time.isoformat(),
            "air_temp": float(weather_row.get("AirTemp")) if pd.notna(weather_row.get("AirTemp")) else None,
            "track_temp": float(weather_row.get("TrackTemp")) if pd.notna(weather_row.get("TrackTemp")) else None,
            "pressure": float(weather_row.get("Pressure")) if pd.notna(weather_row.get("Pressure")) else None,
            "rainfall": "wet" if weather_row.get("Rainfall") else "dry",
            "humidity": float(weather_row.get("Humidity")) if pd.notna(weather_row.get("Humidity")) else None,
            "wind_direction": int(weather_row.get("WindDirection")) if pd.notna(weather_row.get("WindDirection")) else None,
            "wind_speed": float(weather_row.get("WindSpeed")) if pd.notna(weather_row.get("WindSpeed")) else None
        }
        
        weather_response = db.store_weather(weather_data_dict)
        return weather_response["data"][0]["id"] if weather_response and weather_response["data"] else None
    return None

def store_laps(laps, session_id, stint_id, session):
    # Process and store each lap directly
    for _, lap_row in laps.iterrows():
    # Get weather_id for this lap
        weather_id = match_and_store_weather(lap_row["Time"], session_id, session)
        
        lap_time_seconds = lap_row["Time"].total_seconds()
        # Create and store lap data
        lap_data: LapData = {
            "stint_id": int(stint_id),  # You'll need to handle stint storage first
            "weather": int(weather_id) if weather_id is not None else None,
            "lap_number": int(lap_row["LapNumber"]),
            "lap_time": lap_time_seconds,
            "tyre_age": int(lap_row.get("TyreLife", 0)),
            "sector1_time": lap_row.get("Sector1Time").total_seconds() if pd.notna(lap_row.get("Sector1Time")) else None,
            "sector2_time": lap_row.get("Sector2Time").total_seconds() if pd.notna(lap_row.get("Sector2Time")) else None,
            "sector3_time": lap_row.get("Sector3Time").total_seconds() if pd.notna(lap_row.get("Sector3Time")) else None
        }
        
        db.store_lap(lap_data)
    
    print(f"Successfully stored {len(laps)} laps for {driver} in {gp} {year}")


def store_weekend_data(year: int, gp: str, driver: str):
    """Store complete weekend data"""
    store_session_stints(year, gp, driver, "FP1")
    store_session_stints(year, gp, driver, "FP2")
    store_session_stints(year, gp, driver, "FP3")
    print(f"Stored complete weekend data for {driver} at {gp} {year}")

if __name__ == "__main__":
    year = 2022
    gp = "Bahrain"
    driver = "VER"
    
    store_weekend_data(year, gp, driver)
    
