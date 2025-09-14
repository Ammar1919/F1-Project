from supa_db import f1_db, DriverData, SessionData, StintData, LapData, WeatherData

class F1Database:
    @staticmethod
    def store_driver(driver_data: DriverData) -> dict:
        """Store driver data in database"""
        try:
            response = f1_db.table("drivers").insert(driver_data).execute()
            print(f"Successfully added driver: {driver_data['driver_name']}")
            return response
        except Exception as e:
            print(f"Error adding driver {driver_data['driver_name']}: {e}")
            return None
    
    @staticmethod
    def store_session(session_data: SessionData) -> dict:
        """Store session data in database"""
        try:
            response = f1_db.table("sessions").insert(session_data).execute()
            print(f"Successfully added session: {session_data['event']} {session_data['session_type']}")
            return response
        except Exception as e:
            print(f"Error adding session {session_data['event']}: {e}")
            return None
    
    @staticmethod
    def store_stint(stint_data: StintData) -> dict:
        """Store stint data in database"""
        try:
            response = f1_db.table("stints").insert(stint_data).execute()
            print(f"Successfully added stint: {stint_data['stint_number']}")
            return response
        except Exception as e:
            print(f"Error adding stint: {e}")
            return None
    
    @staticmethod
    def store_lap(lap_data: LapData) -> dict:
        """Store lap data in database"""
        try:
            response = f1_db.table("laps").insert(lap_data).execute()
            return response
        except Exception as e:
            print(f"Error storing lap data: {e}")
            return None
    
    @staticmethod
    def store_weather(weather_data: WeatherData) -> dict:
        """Store weather data in database"""
        try:
            response = f1_db.table("weather").insert(weather_data).execute()
            return response
        except Exception as e:
            print(f"Error storing weather data: {e}")
            return None
