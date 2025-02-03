import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from retry import retry


# Load AEMO data into a parquet table
def load_data(input_path_format, parquet_output_path, years, months):
    # Loop through each year and month
    for year in years:
        for month in months:
            formatted_data_path = input_path_format.format(year=year, month=month)
            print(f"Processing file: {year}-{month}")

            interval_data = pd.read_csv(formatted_data_path)

            interval_data["year"] = year
            interval_data["month"] = int(month)

            try:
                data = pd.concat([data, interval_data], ignore_index=True)

            except:
                data = interval_data

            print(f"Data for {year}-{month} loaded successfully.")

    data.to_parquet(parquet_output_path, partition_cols=["year", "month"], engine="pyarrow", index=False)
    return data


# Build offer and supply curves
def build_offer_supply_curves(data):
    supply_demand_curves = {}

    for day in np.sort(data["Trading Date"].unique()):

        daily_data = data[data["Trading Date"] == day].copy()
        supply_demand_curves[day] = {}

        for interval in np.sort(data["Interval Number"].unique()):

            # Sort data by Interval and Price
            data_interval = daily_data[daily_data["Interval Number"] == interval].copy()

            # Separate offers and bids
            offers = data_interval[data_interval["Bid or Offer"] == "Offer"].sort_values("Price ($/MWh)").copy()
            bids = (
                data_interval[data_interval["Bid or Offer"] == "Bid"]
                .sort_values("Price ($/MWh)", ascending=False)
                .copy()
            )

            # Calculate cumulative quantity for both offers and bids
            offers["cumulative_quantity"] = offers["Quantity (MWh)"].cumsum()
            bids["cumulative_quantity"] = bids["Quantity (MWh)"].cumsum()

            # Discretización
            offers = pd.concat(
                [
                    offers.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].min(),
                    offers.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].max(),
                ]
            ).sort_values(["Price ($/MWh)", "cumulative_quantity"])

            bids = pd.concat(
                [
                    bids.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].min(),
                    bids.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].max(),
                ]
            ).sort_values(["Price ($/MWh)", "cumulative_quantity"], ascending=False)

            # Get curves values
            supply_curve = offers[["cumulative_quantity", "Price ($/MWh)"]].values
            demand_curve = bids[["cumulative_quantity", "Price ($/MWh)"]].values

            supply_demand_curves[day][interval] = {
                "supply_curve": supply_curve,
                "demand_curve": demand_curve,
            }

    return supply_demand_curves


@retry(tries=3, delay=1)
def fetch_weather_data(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "daylight_duration",
            "precipitation_sum",
            "wind_speed_10m_max",
            "shortwave_radiation_sum",
        ],
        "timezone": "Australia/Sydney",
    }
    response = requests.get(url, params=params)
    return response.json()
