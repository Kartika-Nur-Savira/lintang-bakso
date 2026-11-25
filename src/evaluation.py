"""
Module: Evaluation (LSTM vs SARIMAX)
Fungsi-fungsi evaluasi peramalan deret waktu berbasis validasi urutan waktu
(Rolling-Origin Time Series Cross-Validation) khusus untuk perbandingan:
1. Seasonal Naive (Heuristic Baseline / Kontrol Acuan)
2. SARIMA (Statistical Univariate Time Series)
3. SARIMAX (Statistical Time Series dengan Variabel Eksogen)
4. LSTM (Long Short-Term Memory - Deep Learning Recurrent Neural Network)

Serta pembentukan dataset siap pakai untuk integrasi Business Intelligence (BI) Dashboard.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """
    Menghitung metrik performa forecasting:
    - MAE: Mean Absolute Error (rata-rata selisih absolut porsi).
    - RMSE: Root Mean Squared Error (penalti lebih berat untuk kesalahan besar).
    - WAPE: Weighted Absolute Percentage Error = (sum |actual - pred| / sum actual) * 100.
            Sangat cocok untuk data F&B ritel karena kebal dari pembagian nol (zero-demand issue).
    - Bias: Mean Forecast Error = mean(predicted - actual).
            Positif = Over-forecasting (risiko makanan sisa/basi),
            Negatif = Under-forecasting (risiko kehabisan stok).
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    
    # Floor prediksi di 0 (permintaan fisik tidak bisa bernilai negatif)
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
    Model Baseline Heuristik: Seasonal Naive.
    Memproyeksikan nilai pada hari yang sama dari siklus mingguan sebelumnya: y_{t+h} = y_{t+h-s}.
    """
    last_season = train_series.iloc[-s:].values
    forecast = np.tile(last_season, int(np.ceil(horizon / s)))[:horizon]
    return forecast


class PyTorchLSTM(nn.Module):
    """
    Arsitektur Deep Learning LSTM untuk deret waktu sekuensial harian.
    Menggunakan input gate, forget gate, cell gate, dan output gate.
    """
    def __init__(self, input_dim: int = 1, hidden_dim: int = 16, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def lstm_forecast(
    train_series: pd.Series,
    horizon: int = 7,
    window_size: int = 14,
    hidden_dim: int = 16,
    epochs: int = 30,
    lr: float = 0.02
) -> np.ndarray:
    """
    Melatih model Deep Learning LSTM dengan sliding window sekuensial dan menghasilkan
    proyeksi multi-step 7 hari ke depan secara autoregresif rekursif.
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
    
    dataset = TensorDataset(X_t, y_t)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    torch.manual_seed(42)
    model = PyTorchLSTM(input_dim=1, hidden_dim=hidden_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    model.train()
    for _ in range(epochs):
        for bx, by in loader:
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            
    # Proyeksi autoregresif rekursif 7 langkah
    model.eval()
    curr_window = list(scaled_vals[-window_size:])
    preds = []
    with torch.no_grad():
        for _ in range(horizon):
            inp = torch.tensor(np.array(curr_window[-window_size:]), dtype=torch.float32).view(1, window_size, 1)
            p_val = float(model(inp).item())
            preds.append(p_val)
            curr_window.append(p_val)
            
    preds = np.array(preds) * max_val
    return np.clip(preds, 0.0, None)


def croston_sba_forecast(series: pd.Series, horizon: int = 7, alpha: float = 0.1) -> np.ndarray:
    """
    Metode Khusus Pelengkap Sparse Demand: Syntetos-Boylan Approximation (SBA / Croston).
    Memisahkan interval pesanan dan besaran pesanan untuk mengoreksi bias positif pada data intermiten.
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
        
    demand_rate = (1.0 - alpha / 2.0) * (z / p if p > 0 else 0.0)
    return np.full(horizon, max(0.0, float(demand_rate)))


def rolling_origin_evaluation(
    series: pd.Series,
    exog: Optional[pd.DataFrame] = None,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 7),
    horizon: int = 7,
    n_splits: int = 4
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Melakukan evaluasi peramalan out-of-sample berbasis Rolling-Origin Cross-Validation
    khusus membandingkan SARIMAX vs LSTM beserta baseline Seasonal Naive & SARIMA:
    1. Seasonal Naive (Heuristic Baseline)
    2. SARIMA (Statistical Univariate Baseline)
    3. SARIMAX (Statistical Multivariate with Exogenous Variables)
    4. LSTM (Deep Learning Recurrent Neural Network)
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
        
        # 2. SARIMA (Box-Jenkins Univariat)
        try:
            sarima = SARIMAX(
                train_s,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            sarima_fit = sarima.fit(disp=False, maxiter=50)
            sarima_pred = sarima_fit.get_forecast(steps=horizon).predicted_mean.clip(lower=0.0).values
        except Exception:
            sarima_pred = np.full(horizon, train_s.mean())
            
        # 3. SARIMAX (Multivariat dengan Variabel Eksogen)
        if exog is not None:
            train_exog = exog.iloc[:train_end_idx]
            val_exog = exog.iloc[train_end_idx:val_end_idx]
            try:
                sarimax = SARIMAX(
                    train_s,
                    exog=train_exog,
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                sarimax_fit = sarimax.fit(disp=False, maxiter=50)
                sarimax_pred = sarimax_fit.get_forecast(steps=horizon, exog=val_exog).predicted_mean.clip(lower=0.0).values
            except Exception:
                sarimax_pred = sarima_pred
        else:
            sarimax_pred = sarima_pred
            
        # 4. LSTM (Deep Learning Recurrent Network)
        try:
            lstm_pred = lstm_forecast(train_s, horizon=horizon, window_size=14, epochs=30)
        except Exception:
            lstm_pred = sn_pred
            
        preds_dict = {
            'Seasonal Naive': sn_pred,
            'SARIMA': sarima_pred,
            'SARIMAX': sarimax_pred,
            'LSTM': lstm_pred
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
