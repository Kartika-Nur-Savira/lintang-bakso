"""
Module: Modeling
Fungsi-fungsi estimasi, tuning hyperparameter grid-search terkontrol,
diagnostik residual statistik, dan forecasting untuk model SARIMA dan SARIMAX.
"""

import warnings
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResultsWrapper
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera

# Abaikan warning konvergensi sementara saat grid search jika ada parameter non-stasioner
warnings.filterwarnings('ignore')


def fit_sarima_model(
    endog: pd.Series,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 7),
    enforce_stationarity: bool = False,
    enforce_invertibility: bool = False
) -> SARIMAXResultsWrapper:
    """
    Membuat dan melatih model SARIMA murni tanpa variabel eksogen.
    """
    model = SARIMAX(
        endog=endog,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=enforce_stationarity,
        enforce_invertibility=enforce_invertibility
    )
    results = model.fit(disp=False, maxiter=200)
    return results


def fit_sarimax_model(
    endog: pd.Series,
    exog: pd.DataFrame,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 7),
    enforce_stationarity: bool = False,
    enforce_invertibility: bool = False
) -> SARIMAXResultsWrapper:
    """
    Membuat dan melatih model SARIMAX dengan matriks variabel eksogen.
    """
    model = SARIMAX(
        endog=endog,
        exog=exog,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=enforce_stationarity,
        enforce_invertibility=enforce_invertibility
    )
    results = model.fit(disp=False, maxiter=200)
    return results


