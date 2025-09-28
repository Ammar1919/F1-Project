from data_engine.race_data import get_cleaned_weekend_data, get_cleaned_session_data
import fastf1 as f1
import numpy as np
from visualizer.base_plots import plot_track_map_base, plot_overlay_speed_trace_base, plot_scatter_chart_base

def get_fastest_lap(driver, session_obj):
    laps = laps.pick_drivers(driver)
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
    laps = laps.pick_drivers(driver).pick_wo_box().pick_accurate()
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

def plot_track_map(driver, event, session, year, metric, lap_type):
    lap_func_map = {"Fastest": get_fastest_lap, "Median": get_median_lap}

    session_obj = f1.get_session(year, event, session)
    session_obj.load()

    lap = lap_func_map[lap_type](driver, session_obj)
    title = f"{event} {session} {year} - {driver} - {lap_type} Lap {metric}: {lap["LapTime"]}"

    plot_track_lap_metric(lap, metric, title)

def plot_track_lap_metric(lap, metric, title):
    x, y, colour, segments = prepare_track_data(lap, metric)
    plot_track_map_base(lap, colour, segments, title, metric)

def plot_overlap_speed_traces(d1_name, d2_name, event, session, year, lap_type):
    func_map = {"Fastest": get_fastest_lap, "Median": get_median_lap}

    session_obj = f1.get_session(year, event, session)
    session_obj.load()

    d1_lap = func_map[lap_type](d1_name, session_obj)
    d2_lap = func_map[lap_type](d2_name, session_obj)

    circuit_info = session_obj.get_circuit_info()
    title = f"{d1_name}'s and {d2_name}'s {lap_type} Lap in {session} - {event} - {year}"

    plot_overlay_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title, circuit_info)

def plot_scatter_chart(driver, event, session, year):
    session_obj = f1.get_session(year, event, session)
    session_obj.load()
    laps = get_laps(driver, session_obj.laps)
    plot_scatter_chart_base(driver, laps, "")

if __name__ == "__main__":
    driver = "HAM"
    event = "Bahrain"
    session = "Race"
    year = 2025
    

    plot_scatter_chart(driver, event, session, year)

    
