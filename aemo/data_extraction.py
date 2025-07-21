import pandas as pd
import numpy as np
import requests
from retry import retry
from concurrent.futures import ThreadPoolExecutor


# Build demand and supply curves
def build_supply_demand_curves(data):
    supply_curves = []
    demand_curves = []

    for day in np.sort(data["Trading Date"].unique()):

        daily_data = data[data["Trading Date"] == day].copy()

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

            # Discretizacion
            offers = pd.concat(
                [
                    offers.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].min(),
                    offers.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].max(),
                ]
            ).sort_values(["cumulative_quantity", "Price ($/MWh)"])

            bids = pd.concat(
                [
                    bids.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].min(),
                    bids.groupby("Price ($/MWh)", as_index=False)["cumulative_quantity"].max(),
                ]
            ).sort_values(["cumulative_quantity", "Price ($/MWh)"])

            # Get curves values
            raw_supply_curve = np.round(offers[["cumulative_quantity", "Price ($/MWh)"]].values, 4).tolist()
            raw_demand_curve = np.round(bids[["cumulative_quantity", "Price ($/MWh)"]].values, 4).tolist()

            # Compute cross point
            cross_point = find_intersection(raw_supply_curve, raw_demand_curve)

            # Append results
            supply_curves.append(
                {
                    "day": day,
                    "interval": interval,
                    "raw_curve": raw_supply_curve,
                    "cross_point": cross_point,
                }
            )

            demand_curves.append(
                {
                    "day": day,
                    "interval": interval,
                    "raw_curve": raw_demand_curve,
                    "cross_point": cross_point,
                }
            )

    supply_curves = pd.DataFrame(supply_curves)
    demand_curves = pd.DataFrame(demand_curves)

    return supply_curves, demand_curves


# Load AEMO data into a parquet table
def load_data(input_path_format, root_path, years, months):

    # Load each month data
    def load_month_data(date):
        year, month = date
        formatted_data_path = input_path_format.format(year=year, month=month)

        interval_data = pd.read_csv(formatted_data_path, low_memory=False)
        interval_data["year"] = year
        interval_data["month"] = int(month)
        supply_curves, demand_curves = build_supply_demand_curves(interval_data)

        return supply_curves, demand_curves

    # Loop through each year and month
    for year in years:
        with ThreadPoolExecutor() as executor:
            dates = [(year, m) for m in months]
            year_results = list(executor.map(load_month_data, dates))

        supply_curves_union = pd.concat([r[0] for r in year_results])
        demand_curves_union = pd.concat([r[1] for r in year_results])

        supply_output_path = root_path + rf"\aemo\data\processed\supply_curves_{year}.csv"
        demand_output_path = root_path + rf"\aemo\data\processed\demand_curves_{year}.csv"

        supply_curves_union.to_csv(supply_output_path, index=False)
        demand_curves_union.to_csv(demand_output_path, index=False)

        print(f"Data for {year} loaded successfully.")


def find_intersection(curve1, curve2):
    x1, y1 = zip(*curve1)
    x2, y2 = zip(*curve2)

    # Define the search grid with a step of 0.5
    x_min = min(min(x1), min(x2))
    x_max = max(max(x1), max(x2))
    x_grid = np.arange(x_min, x_max, 0.5)

    # Interpolate both curves
    y1_interp = np.interp(x_grid, x1, y1)
    y2_interp = np.interp(x_grid, x2, y2)

    # Calculate distances and find minimum
    distances = np.abs(y1_interp - y2_interp)
    min_idx = np.argmin(distances)

    return round(x_grid[min_idx], 4), round(y1_interp[min_idx], 4)


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
