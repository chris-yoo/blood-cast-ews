#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Forecast Service - Holt-Winter model training and forecasting
Based on baseline code provided
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import warnings
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tools.sm_exceptions import ConvergenceWarning, ValueWarning

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=ValueWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)


def forecast_hw(train, seasonal_periods=12):
    """
    Holt-Winter forecasting function from baseline
    
    Args:
        train: pandas Series with DatetimeIndex (monthly frequency)
        seasonal_periods: Number of periods in a season (default 12 for monthly)
    
    Returns:
        Forecasted value for next period, or np.nan if insufficient data
    """
    if len(train) < 24:  # Minimum 2 seasons
        return np.nan
    
    try:
        model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal="add",
            seasonal_periods=seasonal_periods,
            initialization_method="estimated"
        ).fit(optimized=True)
        
        forecast = model.forecast(1)
        return float(forecast.iloc[0])
    except Exception as e:
        print(f"Error in Holt-Winter forecast: {e}")
        return np.nan


class ForecastService:
    """Service for loading data, training models, and generating forecasts"""
    
    def __init__(self, data_file=None):
        """
        Initialize forecast service
        
        Args:
            data_file: Path to Excel file. If None, uses default path.
        """
        if data_file is None:
            data_file = Path(__file__).parent.parent.parent / "data" / "redcross_blood.xlsx"
        
        self.data_file = Path(data_file)
        self.df = None
        self.time_series = {}  # Cache for (region, bloodtype) -> time series
        self.last_date = None
        self.regions = []
        self.bloodtypes = []
        
    def load_data(self):
        """Load and prepare data from Excel file"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        # Load data (header=3, columns 1-7)
        self.df = pd.read_excel(self.data_file, header=3, usecols=range(1, 8))
        
        # Convert date column
        self.df['날짜'] = pd.to_datetime(self.df['날짜'])
        
        # Get unique regions and blood types
        self.regions = sorted(self.df['지역'].dropna().unique())
        self.bloodtypes = sorted(self.df['혈액형'].dropna().unique())
        
        # Get last date
        self.last_date = self.df['날짜'].max()
        
        # Build time series for each (region, bloodtype) combination
        self._build_time_series()
        
        return self
    
    def _build_time_series(self):
        """Build monthly time series for each (region, bloodtype) combination"""
        self.time_series = {}
        
        for region in self.regions:
            for bloodtype in self.bloodtypes:
                # Filter data for this combination
                combo_data = self.df[
                    (self.df['지역'] == region) & 
                    (self.df['혈액형'] == bloodtype)
                ]
                
                if len(combo_data) == 0:
                    continue
                
                # Group by date and sum 헌혈건수
                ts = combo_data.groupby('날짜')['헌혈건수'].sum()
                ts.index = pd.to_datetime(ts.index)
                ts = ts.sort_index()
                
                # Resample to monthly (MS = Month Start)
                ts_monthly = ts.resample('MS').sum()
                
                # Only store if we have >= 24 months
                if len(ts_monthly) >= 24:
                    self.time_series[(region, bloodtype)] = ts_monthly
        
        return self
    
    def get_time_series(self, region, bloodtype):
        """Get time series for a specific (region, bloodtype) combination"""
        key = (region, bloodtype)
        if key not in self.time_series:
            return None
        return self.time_series[key].copy()
    
    def forecast(self, region, bloodtype, n_months=3):
        """
        Forecast n_months ahead for a specific (region, bloodtype)
        
        Args:
            region: Region name (한글)
            bloodtype: Blood type (A, B, AB, O)
            n_months: Number of months to forecast (default 3)
        
        Returns:
            List of forecasted values for 1, 2, ..., n_months ahead
        """
        ts = self.get_time_series(region, bloodtype)
        if ts is None:
            return [np.nan] * n_months
        
        forecasts = []
        hist = ts.copy()
        
        for i in range(n_months):
            forecast_val = forecast_hw(hist)
            forecasts.append(forecast_val)
            
            # Add forecast to history for next iteration
            if not np.isnan(forecast_val):
                next_date = hist.index[-1] + pd.DateOffset(months=1)
                hist = pd.concat([hist, pd.Series([forecast_val], index=[next_date])])
        
        return forecasts
    
    def calculate_severity(self, region, bloodtype, forecast_value, month_ahead):
        """
        Calculate severity level based on threshold
        
        Args:
            region: Region name
            bloodtype: Blood type
            forecast_value: Forecasted value
            month_ahead: Which month ahead (1, 2, or 3)
        
        Returns:
            Severity level: '관심', '주의', '경계', '심각', or None if insufficient data
        """
        ts = self.get_time_series(region, bloodtype)
        if ts is None or np.isnan(forecast_value):
            return None
        
        # Calculate baseline: recent 12-month average
        if len(ts) >= 12:
            baseline = ts.iloc[-12:].mean()
        else:
            baseline = ts.mean()
        
        # Calculate percentage change
        pct_change = ((forecast_value - baseline) / baseline) * 100
        
        # Determine severity based on threshold
        # 관심 (Blue): -10% to -20% from baseline
        # 주의 (Yellow): -20% to -30% from baseline
        # 경계 (Orange): -30% to -40% from baseline
        # 심각 (Red): < -40% from baseline
        
        if pct_change >= -10:
            return None  # No shortage
        elif pct_change >= -20:
            return '관심'  # Blue
        elif pct_change >= -30:
            return '주의'  # Yellow
        elif pct_change >= -40:
            return '경계'  # Orange
        else:
            return '심각'  # Red
    
    def get_all_forecasts(self, include_all=False):
        """
        Get forecasts for all (region, bloodtype) combinations for 1, 2, 3 months ahead
        
        Args:
            include_all: If True, include all forecasts even without severity warnings.
                       If False, only include forecasts with severity warnings (default).
        
        Returns:
            List of dictionaries with forecast data
        """
        results = []
        
        for region in self.regions:
            for bloodtype in self.bloodtypes:
                # Forecast 1, 2, 3 months ahead
                forecasts = self.forecast(region, bloodtype, n_months=3)
                
                for month_idx, forecast_val in enumerate(forecasts, start=1):
                    if np.isnan(forecast_val):
                        continue
                    
                    severity = self.calculate_severity(region, bloodtype, forecast_val, month_idx)
                    
                    # Include if there's a shortage, or if include_all is True
                    if severity or include_all:
                        results.append({
                            'id': f"{region}_{bloodtype}_{month_idx}",
                            'region': region,
                            'bloodType': bloodtype,
                            'month': month_idx,
                            'forecastValue': float(forecast_val),
                            'severity': severity or '정상'  # '정상' if no severity
                        })
        
        return results


# Global service instance (lazy loaded)
_service_instance = None

def get_forecast_service():
    """Get or create forecast service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ForecastService()
        _service_instance.load_data()
    return _service_instance

