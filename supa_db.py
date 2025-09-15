import os
import supabase
from supabase import create_client, Client
from datetime import datetime
from typing import TypedDict
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
f1_db: Client = create_client(url, key)

class DriverData(TypedDict):
    driver_name: str
    driver_number: int
    team: str

class SessionData(TypedDict):
    event: str
    date: str
    session_type: str
    weather_type: str
    year: int

class StintData(TypedDict):
    session_id: int
    driver_id: int
    stint_number: int
    tyre_compound: str
    initial_tyre_age: int
    num_laps: int

class LapData(TypedDict):
    stint_id: int
    weather_id: int
    lap_number: int
    lap_time: float
    tyre_age: int
    sector1_time: float
    sector2_time: float
    sector3_time: float

class WeatherData(TypedDict):
    session_id: int
    time: str
    air_temp: float
    track_temp: float
    pressure: float
    rainfall: str
    humidity: float
    wind_direction: int
    wind_speed: float

def create_session_data(gp, date, ses, event_weather, year):
    session_data: SessionData = {
        "event": gp, 
        "date": date.isoformat(), 
        "session_type": ses, 
        "weather_type": event_weather,
        "year": year
    }
    return session_data

def create_stint_data(session_id, driver_id, first_lap, num_laps):
    compound = first_lap["Compound"]
    init_age = int(first_lap["TyreLife"])
    stint_number = int(first_lap["Stint"])
    stint_data: StintData = {
        "session_id": int(session_id),
        "driver_id": int(driver_id),
        "stint_number": stint_number,
        "tyre_compound": compound,
        "initial_tyre_age": init_age,
        "num_laps": num_laps
    }
    return stint_data

def create_lap_data(stint_id, weather_id, lap):
    lap_time_seconds = lap["LapTime"].total_seconds()
    lap_data: LapData = {
            "stint_id": int(stint_id),  # You'll need to handle stint storage first
            "weather": int(weather_id) if weather_id is not None else None,
            "lap_number": int(lap["LapNumber"]),
            "lap_time": lap_time_seconds,
            "tyre_age": int(lap.get("TyreLife", 0)),
            "sector1_time": lap.get("Sector1Time").total_seconds() if pd.notna(lap.get("Sector1Time")) else None,
            "sector2_time": lap.get("Sector2Time").total_seconds() if pd.notna(lap.get("Sector2Time")) else None,
            "sector3_time": lap.get("Sector3Time").total_seconds() if pd.notna(lap.get("Sector3Time")) else None
        }
    return lap_data

def create_weather_data(session_id, weather, absolute_time):
    weather_data_dict: WeatherData = {
            "session_id": int(session_id),
            "time": absolute_time.isoformat(),
            "air_temp": float(weather.get("AirTemp")) if pd.notna(weather.get("AirTemp")) else None,
            "track_temp": float(weather.get("TrackTemp")) if pd.notna(weather.get("TrackTemp")) else None,
            "pressure": float(weather.get("Pressure")) if pd.notna(weather.get("Pressure")) else None,
            "rainfall": "wet" if weather.get("Rainfall") else "dry",
            "humidity": float(weather.get("Humidity")) if pd.notna(weather.get("Humidity")) else None,
            "wind_direction": int(weather.get("WindDirection")) if pd.notna(weather.get("WindDirection")) else None,
            "wind_speed": float(weather.get("WindSpeed")) if pd.notna(weather.get("WindSpeed")) else None
        }
    return weather_data_dict

def add_driver(driver_data: DriverData):
    try:
        response = (
            f1_db.table("drivers")
            .insert(driver_data)
            .execute()
        )
        return response
    except Exception as e:
        print(f"Error adding driver {driver_data['driver_name']}: {e}")
        return None

def add_session(session_data: SessionData):
    try:
        response = (
            f1_db.table("sessions")
            .insert(session_data)
            .execute()
        )
        return response
    except Exception as e:
        print(f"Error adding session {session_data['event']}: {e}")
        return None

def add_stint(stint_data: StintData):
    try:
        response = (
            f1_db.table("sessions")
            .insert(stint_data)
            .execute()
        )
        return response
    except Exception as e:
        print(f"Error adding session {stint_data['session_id'], stint_data['driver_id'], stint_data['stint_num']}: {e}")
        return None

def add_lap(lap_data: LapData):
    try:
        response = (
            f1_db.table("lap")
            .insert(lap_data)
            .execute()
        )
        return response
    except Exception as e:
        print(f"Error adding lap {lap_data['stint_id'], lap_data['lap_number']}: {e}")
        return None

def add_weather(weather_data: WeatherData):
    try:
        response = (
            f1_db.table("weather_table")
            .insert(weather_data)
            .execute()
        )
        return response
    except Exception as e:
        print(f"Error adding weather {weather_data['session_id'], weather_data['time']}")
        return None

