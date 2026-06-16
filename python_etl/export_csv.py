import pandas as pd
import math

RAW = '../raw_data/'
OUT = '../clean_data/'

def fix_dates(s):
    return pd.to_datetime(s, errors='coerce').dt.strftime('%Y-%m-%d')

def fix_cols(df):
    df.columns = df.columns.str.strip().str.upper().str.replace(' ','_').str.replace(r'[^A-Z0-9_]','',regex=True)
    return df

# Machine Health
df = fix_cols(pd.read_excel(RAW+'machine_health_log.xlsx'))
df['DATE'] = fix_dates(df['DATE'])
df = df.dropna(subset=['MACHINE_ID'])
df.to_csv(OUT+'machine_health.csv', index=False)
print('machine_health.csv done')

# Production Output
df = fix_cols(pd.read_excel(RAW+'production_output_log.xlsx'))
df['DATE'] = fix_dates(df['DATE'])
df.to_csv(OUT+'production_output.csv', index=False)
print('production_output.csv done')

# Maintenance
df = fix_cols(pd.read_excel(RAW+'maintenance_workorders.xlsx'))
df['REPORTED_DATE'] = fix_dates(df['REPORTED_DATE'])
df['SCHEDULED_DATE'] = fix_dates(df['SCHEDULED_DATE'])
df['COMPLETED_DATE'] = fix_dates(df['COMPLETED_DATE'])
df.to_csv(OUT+'maintenance_workorders.csv', index=False)
print('maintenance_workorders.csv done')

# Quality Defects
df = fix_cols(pd.read_excel(RAW+'quality_defects_log.xlsx'))
df['DATE'] = fix_dates(df['DATE'])
df.to_csv(OUT+'quality_defects.csv', index=False)
print('quality_defects.csv done')

print('All CSVs exported to clean_data folder!')