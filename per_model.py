from matplotlib import pyplot as plt
from race_data import get_cleaned_weekend_data, get_all_weekend_laps
from supa_db import DriverData
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

"""

Absolute Performance Model
==========================

Create an XGBoost regression model per tyre compound per weekend (for now, adjust later) that predicts absolute performance i.e. laptime for a certain tyre age

"""

def preprocess_data(laps, compound):
    laps = laps.sort_values(by='weather_time') # do time-based sort for a time-based split
    laps = laps[laps["tyre_compound"]==compound]
    laps = laps.drop(['tyre_compound', 'weather_time', 'sector1_time', 'sector2_time', 'sector3_time'], axis=1)
    X = laps.drop(['lap_time'], axis=1)
    y = laps['lap_time']

    if 'session_type' in X.columns:
        X['session_type'] = pd.Categorical(X['session_type']).codes
    if 'rainfall' in X.columns:
        X['rainfall'] = pd.Categorical(X['rainfall']).codes
    
    X = X.fillna(-1)

    print(X)

    return X, y


def abs_performance_model(laps, compound):
    X, y = preprocess_data(laps, compound)
    
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2) 
    # Avoiding random nature of train_test_split in favour of time-based splitting 

    X_train, X_test, y_train, y_test = time_based_split(X, y, test_size=0.2)

    
    model = XGBRegressor(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)

    print(f"MSE: {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")

    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\nFeature Importance:")
    print(feature_importance)

    return model

def time_based_split(X, y, test_size):
    split_idx = int(len(X) * (1-test_size))

    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":

    event = "Miami"
    year = 2023
    all_weekend_laps = get_all_weekend_laps(event, year)
    soft_per_model = abs_performance_model(all_weekend_laps, "SOFT")



            

            
