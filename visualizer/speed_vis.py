from data_engine.race_data import get_cleaned_weekend_data, get_cleaned_session_data
import fastf1 as f1
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

colourmap = mpl.cm.plasma

def get_fastest_lap(driver, event, session, year):
    session_obj = f1.get_session(year, event, session)
    session_obj.load()
    laps = session_obj.laps.pick_drivers(driver)
    if session == "Qualifying":
        laps = get_q_session(laps)
    return laps.pick_fastest()

def get_q_session(laps):
    q1, q2, q3 = laps.split_qualifying_sessions()
    if not q3.empty:
        return q3
    elif not q2.empty:
        return q2
    return q1

def get_median_lap(driver, event, session, year):
    session_obj = f1.get_session(year, event, session)
    session_obj.load()
    laps = session_obj.laps.pick_drivers(driver).pick_wo_box()
    if session == "Qualifying":
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

def plot_track_map(lap, colour, segments, title, metric):
    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(12, 6.75))
    fig.suptitle(title, size=24, y=0.97)

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.12)
    ax.axis('off')

    # Plot track outline
    ax.plot(lap.telemetry['X'], lap.telemetry['Y'], color='black',
            linestyle='-', linewidth=16, zorder=0)
    
    # Plot coloured segments
    norm = plt.Normalize(colour.min(), colour.max())
    lc = LineCollection(segments, cmap=colourmap, norm=norm, linestyle='-', linewidth=5)
    lc.set_array(colour)
    ax.add_collection(lc)

    # Add colorbar
    cbaxes = fig.add_axes([0.25, 0.05, 0.5, 0.05])
    normlegend = mpl.colors.Normalize(vmin=colour.min(), vmax=colour.max())
    legend = mpl.colorbar.ColorbarBase(cbaxes, norm=normlegend, cmap=colourmap,
                                    orientation='horizontal')
    
    # Set custom ticks based on metric
    if metric == 'Speed':
        ticks = np.arange(0, 401, 50)
        legend.set_ticks(ticks)
        legend.set_ticklabels([f"{tick}" for tick in ticks])
    
    plt.show()

def plot_overlap_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title, circuit_info):
    d1_tel = d1_lap.get_car_data().add_distance()
    d2_tel = d2_lap.get_car_data().add_distance()

    d1_colour = 'red'
    d2_colour = 'blue'

    fig, ax = plt.subplots()
    ax.plot(d1_tel['Distance'], d1_tel['Speed'], color=d1_colour, label=d1_name)
    ax.plot(d2_tel['Distance'], d2_tel['Speed'], color=d2_colour, label=d2_name)

    v_min = d1_tel['Speed'].min()
    v_max = d1_tel['Speed'].max()

    ax.vlines(x=circuit_info.corners['Distance'], ymin=v_min-20, ymax=v_max+20, linestyles='dotted', colors='grey')

    for _, corner in circuit_info.corners.iterrows():
        txt = f"{corner['Number']}{corner['Letter']}"
        ax.text(corner['Distance'], v_min-25, txt, va='center_baseline', ha='center', size='small')

    ax.set_xlabel('Distance in m')
    ax.set_ylabel('Speed in km/h')

    ax.legend()
    plt.suptitle(title)

    plt.show()


def plot_fastest_lap_speed_track_map(driver, event, session, year):
    # Convienience function for plotting fastest lap speed
    lap = get_fastest_lap(driver, event, session, year)
    title = f"{event} {session} {year} - {driver} - Fastest Lap: {lap["LapTime"]}"
    plot_track_lap_metric(lap, "Speed", title)

def plot_median_lap_speed_track_map(driver, event, session, year):
    lap = get_median_lap(driver, event, session, year)
    title = f"{event} {session} {year} - {driver} - Median Lap: {lap["LapTime"]}"
    plot_track_lap_metric(lap, "Speed", title)

def plot_track_lap_metric(lap, metric, title):
    # Generic function for plotting any lap with any metric
    x, y, colour, segments = prepare_track_data(lap, metric)
    plot_track_map(lap, colour, segments, title, metric)

def plot_fastest_overlap_speed_trace(d1_name, d2_name, event, session, year):
    d1_lap = get_fastest_lap(d1_name, event, session, year)
    d2_lap = get_fastest_lap(d2_name, event, session, year)
    title = f"{d1_name}'s and {d2_name}'s Fastest Laps in {session} - {event} - year"
    plot_overlap_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title)

def plot_median_overlap_speed_trace(d1_name, d2_name, event, session, year):
    d1_lap = get_median_lap(d1_name, event, session, year)
    d2_lap = get_median_lap(d2_name, event, session, year)
    title = f"{d1_name}'s and {d2_name}'s Median Laps in {session} - {event} - year"
    plot_overlap_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title)

def plot_overlap_speed_traces(d1_name, d2_name, event, session, year, lap_type):
    func_map = {"Fastest": get_fastest_lap, "Median": get_median_lap}
    d1_lap = func_map[lap_type](d1_name, event, session, year)
    d2_lap = func_map[lap_type](d2_name, event, session, year)
    session_obj = f1.get_session(year, event, session)
    session_obj.load()
    circuit_info = session_obj.get_circuit_info()
    title = f"{d1_name}'s and {d2_name}'s {lap_type} Lap in {session} - {event} - {year}"
    plot_overlap_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title, circuit_info)

if __name__ == "__main__":
    driver = "HAM"
    event = "Bahrain"
    session = "Race"
    year = 2025
    
    plot_overlap_speed_traces("LEC", "HAM", event, session, year, "Median")
    
    # HAM median lap time for BAH 2025 Q = 1:31.219
    # LEC median lap time for BAH 2025 Q = 1:31.056
    # HAM fastest lap time for BAH 2025 Q = 1:30.772
    # LEC fastest lap time for BAH 2025 Q = 1:30.175
 
