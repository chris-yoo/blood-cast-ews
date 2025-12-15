#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Exploration Script for redcross_blood.xlsx
Examines the structure, unique values, and time series characteristics
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def explore_data():
    """Comprehensive data exploration"""
    
    # Get data file path
    data_file = Path(__file__).parent.parent.parent / "data" / "redcross_blood.xlsx"
    
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        return
    
    print("=" * 80)
    print("DATA EXPLORATION: redcross_blood.xlsx")
    print("=" * 80)
    print()
    
    # Load data (header=3, columns 1-7 as per baseline)
    print("Loading data...")
    df = pd.read_excel(data_file, header=3, usecols=range(1, 8))
    print(f"✓ Loaded {len(df)} rows")
    print()
    
    # 1. Data Structure
    print("-" * 80)
    print("1. DATA STRUCTURE")
    print("-" * 80)
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print()
    print("Column names and types:")
    print(df.dtypes)
    print()
    print("First few rows:")
    print(df.head(10))
    print()
    print("Missing values:")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.sum() > 0 else "No missing values")
    print()
    
    # 2. Unique Values Analysis
    print("-" * 80)
    print("2. UNIQUE VALUES")
    print("-" * 80)
    
    # Get column names (assuming they are in Korean)
    columns = df.columns.tolist()
    print(f"Columns: {columns}")
    print()
    
    # Try to identify columns by checking unique values
    # Common patterns: 지역, 혈액형, 직업, 연령대, 성별, 날짜, 헌혈건수
    
    # Find region column (지역)
    region_col = None
    bloodtype_col = None
    occupation_col = None
    age_col = None
    gender_col = None
    date_col = None
    count_col = None
    
    for col in columns:
        unique_vals = df[col].unique()[:10]
        # Check if it looks like a region (Korean text, multiple values)
        if df[col].dtype == 'object' and len(df[col].unique()) > 5:
            if region_col is None:
                region_col = col
        # Check if it looks like blood type (A, B, AB, O)
        elif df[col].dtype == 'object' and len(df[col].unique()) <= 4:
            if all(str(v) in ['A', 'B', 'AB', 'O', 'a', 'b', 'ab', 'o'] for v in unique_vals if pd.notna(v)):
                bloodtype_col = col
        # Check if it looks like date
        elif df[col].dtype in ['datetime64[ns]', 'object']:
            try:
                pd.to_datetime(df[col].iloc[0])
                if date_col is None:
                    date_col = col
            except:
                pass
        # Check if it looks like numeric count
        elif df[col].dtype in ['int64', 'float64']:
            if count_col is None:
                count_col = col
    
    # Manual identification - check actual column names
    # From the output, we know: 날짜, 지역, 직업, 연령대, 성별, 혈액형, 헌혈건수
    for col in columns:
        if '지역' in str(col) or col == '지역':
            region_col = col
        elif '혈액형' in str(col) or col == '혈액형':
            bloodtype_col = col
        elif '직업' in str(col) or col == '직업':
            occupation_col = col
        elif '연령대' in str(col) or col == '연령대':
            age_col = col
        elif '성별' in str(col) or col == '성별':
            gender_col = col
        elif '날짜' in str(col) or col == '날짜':
            date_col = col
        elif '헌혈건수' in str(col) or col == '헌혈건수':
            count_col = col
    
    print(f"Region column: {region_col}")
    print(f"Blood type column: {bloodtype_col}")
    print(f"Occupation column: {occupation_col}")
    print(f"Age column: {age_col}")
    print(f"Gender column: {gender_col}")
    print(f"Date column: {date_col}")
    print(f"Count column: {count_col}")
    print()
    
    # Extract unique values
    if region_col:
        regions = sorted(df[region_col].dropna().unique())
        print(f"Unique Regions ({len(regions)}):")
        for r in regions:
            print(f"  - {r}")
        print()
    
    if bloodtype_col:
        bloodtypes = sorted(df[bloodtype_col].dropna().unique())
        print(f"Unique Blood Types ({len(bloodtypes)}):")
        for bt in bloodtypes:
            print(f"  - {bt}")
        print()
    
    if occupation_col:
        occupations = sorted(df[occupation_col].dropna().unique())
        print(f"Unique Occupations ({len(occupations)}):")
        for occ in occupations:
            print(f"  - {occ}")
        print()
    
    if age_col:
        ages = sorted(df[age_col].dropna().unique())
        print(f"Unique Age Groups ({len(ages)}):")
        for age in ages:
            print(f"  - {age}")
        print()
    
    if gender_col:
        genders = sorted(df[gender_col].dropna().unique())
        print(f"Unique Genders ({len(genders)}):")
        for g in genders:
            print(f"  - {g}")
        print()
    
    # 3. Time Series Characteristics
    print("-" * 80)
    print("3. TIME SERIES CHARACTERISTICS")
    print("-" * 80)
    
    if date_col:
        # Convert date column
        df[date_col] = pd.to_datetime(df[date_col])
        date_min = df[date_col].min()
        date_max = df[date_col].max()
        print(f"Date range: {date_min} to {date_max}")
        print(f"Total span: {(date_max - date_min).days} days")
        print(f"Total span: {(date_max - date_min).days / 30.44:.1f} months")
        print()
        
        # Check frequency
        date_counts = df[date_col].value_counts().sort_index()
        print(f"Unique dates: {len(date_counts)}")
        print(f"Most common date frequency: {date_counts.mode().iloc[0] if len(date_counts) > 0 else 'N/A'} records per date")
        print()
    
    # 4. Group by (Region, Blood Type) Analysis
    print("-" * 80)
    print("4. (REGION, BLOOD TYPE) COMBINATIONS")
    print("-" * 80)
    
    if region_col and bloodtype_col and date_col and count_col:
        # Group by region and blood type, aggregate by date
        grouped = df.groupby([region_col, bloodtype_col, date_col])[count_col].sum().reset_index()
        
        # Get unique combinations
        combinations = df.groupby([region_col, bloodtype_col]).size().reset_index(name='count')
        print(f"Total unique (Region, Blood Type) combinations: {len(combinations)}")
        print()
        
        # Analyze time series for each combination
        print("Time series length for each combination:")
        ts_lengths = []
        valid_combinations = []
        
        for idx, row in combinations.iterrows():
            region = row[region_col]
            bloodtype = row[bloodtype_col]
            
            # Filter data for this combination
            combo_data = df[(df[region_col] == region) & (df[bloodtype_col] == bloodtype)]
            
            # Group by date and sum
            ts = combo_data.groupby(date_col)[count_col].sum()
            ts.index = pd.to_datetime(ts.index)
            ts = ts.sort_index()
            
            # Resample to monthly (MS = Month Start)
            ts_monthly = ts.resample('MS').sum()
            
            length = len(ts_monthly)
            ts_lengths.append({
                'region': region,
                'bloodtype': bloodtype,
                'length': length,
                'min_date': ts_monthly.index.min(),
                'max_date': ts_monthly.index.max(),
                'total_count': ts_monthly.sum()
            })
            
            if length >= 24:  # Minimum for Holt-Winter
                valid_combinations.append((region, bloodtype))
        
        # Sort by length
        ts_lengths_df = pd.DataFrame(ts_lengths).sort_values('length', ascending=False)
        print(ts_lengths_df.head(20))
        print()
        
        print(f"Combinations with >= 24 months (suitable for Holt-Winter): {len(valid_combinations)}")
        print(f"Combinations with < 24 months: {len(combinations) - len(valid_combinations)}")
        print()
        
        # Show sample time series
        if len(valid_combinations) > 0:
            sample_region, sample_bloodtype = valid_combinations[0]
            sample_data = df[(df[region_col] == sample_region) & (df[bloodtype_col] == sample_bloodtype)]
            sample_ts = sample_data.groupby(date_col)[count_col].sum()
            sample_ts.index = pd.to_datetime(sample_ts.index)
            sample_ts = sample_ts.resample('MS').sum().sort_index()
            
            print(f"Sample time series: {sample_region} | {sample_bloodtype}")
            print(f"Length: {len(sample_ts)} months")
            print(f"Date range: {sample_ts.index.min()} to {sample_ts.index.max()}")
            print("First 12 values:")
            print(sample_ts.head(12))
            print("Last 12 values:")
            print(sample_ts.tail(12))
            print()
    
    # 5. Summary Report
    print("-" * 80)
    print("5. SUMMARY REPORT")
    print("-" * 80)
    
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'date_range': {
            'min': str(date_min) if date_col else None,
            'max': str(date_max) if date_col else None
        },
        'unique_regions': len(regions) if region_col else 0,
        'unique_bloodtypes': len(bloodtypes) if bloodtype_col else 0,
        'unique_occupations': len(occupations) if occupation_col else 0,
        'unique_ages': len(ages) if age_col else 0,
        'unique_genders': len(genders) if gender_col else 0,
        'total_combinations': len(combinations) if region_col and bloodtype_col else 0,
        'valid_combinations_24plus': len(valid_combinations) if region_col and bloodtype_col else 0,
        'column_mapping': {
            'region': region_col,
            'bloodtype': bloodtype_col,
            'occupation': occupation_col,
            'age': age_col,
            'gender': gender_col,
            'date': date_col,
            'count': count_col
        }
    }
    
    if region_col:
        summary['regions'] = regions
    if bloodtype_col:
        summary['bloodtypes'] = bloodtypes
    
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()
    
    # Save summary to file
    summary_file = Path(__file__).parent.parent / "data_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✓ Summary saved to {summary_file}")
    
    print()
    print("=" * 80)
    print("EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    explore_data()

