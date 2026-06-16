# =============================================================================
# ETL PIPELINE - Automation Operations BI Dashboards
# Description: Cleans raw Excel data and loads into MySQL automation_ops DB
# =============================================================================
# PIPELINE:
#   Raw Excel → pandas clean → MySQL (automation_ops) → Power BI
# =============================================================================

import pandas as pd
import mysql.connector
from mysql.connector import errorcode
import os
import math

# -----------------------------------------------------------------------------
# SECTION 1 — MySQL CONNECTION DETAILS
# -----------------------------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "pavani",
    "password": "Pavani@123",
    "database": "automation_ops"
}

RAW_DIR = "../raw_data/"

# =============================================================================
# SECTION 2 — HELPER FUNCTIONS
# =============================================================================

def fix_dates(series):
    """Converts any date format to YYYY-MM-DD for MySQL compatibility"""
    return pd.to_datetime(series, errors='coerce').dt.strftime('%Y-%m-%d')

def fix_column_names(df):
    """Standardizes column names — no spaces, all uppercase"""
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
        .str.replace(' ', '_')
        .str.replace(r'[^A-Z0-9_]', '', regex=True)
    )
    return df

def standardize_text(df, columns):
    """Title Case + strip whitespace on text columns"""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
            df[col] = df[col].replace('Nan', None)
    return df

def clean_value(v):
    """
    Converts any NaN, NaT, None, or empty string to Python None
    so MySQL stores it as NULL — no 'nan' strings slip through
    """
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if str(v).strip().lower() in ('nan', 'nat', 'none', ''):
        return None
    return v

def log_cleaning(name, before, after, df):
    """Prints cleaning summary for audit trail"""
    nulls = df.isnull().sum()
    null_cols = nulls[nulls > 0].to_dict()
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  Rows before: {before:,}  |  Rows after: {after:,}  |  Dropped: {before-after:,}")
    if null_cols:
        print(f"  Remaining nulls (acceptable): {null_cols}")
    print(f"{'='*60}")

# =============================================================================
# SECTION 3 — CLEAN ALL 4 DATASETS
# =============================================================================

def clean_machine_health():
    print("\n[1/4] Cleaning machine_health_log...")
    df = pd.read_excel(RAW_DIR + "machine_health_log.xlsx")
    before = len(df)
    df = fix_column_names(df)
    df['DATE'] = fix_dates(df['DATE'])
    df = df.dropna(subset=['MACHINE_ID'])
    df['SHIFT'] = df['SHIFT'].fillna('Unknown')
    df = standardize_text(df, ['MACHINE_NAME', 'STATUS', 'LOCATION', 'SHIFT'])
    df['ERROR_CODE'] = df['ERROR_CODE'].fillna('None')
    df['NOTES'] = df['NOTES'].fillna('')
    df = df.drop_duplicates()
    log_cleaning("MACHINE HEALTH LOG", before, len(df), df)
    return df

def clean_production_output():
    print("\n[2/4] Cleaning production_output_log...")
    df = pd.read_excel(RAW_DIR + "production_output_log.xlsx")
    before = len(df)
    df = fix_column_names(df)
    df['DATE'] = fix_dates(df['DATE'])
    invalid = df['UNITS_FAILED'] > df['UNITS_PRODUCED']
    df = df[~invalid]
    df = standardize_text(df, ['SHIFT', 'LINE_ID', 'PRODUCT_TYPE'])
    df['PASS_RATE_PCT'] = round(
        (df['UNITS_PRODUCED'] - df['UNITS_FAILED']) / df['UNITS_PRODUCED'] * 100, 2)
    df['EFFICIENCY_PCT'] = round(df['UNITS_PRODUCED'] / df['UNITS_PLANNED'] * 100, 2)
    df['NOTES'] = df['NOTES'].fillna('')
    df = df.drop_duplicates()
    log_cleaning("PRODUCTION OUTPUT LOG", before, len(df), df)
    return df

def clean_maintenance_workorders():
    print("\n[3/4] Cleaning maintenance_workorders...")
    df = pd.read_excel(RAW_DIR + "maintenance_workorders.xlsx")
    before = len(df)
    df = fix_column_names(df)
    df['REPORTED_DATE']  = fix_dates(df['REPORTED_DATE'])
    df['SCHEDULED_DATE'] = fix_dates(df['SCHEDULED_DATE'])
    df['COMPLETED_DATE'] = fix_dates(df['COMPLETED_DATE'])
    df['ROOT_CAUSE'] = df['ROOT_CAUSE'].fillna('Under Investigation')
    df = standardize_text(df, ['WO_TYPE', 'PRIORITY', 'STATUS', 'MACHINE_NAME', 'PARTS_USED'])
    df['RESOLUTION_DAYS'] = (
        pd.to_datetime(df['COMPLETED_DATE']) - pd.to_datetime(df['REPORTED_DATE'])
    ).dt.days
    today = pd.Timestamp.today().normalize()
    df['OVERDUE_FLAG'] = (
        (df['STATUS'] != 'Completed') &
        (pd.to_datetime(df['SCHEDULED_DATE']) < today)
    ).astype(int)
    df = df.drop_duplicates()
    log_cleaning("MAINTENANCE WORK ORDERS", before, len(df), df)
    return df

