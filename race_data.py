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

def get_telemetry(year, gp, ses, driver):
    lap = get_lap(year, gp, ses, driver)
    car_data = lap.get_car_data().add_distance()
    telemetry = lap.telemetry.add_distance()
    telemetry.drop('DriverAhead', axis=1, inplace=True)
    telemetry.drop('DistanceToDriverAhead', axis=1, inplace=True)
    return telemetry

# GPS data is too noisy, cannot reliably calculate acceleration
