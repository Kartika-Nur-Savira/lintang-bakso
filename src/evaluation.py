"""
Module: Evaluation
Fungsi-fungsi evaluasi peramalan deret waktu berbasis validasi urutan waktu
(Rolling-Origin Time Series Cross-Validation), perhitungan metrik performa
(MAE, RMSE, WAPE, Bias), dan pembandingan multi-model komprehensif:
- Statistical Baseline: Seasonal Naive
- Classical Statistical: Holt-Winters ETS, SARIMA, SARIMAX
- Machine Learning: LightGBM, Random Forest, Gradient Boosting
- Deep Learning / Neural Network: LSTM (PyTorch), MLP Regressor
- Intermittent / Sparse Demand: Croston's Method (SBA)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
import lightgbm as lgb
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """
    Menghitung metrik performa forecasting:
    - MAE: Mean Absolute Error (rata-rata selisih absolut porsi)
    - RMSE: Root Mean Squared Error (penalti lebih berat untuk kesalahan besar)
    - WAPE: Weighted Absolute Percentage Error = (sum |actual - pred| / sum actual) * 100
            Sangat cocok untuk data F&B ritel karena kebal dari pembagian nol (zero-demand issue).
    - Bias: Mean Forecast Error = mean(predicted - actual)
            Positif = Over-forecasting (risiko makanan sisa/basi),
            Negatif = Under-forecasting (risiko kehabisan stok).
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    
    # Floor prediksi di 0 (permintaan riil tidak bisa negatif)
    predicted = np.clip(predicted, a_min=0.0, a_max=None)
    
    errors = predicted - actual
    abs_errors = np.abs(errors)
    
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    
    total_actual = float(np.sum(actual))
    if total_actual > 0:
        wape = float((np.sum(abs_errors) / total_actual) * 100.0)
    else:
        wape = 0.0 if np.sum(abs_errors) == 0 else 100.0
        
    bias = float(np.mean(errors))
    
    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "WAPE": round(wape, 2),
        "Bias": round(bias, 4)
    }


def seasonal_naive_forecast(train_series: pd.Series, horizon: int = 7, s: int = 7) -> np.ndarray:
    """
    Model Baseline Benchmark: Seasonal Naive.
    Memproyeksikan nilai pada hari yang sama dari minggu sebelumnya: y_{t+h} = y_{t+h-s}.
    """
    last_season = train_series.iloc[-s:].values
    forecast = np.tile(last_season, int(np.ceil(horizon / s)))[:horizon]
    return forecast


def croston_sba_forecast(series: pd.Series, horizon: int = 7, alpha: float = 0.1) -> np.ndarray:
    """
    Metode Khusus Intermittent/Sparse Demand: Syntetos-Boylan Approximation (SBA / Croston).
    Memisahkan estimasi interval antar-pesanan dan besaran pesanan untuk mengoreksi bias positif.
    """
    vals = series.values
    nz = np.where(vals > 0)[0]
    if len(nz) == 0:
        return np.zeros(horizon)
        
    intervals = np.diff(np.concatenate(([0], nz)))
    sizes = vals[nz]
    
    z = sizes[0]
    p = intervals[0] if len(intervals) > 0 and intervals[0] > 0 else 1.0
    
    for i in range(1, len(sizes)):
        z = alpha * sizes[i] + (1 - alpha) * z
        p = alpha * intervals[i] + (1 - alpha) * p
        
    # SBA correction factor (1 - alpha / 2)
    demand_rate = (1.0 - alpha / 2.0) * (z / p if p > 0 else 0.0)
    return np.full(horizon, max(0.0, float(demand_rate)))


def make_lag_features(series: pd.Series, exog: pd.DataFrame) -> pd.DataFrame:
    """
    Mengekstrak fitur lag, statistik bergulir, dan kalender untuk algoritma Machine Learning.
    """
    df_f = pd.DataFrame(index=series.index)
    df_f['y'] = series.values
    for lag in [1, 2, 7, 14]:
        df_f[f'lag_{lag}'] = series.shift(lag)
    df_f['roll_mean_7'] = series.shift(1).rolling(7).mean()
    df_f['roll_std_7'] = series.shift(1).rolling(7).std()
    df_f = pd.concat([df_f, exog], axis=1).dropna()
    return df_f


