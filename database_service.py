from supa_db import f1_db, DriverData, SessionData, StintData, LapData, WeatherData

class F1Database:
    @staticmethod
    def driver_exists(driver_data: DriverData) -> dict:
        """Check if driver exists in database, return with consistent format"""
        try:
            response = ( 
                f1_db.table("drivers").select("id, driver_name, driver_number, team")
                .eq("driver_name", driver_data['driver_name'])
                .eq("driver_number", driver_data['driver_number'])
                .eq("team", driver_data['team'])
                .execute()
            )
            if len(response.data) > 0:
                return {"exists": True, "data": response.data}
            else:
                return {"exists": False, "data": None}
        except Exception as e:
            print(f"Error checking if driver {driver_data['driver_name']} exists : {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def session_exists(session_data: SessionData) -> dict:
        """Check if session exists, return with consistent format"""
        try:
            response = (
                f1_db.table("sessions")
                .select("id, event, session_type")
                .eq("event", session_data["event"])
                .eq("session_type", session_data["session_type"])
                .execute()
            )
            if len(response.data) > 0:
                return {"exists": True, "data": response.data}
            else:
                return {"exists": False, "data": None}
        except Exception as e:
            print(f"Error checking if session exists: {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def weather_exists(weather_data: WeatherData) -> dict:
        """Check if weather snippet exists, return ID if found"""
        try:
            response = (
                f1_db.table("weather_table").select("id, time")
                .eq("time", weather_data['time'])
                .execute()
            )
            if len(response.data) > 0:
                return {"exists": True, "data": response.data}
            else:
                return {"exists": False, "data": None}
        except Exception as e:
            print(f"Error checking if weather at {weather_data['time']} exists: {e}")
            return {"exists": False, "data": None}

    @staticmethod
    def store_driver(driver_data: DriverData) -> dict:
        """Store driver data in database or return existing ID"""
        existing_driver = F1Database.driver_exists(driver_data)
        
        if existing_driver["exists"]:
            print(f"Driver {driver_data['driver_name']} already exists, returning existing ID")
            return existing_driver  # Returns {"exists": True, "data": [...]}
        
        try:
            response = f1_db.table("drivers").insert(driver_data).execute()
            print(f"Successfully added driver: {driver_data['driver_name']}")
            return {"exists": False, "data": response.data}
        except Exception as e:
            print(f"Error adding driver {driver_data['driver_name']}: {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def store_session(session_data: SessionData) -> dict:
        """Store session data in database"""
        # Convert string weather_type to boolean for database
        processed_data = session_data.copy()
        if isinstance(processed_data["weather_type"], str):
            processed_data["weather_type"] = processed_data["weather_type"].lower() == "wet"
        
        existing_session = F1Database.session_exists(processed_data)
        
        if existing_session["exists"]:
            print(f"Session {session_data['event']} {session_data['session_type']} already exists")
            return existing_session  # Returns {"exists": True, "data": [...]}
        
        try:
            response = f1_db.table("sessions").insert(processed_data).execute()
            print(f"Successfully added session: {session_data['event']} {session_data['session_type']}")
            return {"exists": False, "data": response.data}
        except Exception as e:
            print(f"Error adding session {session_data['event']}: {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def store_stint(stint_data: StintData) -> dict:
        """Store stint data in database"""
        try:
            response = f1_db.table("stints").insert(stint_data).execute()
            print(f"Successfully added stint: {stint_data['stint_number']}")
            return {"exists": False, "data": response.data}
        except Exception as e:
            print(f"Error adding stint: {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def store_lap(lap_data: LapData) -> dict:
        """Store lap data in database"""
        try:
            response = f1_db.table("lap").insert(lap_data).execute()
            return {"exists": False, "data": response.data}
        except Exception as e:
            print(f"Error storing lap data: {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def store_weather(weather_data: WeatherData) -> dict:
        """Store weather data in database or return existing ID"""
        existing_weather = F1Database.weather_exists(weather_data)
        
        if existing_weather["exists"]:
            print(f"Weather data at {weather_data['time']} already exists, returning existing ID")
            return existing_weather  # Returns {"exists": True, "data": [...]}
        
        try:
            response = f1_db.table("weather_table").insert(weather_data).execute()
            print(f"Successfully added weather data at {weather_data['time']}")
            return {"exists": False, "data": response.data}  # Consistent format
        except Exception as e:
            print(f"Error storing weather data: {e}")
            return {"exists": False, "data": None}
    
    @staticmethod
    def get_driver_id(driver_data: DriverData) -> int:
        """Get driver ID from database, return None if not found"""
        try:
            response = (
                f1_db.table("drivers").select("id")
                .eq("driver_name", driver_data['driver_name'])
                .eq("driver_number", driver_data['driver_number'])
                .eq("team", driver_data['team'])
                .execute()
            )
            if len(response.data) > 0:
                return response.data[0]["id"]
            else:
                print(f"Driver {driver_data['driver_name']} not found")
                return None
        except Exception as e:
            print(f"Error getting driver ID for {driver_data['driver_name']}: {e}")
            return None

