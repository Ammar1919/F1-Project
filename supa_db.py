import os
import supabase
from supabase import create_client, Client
from datetime import datetime
from typing import TypedDict

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
f1_db: Client = create_client(url, key)

class DriverData(TypedDict):
    driver_name: str
    driver_number: int
    team: str

class SessionData(TypedDict):
    event: str
    date: datetime
    session_type: str
    weather_type: str

class StintData(TypedDict):
    session_id: int
    driver_id: int
    stint_number: int
    tyre_compound: str
    initial_tyre_age: int

class LapData(TypedDict):
    stint_id: int
    weather_id: int
    lap_number: int
    lap_time: datetime
    tyre_age: int
    sector1_time: datetime
    sector2_time: datetime
    sector3_time: datetime

class WeatherData(TypedDict):
    session_id: int
    time: datetime
    air_temp: float
    track_temp: float
    pressure: float
    rainfall: bool
    humidity: float
    wind_direction: int
    wind_speed: float

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
        print(f"Erro adding weather {weather_data['session_id'], weather_data['time']}")
        return None

