from data_engine.race_data import get_cleaned_weekend_data, get_cleaned_session_data
import fastf1 as f1
import numpy as np
from visualizer.base_plots import plot_track_map_base, plot_overlay_speed_trace_base, plot_scatter_chart_base, plot_single_trace_base, plot_tyre_strategies_base
from data_engine.vis_data import get_fastest_lap, get_median_lap, get_laps, prepare_track_data
import fastf1.plotting

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

def plot_overlay_speed_traces(d1_name, d2_name, event, session, year, lap_type):
    func_map = {"Fastest": get_fastest_lap, "Median": get_median_lap}

    session_obj = f1.get_session(year, event, session)
    session_obj.load()

    d1_lap = func_map[lap_type](d1_name, session_obj)
    d2_lap = func_map[lap_type](d2_name, session_obj)

    circuit_info = session_obj.get_circuit_info()
    title = f"{d1_name}'s and {d2_name}'s {lap_type} Lap in {session} - {event} - {year}"

    plot_overlay_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title, circuit_info)

def plot_throttle_input_track_map(driver, event, session, year, lap_type):
    func_map = {"Fastest": get_fastest_lap, "Median": get_median_lap}

    session_obj = f1.get_session(year, event, session)
    session_obj.load()

    lap = func_map[lap_type](driver, session_obj)

    title = f"{driver}'s throttle input for {lap_type} Lap in {session} - {event} - {year}"
    plot_track_lap_metric(lap, "Throttle", title)

def plot_throttle_input_trace(driver, event, session, year, lap_type):
    func_map = {"Fastest": get_fastest_lap, "Median": get_median_lap}

    session_obj = f1.get_session(year, event, session)
    session_obj.load()

    lap = func_map[lap_type](driver, session_obj)

    circuit_info = session_obj.get_circuit_info()
    title = f"{driver}'s throttle input for {lap_type} Lap in {session} - {event} - {year}"

    plot_single_trace_base(driver, lap, title, "Throttle", circuit_info)
  
def plot_laps_scatter_chart(driver, event, session, year):
    session_obj = f1.get_session(year, event, session)
    session_obj.load()
    laps = get_laps(driver, session_obj.laps)

    plot_scatter_chart_base(driver, laps, "")

def get_driver_stints(driver, laps):
    stints = laps[laps["Driver"] == driver][["Driver", "Stint", "Compound", "LapNumber"]]

    stints = stints.groupby(['Stint', 'Compound']).agg({'LapNumber': 'count', 'Driver': 'first'}).reset_index()

    stints = stints.rename(columns={"LapNumber": "StintLength"})
    return stints

def plot_tyre_strategies(d1_name, d2_name, event, session, year):
    session_obj = f1.get_session(year, event, session)
    session_obj.load()

    d1_laps = get_laps(d1_name, session_obj.laps)
    d2_laps = get_laps(d2_name, session_obj.laps)

    d1_stints = get_driver_stints(d1_name, d1_laps)
    d2_stints = get_driver_stints(d2_name, d2_laps)

    title = f"{d1_name} and {d2_name} Tyre Strategies during {session} - {event} - {year}"

    plot_tyre_strategies_base(d1_name, d2_name, [d1_stints, d2_stints], title, session_obj)


if __name__ == "__main__":
    driver = "HAM"
    event = "Australia"
    session = "Race"
    year = 2025
    

    plot_tyre_strategies("HAM", "LEC", event, session, year)
    