def clean_quality_defects():
    print("\n[4/4] Cleaning quality_defects_log...")
    df = pd.read_excel(RAW_DIR + "quality_defects_log.xlsx")
    before = len(df)
    df = fix_column_names(df)
    df['DATE'] = fix_dates(df['DATE'])
    df['REWORK_HOURS'] = df.apply(
        lambda r: 0 if pd.isnull(r['REWORK_HOURS']) and r['DISPOSITION'] == 'Scrap'
                  else r['REWORK_HOURS'], axis=1)
    df = standardize_text(df, ['SHIFT','LINE_ID','PRODUCT_TYPE',
                                'DEFECT_TYPE','SEVERITY','DISPOSITION'])
    severity_map = {'Critical': 3, 'Major': 2, 'Minor': 1}
    df['SEVERITY_SCORE'] = df['SEVERITY'].map(severity_map).fillna(0).astype(int)
    df['NOTES'] = df['NOTES'].fillna('')
    df = df.drop_duplicates()
    log_cleaning("QUALITY DEFECTS LOG", before, len(df), df)
    return df

# =============================================================================
# SECTION 4 — CONNECT TO MYSQL
# =============================================================================

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("\n  ✅ Connected to MySQL — automation_ops")
        return conn
    except mysql.connector.Error as e:
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("  ❌ Wrong username or password")
        elif e.errno == errorcode.ER_BAD_DB_ERROR:
            print("  ❌ Database automation_ops not found — did you create it in Workbench?")
        else:
            print(f"  ❌ Error: {e}")
        raise

# =============================================================================
# SECTION 5 — CREATE TABLES IN MYSQL
# =============================================================================

CREATE_TABLES = {

    "machine_health": """
        CREATE TABLE IF NOT EXISTS machine_health (
            LOG_ID          VARCHAR(20),
            MACHINE_ID      VARCHAR(10),
            MACHINE_NAME    VARCHAR(50),
            LOCATION        VARCHAR(20),
            DATE            DATE,
            SHIFT           VARCHAR(20),
            STATUS          VARCHAR(20),
            UPTIME_HOURS    FLOAT,
            DOWNTIME_HOURS  FLOAT,
            ERROR_CODE      VARCHAR(20),
            OPERATOR_ID     VARCHAR(10),
            NOTES           TEXT
        )
    """,

    "production_output": """
        CREATE TABLE IF NOT EXISTS production_output (
            RECORD_ID       VARCHAR(20),
            DATE            DATE,
            SHIFT           VARCHAR(20),
            LINE_ID         VARCHAR(20),
            PRODUCT_TYPE    VARCHAR(30),
            UNITS_PLANNED   INT,
            UNITS_PRODUCED  INT,
            UNITS_FAILED    INT,
            OPERATOR_ID     VARCHAR(10),
            CYCLE_TIME_MIN  FLOAT,
            NOTES           TEXT,
            PASS_RATE_PCT   FLOAT,
            EFFICIENCY_PCT  FLOAT
        )
    """,

    "maintenance_workorders": """
        CREATE TABLE IF NOT EXISTS maintenance_workorders (
            WO_ID           VARCHAR(10),
            MACHINE_ID      VARCHAR(10),
            MACHINE_NAME    VARCHAR(50),
            WO_TYPE         VARCHAR(20),
            PRIORITY        VARCHAR(20),
            REPORTED_DATE   DATE,
            SCHEDULED_DATE  DATE,
            COMPLETED_DATE  DATE,
            TECHNICIAN_ID   VARCHAR(10),
            PARTS_USED      VARCHAR(30),
            LABOR_HOURS     FLOAT,
            STATUS          VARCHAR(20),
            ROOT_CAUSE      VARCHAR(50),
            COST_USD        FLOAT,
            RESOLUTION_DAYS INT,
            OVERDUE_FLAG    INT
        )
    """,

    "quality_defects": """
        CREATE TABLE IF NOT EXISTS quality_defects (
            DEFECT_ID       VARCHAR(20),
            DATE            DATE,
            SHIFT           VARCHAR(20),
            LINE_ID         VARCHAR(20),
            MACHINE_ID      VARCHAR(10),
            PRODUCT_TYPE    VARCHAR(30),
            DEFECT_TYPE     VARCHAR(30),
            SEVERITY        VARCHAR(20),
            UNITS_AFFECTED  INT,
            INSPECTOR_ID    VARCHAR(10),
            DISPOSITION     VARCHAR(20),
            REWORK_HOURS    FLOAT,
            COST_USD        FLOAT,
            NOTES           TEXT,
            SEVERITY_SCORE  INT
        )
    """
}

