import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from matplotlib import colormaps
from matplotlib import colors 

import fastf1 as f1

heat_map = mpl.cm.plasma

def plot_track_map_base(lap, colour, segments, title, metric):
    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(12, 6.75))
    fig.suptitle(title, size=24, y=0.97)

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.12)
    ax.axis('off')

    # Plot track outline
    ax.plot(lap.telemetry['X'], lap.telemetry['Y'], color='black',
            linestyle='-', linewidth=16, zorder=0)
    
    # Plot coloured segments
    if metric == 'nGear':
        cmap = colormaps['tab10']
        norm = mpl.colors.BoundaryNorm(boundaries=np.arange(0.5, 9.5, 1), ncolors=cmap.N)
    else:
        cmap = heat_map  # Use the continuous colormap for other metrics
        norm = plt.Normalize(colour.min(), colour.max())
    
    lc = LineCollection(segments, cmap=cmap, norm=norm, linestyle='-', linewidth=5)
    lc.set_array(colour)
    ax.add_collection(lc)

    cbaxes = fig.add_axes([0.25, 0.05, 0.5, 0.05])
    
    # Use the same norm and cmap for the colorbar as for the plot
    legend = mpl.colorbar.ColorbarBase(cbaxes, norm=norm, cmap=cmap,
                                    orientation='horizontal')
    
    # Set custom ticks based on metric
    if metric == 'Speed':
        ticks = np.arange(0, 401, 50)
        legend.set_ticks(ticks)
        legend.set_ticklabels([f"{tick}" for tick in ticks])
    elif metric == 'nGear':
        gear_range = np.arange(int(colour.min()), int(colour.max())+1)
        legend.set_ticks(gear_range)
        legend.set_ticklabels([f"Gear {int(gear)}" for gear in gear_range])
    
    plt.show()

def plot_overlay_speed_trace_base(d1_name, d2_name, d1_lap, d2_lap, title, circuit_info):
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

def plot_single_trace_base(driver, lap, title, metric, circuit_info):
    tel = lap.get_car_data().add_distance()
    colour = 'red'

    fig, ax = plt.subplots()
    ax.plot(tel['Distance'], tel[metric], color=colour, label=driver)

    distance_ticks = np.arange(0, tel['Distance'].max(), 100)
    ax.set_xticks(distance_ticks)
    
    v_min = tel['Speed'].min()
    v_max = tel['Speed'].max()

    ax.vlines(x=circuit_info.corners['Distance'], ymin=v_min-20, ymax=v_max+20, linestyles='dotted', colors='grey')

    for _, corner in circuit_info.corners.iterrows():
        txt = f"{corner['Number']}{corner['Letter']}"
        ax.text(corner['Distance'], v_min-25, txt, va='center_baseline', ha='center', size='small')

    ax.set_xlabel('Distance in m')
    ax.set_ylabel(metric)
    ax.set_ylim(top=100)

    ax.legend()
    plt.suptitle(title)

    plt.show()


def plot_scatter_chart_base(driver, laps, title):
    x = np.array(laps["LapNumber"])
    y = np.array(laps["LapTime"].dt.total_seconds())
    tyre_dict = {"SOFT": "red", "MEDIUM": "yellow", "HARD": "white", "INTERS": "green", "WETS": "blue"}
    tyre_compounds = np.array(laps["Compound"])

    colours = [tyre_dict.get(compound, "black") for compound in tyre_compounds]

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('darkgrey')
    ax.set_facecolor(colors.CSS4_COLORS['indigo'])
    plt.title(title, color='white')
    plt.xlabel("Lap Number", color='white')
    plt.ylabel("Lap Time (s)", color='white')
    ax.tick_params(colors='white')

    for spine in ax.spines.values():
        spine.set_edgecolor('white')

    plt.scatter(x, y, c=colours)
    plt.show()

def plot_tyre_strategies_base(d1_name, d2_name, stints, title, session):
    fig, ax = plt.subplots()

    for driver_stints in stints:
        previous_stint_end = 0
        for idx, row in driver_stints.iterrows():
            compound_colour = f1.plotting.get_compound_color(row["Compound"], session=session)

            plt.barh(
                y=row["Driver"],
                width=row["StintLength"],
                left=previous_stint_end,
                color=compound_colour,
                edgecolor="black",
                fill=True
            )

            previous_stint_end += row["StintLength"]
    
    plt.title(title)
    plt.xlabel("Lap Number")
    plt.grid(False)

    ax.invert_yaxis()

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.tight_layout()
    plt.show()