class FastLSTM(nn.Module):
    """Arsitektur PyTorch LSTM untuk peramalan deret waktu permintaan harian."""
    def __init__(self, hidden_size: int = 16):
        super().__init__()
        self.lstm = nn.LSTM(1, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def lstm_forecast(train_series: pd.Series, horizon: int = 7, window_size: int = 14, epochs: int = 30) -> np.ndarray:
    """
    Melatih model LSTM pada sliding window deret historis dan memproyeksikan horizon secara autoregresif.
    """
    vals = train_series.values.astype(float)
    max_val = float(np.max(vals))
    if max_val == 0.0:
        return np.zeros(horizon)
        
    scaled_vals = vals / max_val
    X, y = [], []
    for i in range(len(scaled_vals) - window_size):
        X.append(scaled_vals[i : i + window_size])
        y.append(scaled_vals[i + window_size])
        
    if len(X) < 10:
        return np.full(horizon, float(np.mean(vals)))
        
    X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)
    y_t = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1)
    
    loader = DataLoader(TensorDataset(X_t, y_t), batch_size=32, shuffle=True)
    
    torch.manual_seed(42)
    model = FastLSTM(hidden_size=16)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.02)
    criterion = nn.MSELoss()
    
    model.train()
    for _ in range(epochs):
        for bx, by in loader:
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            
    # Proyeksi autoregresif rekursif multi-langkah
    model.eval()
    curr_window = list(scaled_vals[-window_size:])
    preds = []
    with torch.no_grad():
        for _ in range(horizon):
            inp = torch.tensor(np.array(curr_window[-window_size:]), dtype=torch.float32).view(1, window_size, 1)
            pred_step = float(model(inp).item())
            preds.append(pred_step)
            curr_window.append(pred_step)
            
    preds = np.array(preds) * max_val
    return np.clip(preds, 0.0, None)


