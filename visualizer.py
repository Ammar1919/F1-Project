from matplotlib import pyplot as plt
from race_data import get_cleaned_weekend_data
from supa_db import DriverData

"""

Degradation Curve
=================

For each tyre compound in the weekend
Plot stint tyre degradations overlapping each other
If tyres are old, plot from continuance: init_tyre_age of one == init_tyre_age + num_laps of other

"""

def plot_degradation_curve(wknd_data):
    print(wknd_data)

if __name__ == "__main__":

    driver_name = "NOR"
    driver_number = 4
    team = "McLaren"
    event = "Bahrain"
    year = 2023

    driver_data: DriverData = {
        "driver_name": driver_name,
        "driver_number": driver_number,
        "team": team
    }


    wknd_data = get_cleaned_weekend_data(driver_data, event, year)
    plot_degradation_curve(wknd_data)


            

            
