import matplotlib.pyplot as plt
import random
import numpy as np
from scipy.stats import wasserstein_distance as wasserstein_distance_scipy


def subsample_list(data, probability, seed=123):
    if seed is not None:
        random.seed(seed)

    subsampled = np.array([item for item in data if random.random() < probability])
    return subsampled


def plot_offer_supply_curves(supply_curve, demand_curve):

    # Separate quantity and price for offers
    supply_quantities, supply_prices = zip(*supply_curve)
    # Separate quantity and price for bids
    demand_quantities, demand_prices = zip(*demand_curve)

    # Plot the curves
    plt.figure(figsize=(10, 6))
    plt.plot(supply_quantities, supply_prices, label="Supply Curve", color="blue")
    plt.plot(demand_quantities, demand_prices, label="Demand Curve", color="red")

    # Adding labels and title
    plt.xlabel("Quantity")
    plt.ylabel("Price")
    plt.title(f"Supply and Demand Curves")
    plt.legend()
    plt.grid(True)
    plt.show()


def wasserstein_distance(curve1, curve2, plot=False):
    x1, y1 = curve1[:, 0], curve1[:, 1]
    x2, y2 = curve2[:, 0], curve2[:, 1]

    if plot:
        # Plot the curves
        plt.figure(figsize=(10, 6))
        plt.plot(x1, y1, label="Curve 1", color="blue")
        plt.plot(x2, y2, label="Curve 2", color="red")

    min_y_value = min([y1.min(), y2.min()])

    if min_y_value < 0:
        y1 = y1 + abs(min_y_value)
        y2 = y2 + abs(min_y_value)

    distance = wasserstein_distance_scipy(x1, x2, y1, y2)

    if plot:
        # Adding labels and title
        plt.xlabel("Quantity")
        plt.ylabel("Price")
        plt.title(f"Distance: {distance}")
        plt.legend()
        plt.grid(True)
        plt.show()

    return distance