def rolling_origin_benchmark_all_models(
    series: pd.Series,
    exog: Optional[pd.DataFrame] = None,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 7),
    horizon: int = 7,
    n_splits: int = 4
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Melakukan benchmark perbandingan multi-model secara komprehensif menggunakan Rolling-Origin CV:
    1. Seasonal Naive (Heuristic Baseline)
    2. Holt-Winters ETS (Classical Smoothing)
    3. SARIMA (Autoregressive Baseline)
    4. SARIMAX (Autoregressive dengan Variabel Eksogen)
    5. LightGBM (Gradient Boosting Trees)
    6. Random Forest (Ensemble Bagging Trees)
    7. LSTM (Deep Learning Recurrent Neural Network)
    8. MLP Regressor (Feedforward Deep Neural Network)
    9. Croston SBA (Intermittent / Sparse Demand)
    """
    total_len = len(series)
    test_len = horizon * n_splits
    start_train_len = total_len - test_len
    
    fold_details = []
    
    for fold in range(n_splits):
        train_end_idx = start_train_len + (fold * horizon)
        val_end_idx = train_end_idx + horizon
        
        train_s = series.iloc[:train_end_idx]
        val_s = series.iloc[train_end_idx:val_end_idx]
        val_dates = series.index[train_end_idx:val_end_idx]
        actuals = val_s.values
        
        # 1. Seasonal Naive
        sn_pred = seasonal_naive_forecast(train_s, horizon=horizon, s=7)
        
        # 2. Holt-Winters ETS
        try:
            hw = ExponentialSmoothing(train_s, seasonal_periods=7, trend='add', seasonal='add', initialization_method='estimated')
            hw_fit = hw.fit()
            hw_pred = hw_fit.forecast(horizon).clip(lower=0.0).values
        except Exception:
            hw_pred = np.full(horizon, train_s.mean())
            
        # 3. SARIMA
        try:
            sarima = SARIMAX(train_s, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
            sarima_fit = sarima.fit(disp=False, maxiter=50)
            sarima_pred = sarima_fit.get_forecast(steps=horizon).predicted_mean.clip(lower=0.0).values
        except Exception:
            sarima_pred = np.full(horizon, train_s.mean())
            
        # 4. SARIMAX
        if exog is not None:
            train_exog = exog.iloc[:train_end_idx]
            val_exog = exog.iloc[train_end_idx:val_end_idx]
            try:
                sarimax = SARIMAX(train_s, exog=train_exog, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
                sarimax_fit = sarimax.fit(disp=False, maxiter=50)
                sarimax_pred = sarimax_fit.get_forecast(steps=horizon, exog=val_exog).predicted_mean.clip(lower=0.0).values
            except Exception:
                sarimax_pred = sarima_pred
        else:
            sarimax_pred = sarima_pred
            
        # Feature matrix untuk Machine Learning
        if exog is not None:
            df_feats = make_lag_features(series.iloc[:val_end_idx], exog.iloc[:val_end_idx])
            X_tr = df_feats.loc[df_feats.index < val_dates[0]].drop(columns=['y'])
            y_tr = df_feats.loc[df_feats.index < val_dates[0], 'y']
            X_va = df_feats.loc[val_dates].drop(columns=['y'])
            
            # 5. LightGBM
            try:
                lgb_model = lgb.LGBMRegressor(
                    n_estimators=50, max_depth=4, learning_rate=0.05,
                    num_leaves=15, min_child_samples=5, random_state=42, verbose=-1
                )
                lgb_model.fit(X_tr, y_tr)
                lgb_pred = np.clip(lgb_model.predict(X_va), 0.0, None)
            except Exception:
                lgb_pred = np.full(horizon, train_s.mean())
                
            # 6. Random Forest
            try:
                rf = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
                rf.fit(X_tr, y_tr)
                rf_pred = np.clip(rf.predict(X_va), 0.0, None)
            except Exception:
                rf_pred = np.full(horizon, train_s.mean())
                
            # 7. MLP Regressor (Neural Network)
            try:
                mlp = MLPRegressor(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42)
                mlp.fit(X_tr, y_tr)
                mlp_pred = np.clip(mlp.predict(X_va), 0.0, None)
            except Exception:
                mlp_pred = np.full(horizon, train_s.mean())
        else:
            lgb_pred = sn_pred
            rf_pred = sn_pred
            mlp_pred = sn_pred
            
        # 8. LSTM (Deep Learning)
        try:
            lstm_pred = lstm_forecast(train_s, horizon=horizon, window_size=14, epochs=30)
        except Exception:
            lstm_pred = sn_pred
            
        # 9. Croston SBA
        croston_pred = croston_sba_forecast(train_s, horizon=horizon)
        
        preds_dict = {
            'Seasonal Naive': sn_pred,
            'Holt-Winters ETS': hw_pred,
            'SARIMA': sarima_pred,
            'SARIMAX': sarimax_pred,
            'LightGBM': lgb_pred,
            'Random Forest': rf_pred,
            'LSTM (Deep Learning)': lstm_pred,
            'MLP (Neural Net)': mlp_pred,
            'Croston (SBA)': croston_pred
        }
        
        for m_name, p_arr in preds_dict.items():
            m_metrics = calculate_metrics(actuals, p_arr)
            fold_details.append({
                'fold': fold + 1,
                'model': m_name,
                'val_start': val_dates[0].strftime('%Y-%m-%d'),
                'val_end': val_dates[-1].strftime('%Y-%m-%d'),
                'MAE': m_metrics['MAE'],
                'RMSE': m_metrics['RMSE'],
                'WAPE': m_metrics['WAPE'],
                'Bias': m_metrics['Bias']
            })
            
    df_folds = pd.DataFrame(fold_details)
    df_summary = df_folds.groupby('model').agg({
        'MAE': 'mean',
        'RMSE': 'mean',
        'WAPE': 'mean',
        'Bias': 'mean'
    }).reset_index().round(4)
    
    return df_folds, df_summary


# Backward compatibility
rolling_origin_evaluation = rolling_origin_benchmark_all_models