def create_tables(conn):
    cursor = conn.cursor()
    print("\n[MySQL] Creating tables...")
    for table_name, ddl in CREATE_TABLES.items():
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(ddl)
        print(f"  ✓ Table '{table_name}' ready")
    conn.commit()
    cursor.close()

# =============================================================================
# SECTION 6 — LOAD DATA INTO MYSQL
# =============================================================================

def load_dataframe_to_mysql(conn, df, table_name):
    """
    Inserts a pandas DataFrame into a MySQL table.
    Uses clean_value() to guarantee no nan strings reach MySQL.
    """
    cursor = conn.cursor()

    cols         = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql          = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

    # Clean every value in every row — converts nan/NaT/None → Python None → MySQL NULL
    rows = [
        tuple(clean_value(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    cursor.executemany(sql, rows)
    conn.commit()
    print(f"  ✓ '{table_name}' — {cursor.rowcount:,} rows inserted")
    cursor.close()

# =============================================================================
# SECTION 7 — VERIFY WITH SQL QUERIES
# =============================================================================

def run_verification_queries(conn):
    cursor = conn.cursor()
    print("\n[SQL] Running verification queries...")

    queries = {
        "Row counts per table": """
            SELECT 'machine_health'          AS table_name, COUNT(*) AS row_count FROM machine_health
            UNION ALL
            SELECT 'production_output',      COUNT(*) FROM production_output
            UNION ALL
            SELECT 'maintenance_workorders', COUNT(*) FROM maintenance_workorders
            UNION ALL
            SELECT 'quality_defects',        COUNT(*) FROM quality_defects
        """,
        "Machine uptime % by machine": """
            SELECT
                MACHINE_ID,
                MACHINE_NAME,
                ROUND(SUM(UPTIME_HOURS) /
                    (SUM(UPTIME_HOURS) + SUM(DOWNTIME_HOURS)) * 100, 2) AS UPTIME_PCT,
                SUM(CASE WHEN STATUS = 'Down' THEN 1 ELSE 0 END) AS DOWN_COUNT
            FROM machine_health
            GROUP BY MACHINE_ID, MACHINE_NAME
            ORDER BY UPTIME_PCT ASC
        """,
        "Production efficiency by line": """
            SELECT
                LINE_ID,
                ROUND(AVG(EFFICIENCY_PCT), 2) AS AVG_EFFICIENCY_PCT,
                ROUND(AVG(PASS_RATE_PCT), 2)  AS AVG_PASS_RATE_PCT,
                SUM(UNITS_FAILED)             AS TOTAL_FAILED
            FROM production_output
            GROUP BY LINE_ID
        """,
        "Open vs completed work orders": """
            SELECT STATUS, COUNT(*) AS COUNT, ROUND(SUM(COST_USD), 2) AS TOTAL_COST
            FROM maintenance_workorders
            GROUP BY STATUS
        """,
        "Top defect types by count": """
            SELECT DEFECT_TYPE, SEVERITY, COUNT(*) AS DEFECT_COUNT,
                   SUM(UNITS_AFFECTED) AS UNITS_AFFECTED
            FROM quality_defects
            GROUP BY DEFECT_TYPE, SEVERITY
            ORDER BY DEFECT_COUNT DESC
            LIMIT 5
        """
    }

    for label, query in queries.items():
        print(f"\n  ── {label} ──")
        cursor.execute(query)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        df_result = pd.DataFrame(rows, columns=cols)
        print(df_result.to_string(index=False))

    cursor.close()

# =============================================================================
# SECTION 8 — MAIN: RUN FULL PIPELINE
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AUTOMATION OPERATIONS — ETL TO MYSQL")
    print("  Starting full pipeline...")
    print("="*60)

    # Step 1: Clean all 4 datasets
    machine_health    = clean_machine_health()
    production_output = clean_production_output()
    maintenance_wos   = clean_maintenance_workorders()
    quality_defects   = clean_quality_defects()

    # Step 2: Connect to MySQL
    conn = get_connection()

    # Step 3: Create tables
    create_tables(conn)

    # Step 4: Load clean data into MySQL
    print("\n[MySQL] Loading data...")
    load_dataframe_to_mysql(conn, machine_health,    "machine_health")
    load_dataframe_to_mysql(conn, production_output, "production_output")
    load_dataframe_to_mysql(conn, maintenance_wos,   "maintenance_workorders")
    load_dataframe_to_mysql(conn, quality_defects,   "quality_defects")

    # Step 5: Verify with SQL queries
    run_verification_queries(conn)

    conn.close()

    print("\n" + "="*60)
    print("  ✅ PIPELINE COMPLETE")
    print("  All 4 tables loaded into automation_ops MySQL database")
    print("  Next step → Open Power BI Desktop → Get Data → MySQL")
    print("="*60 + "\n")