def fast_candidate_search(
    endog: pd.Series,
    exog: Optional[pd.DataFrame] = None,
    candidate_specs: Optional[List[Tuple[Tuple, Tuple]]] = None,
    criterion: str = 'aic'
) -> Tuple[Tuple, Tuple, pd.DataFrame]:
    """
    Pencarian efisien berbasis daftar kandidat spesifikasi Box-Jenkins terkurasi
    untuk mempercepat konvergensi tanpa mengurangi ketepatan seleksi model.
    """
    if candidate_specs is None:
        candidate_specs = [
            ((1, 0, 1), (1, 0, 0, 7)),
            ((1, 1, 1), (1, 1, 1, 7)),
            ((1, 0, 0), (1, 0, 0, 7)),
            ((0, 1, 1), (0, 1, 1, 7)),
            ((2, 0, 1), (1, 0, 1, 7)),
            ((1, 0, 0), (0, 0, 0, 7)),
            ((0, 0, 0), (1, 0, 0, 7))
        ]
        
    results_list = []
    best_score = float('inf')
    best_order = candidate_specs[0][0]
    best_seasonal = candidate_specs[0][1]
    
    for order, seasonal_order in candidate_specs:
        try:
            if exog is not None:
                model = SARIMAX(
                    endog=endog,
                    exog=exog,
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
            else:
                model = SARIMAX(
                    endog=endog,
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
            res = model.fit(disp=False, maxiter=40, method='lbfgs')
            score = res.aic if criterion == 'aic' else res.bic
            results_list.append({
                'order': str(order),
                'seasonal_order': str(seasonal_order),
                'aic': res.aic,
                'bic': res.bic
            })
            if score < best_score:
                best_score = score
                best_order = order
                best_seasonal = seasonal_order
        except Exception:
            continue
            
    df_results = pd.DataFrame(results_list)
    if not df_results.empty:
        df_results = df_results.sort_values(criterion).reset_index(drop=True)
    return best_order, best_seasonal, df_results



def run_residual_diagnostics(results: SARIMAXResultsWrapper, lags: int = 14) -> Dict:
    """
    Melakukan uji diagnostik statistik komprehensif terhadap residual model:
    1. Ljung-Box Test untuk autokorelasi residual (H0: tidak ada autokorelasi, residual white noise).
    2. Jarque-Bera Test untuk normalitas residual (H0: residual berdistribusi normal).
    3. Rangkuman statistik deskriptif residual (Mean, Std, Skew, Kurtosis).
    """
    residuals = results.resid
    
    # Ljung-Box Test
    lb_df = acorr_ljungbox(residuals, lags=[7, lags], return_format='DataFrame')
    lb_stat_7 = lb_df.loc[7, 'lb_stat']
    lb_pvalue_7 = lb_df.loc[7, 'lb_pvalue']
    lb_stat_14 = lb_df.loc[lags, 'lb_stat']
    lb_pvalue_14 = lb_df.loc[lags, 'lb_pvalue']
    
    # Jarque-Bera Test
    jb_stat, jb_pvalue, skew, kurtosis = jarque_bera(residuals)
    
    # White noise check: p-value Ljung-Box > 0.05
    is_white_noise = (lb_pvalue_7 > 0.05) and (lb_pvalue_14 > 0.05)
    is_normal = jb_pvalue > 0.05
    
    return {
        "residual_mean": float(residuals.mean()),
        "residual_std": float(residuals.std()),
        "residual_skew": float(skew),
        "residual_kurtosis": float(kurtosis),
        "lb_stat_lag7": float(lb_stat_7),
        "lb_pvalue_lag7": float(lb_pvalue_7),
        "lb_stat_lag14": float(lb_stat_14),
        "lb_pvalue_lag14": float(lb_pvalue_14),
        "jb_stat": float(jb_stat),
        "jb_pvalue": float(jb_pvalue),
        "is_white_noise": bool(is_white_noise),
        "is_normal": bool(is_normal)
    }


def predict_7_days_ahead(
    results: SARIMAXResultsWrapper,
    horizon: int = 7,
    exog_future: Optional[pd.DataFrame] = None,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Menghasilkan proyeksi 7 hari ke depan lengkap dengan interval kepercayaan (Confidence Interval 95%).
    Menerapkan batas bawah 0 (kuantitas permintaan fisik tidak mungkin bernilai negatif).
    """
    forecast_res = results.get_forecast(steps=horizon, exog=exog_future)
    mean_forecast = forecast_res.predicted_mean
    conf_int = forecast_res.conf_int(alpha=alpha)
    
    df_forecast = pd.DataFrame({
        'forecast': mean_forecast,
        'ci_lower': conf_int.iloc[:, 0].clip(lower=0.0),
        'ci_upper': conf_int.iloc[:, 1].clip(lower=0.0)
    })
    
    # Floor forecast di 0
    df_forecast['forecast'] = df_forecast['forecast'].clip(lower=0.0)
    # Rekomendasi operasional: Pembulatan ke atas (ceil) untuk buffer stok aman dapur,
    # atau pembulatan standar (round)
    df_forecast['forecast_rounded'] = df_forecast['forecast'].round().astype(int)
    df_forecast['forecast_safe_stock'] = np.ceil(df_forecast['forecast']).astype(int)
    
    return df_forecast


# ==============================================================================
# DEEP LEARNING: LSTM (LONG SHORT-TERM MEMORY) MODELING
# ==============================================================================
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader


class PyTorchLSTM(nn.Module):
    """
    Arsitektur Deep Learning Recurrent Neural Network (LSTM)
    untuk peramalan sekuensial deret waktu harian.
    """
    def __init__(self, input_dim: int = 1, hidden_dim: int = 16, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def fit_lstm_model(
    series: pd.Series,
    window_size: int = 14,
    hidden_dim: int = 16,
    epochs: int = 30,
    lr: float = 0.02
) -> Tuple[PyTorchLSTM, float]:
    """
    Melatih model LSTM pada sliding window historis.
    Mengembalikan model terlatih dan nilai penskalaan maksimum (max_val) untuk unscaling.
    """
    vals = series.values.astype(float)
    max_val = float(np.max(vals))
    if max_val == 0.0:
        return PyTorchLSTM(hidden_dim=hidden_dim), 1.0
        
    scaled_vals = vals / max_val
    X, y = [], []
    for i in range(len(scaled_vals) - window_size):
        X.append(scaled_vals[i : i + window_size])
        y.append(scaled_vals[i + window_size])
        
    if len(X) < 10:
        return PyTorchLSTM(hidden_dim=hidden_dim), max_val
        
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
            
    return model, max_val


def predict_lstm_7_days_ahead(
    model: PyTorchLSTM,
    series: pd.Series,
    max_val: float,
    horizon: int = 7,
    window_size: int = 14
) -> np.ndarray:
    """
    Menghasilkan proyeksi 7 hari ke depan secara autoregresif rekursif menggunakan model LSTM.
    """
    vals = series.values.astype(float)
    if max_val == 0.0 or len(vals) < window_size:
        return np.zeros(horizon)
        
    scaled_vals = list(vals / max_val)
    curr_window = list(scaled_vals[-window_size:])
    preds = []
    
    model.eval()
    with torch.no_grad():
        for _ in range(horizon):
            inp = torch.tensor(np.array(curr_window[-window_size:]), dtype=torch.float32).view(1, window_size, 1)
            pred_step = float(model(inp).item())
            preds.append(pred_step)
            curr_window.append(pred_step)
            
    preds = np.array(preds) * max_val
    return np.clip(preds, 0.0, None)
