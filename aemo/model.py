import numpy as np
import pandas as pd


def process_embedding_data(embdedding_data, embeddings_columns, latent_dim):
    # Set data type
    embdedding_data[embeddings_columns] = embdedding_data[embeddings_columns].astype("float16")
    embdedding_data["interval"] = embdedding_data["interval"].astype(int)

    # Get date features
    embdedding_data["date"] = pd.to_datetime(embdedding_data["date"])
    embdedding_data["weekday"] = embdedding_data["date"].dt.weekday / 6
    embdedding_data["month"] = embdedding_data["date"].dt.month / 12

    # Set interval as cyclical feature
    interval_min, interval_max = embdedding_data["interval"].min(), embdedding_data["interval"].max()
    embdedding_data["interval_sin"] = np.sin(2 * np.pi * (embdedding_data["interval"] - interval_min) / interval_max)
    embdedding_data["interval_cos"] = np.cos(2 * np.pi * (embdedding_data["interval"] - interval_min) / interval_max)

    # Create shift columns
    shift_columns = [1, 7, 14]
    for shift in shift_columns:
        embdedding_data[[f"X{shift}_{i + 1}" for i in range(latent_dim)]] = embdedding_data[embeddings_columns].shift(shift * 48)

    return embdedding_data


def get_train_test_split(data, test_date, feature_cols, target_cols):

    train_data = data[data["date"] < test_date].copy()
    test_data = data[data["date"] >= test_date].copy()

    X_train = train_data[feature_cols].values
    y_train = train_data[target_cols].values

    X_test = test_data[feature_cols].values
    y_test = test_data[target_cols].values

    return X_train, y_train, X_test, y_test


def compute_baseline_mae(data, shift_days=1):
    shift = shift_days * 48
    predictions = data[:-shift]
    actuals = data[shift:]
    mae = np.mean(np.abs(predictions - actuals))
    return mae
