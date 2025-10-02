import numpy as np

def get_fastest_lap(driver, session_obj):
    laps = session_obj.laps.pick_drivers(driver)
    if session_obj.name == "Qualifying":
        laps = get_q_session(laps)
    return laps.pick_accurate().pick_fastest()

def get_q_session(laps):
    q1, q2, q3 = laps.split_qualifying_sessions()
    if not q3.empty:
        return q3
    elif not q2.empty:
        return q2
    return q1

def get_laps(driver, laps):
    return laps.pick_drivers(driver).pick_wo_box().pick_not_deleted().pick_accurate()

def get_median_lap(driver, session_obj):
    laps = session_obj.laps.pick_drivers(driver).pick_wo_box().pick_accurate()
    if session_obj.name == "Qualifying":
        laps = get_q_session(laps)
    sorted_laps = laps.sort_values(by="LapTime")
    median_idx = (len(sorted_laps)-1)//2
    return sorted_laps.iloc[median_idx]

def prepare_track_data(lap, metric='Speed'):
    telemetry = lap.telemetry
    x, y, colour = telemetry['X'], telemetry['Y'], telemetry[metric]
    
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    return x, y, colour, segments