# Automation Operations — BI Dashboard Project

A complete end-to-end Business Intelligence pipeline built to demonstrate operational analytics capabilities for a manufacturing/automation environment.

---

## Project Overview

This project simulates a real-world data pipeline for monitoring and managing automation operations — including machine health, production output, maintenance work orders, and quality defects.

The goal is to transform raw operational data from multiple sources into simple, actionable dashboards that help operations managers and floor supervisors make faster, better decisions.

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Raw Data | Microsoft Excel | Simulated machine logs and operational data |
| ETL & Cleaning | Python (pandas) | Data cleaning, transformation, and export |
| Database | MySQL | Structured storage of clean operational data |
| Visualization | Power BI Desktop | Interactive dashboards for management |
| Version Control | GitHub | Project documentation and sharing |

---

## Pipeline Architecture

```
Raw Excel Files (dirty data)
        ↓
Python ETL (pandas)
- Fix mixed date formats
- Remove duplicates
- Handle null values
- Standardize text casing
- Calculate derived KPIs
        ↓
MySQL Database (automation_ops)
- machine_health
- production_output
- maintenance_workorders
- quality_defects
        ↓
Clean CSV Export
        ↓
Power BI Desktop
- 4 interactive dashboards
- DAX measures
- Slicers and filters
```

---

## Project Structure

```
automation-bi-dashboards/
├── raw_data/
│   ├── machine_health_log.xlsx
│   ├── production_output_log.xlsx
│   ├── maintenance_workorders.xlsx
│   └── quality_defects_log.xlsx
├── python_etl/
│   ├── etl_mysql_v2.py        ← Full ETL pipeline to MySQL
│   └── export_csv.py          ← CSV export for Power BI
├── clean_data/
│   ├── machine_health.csv
│   ├── production_output.csv
│   ├── maintenance_workorders.csv
│   └── quality_defects.csv
├── PowerBI/
│   └── AutomationAnalytics.pbix
├── screenshots/
│   ├── dashboard1_machine_health.jpeg
│   ├── dashboard2_production_output.jpeg
│   ├── dashboard3_maintenance_workorders.jpeg
│   └── dashboard4_quality_defects.jpeg
└── README.md
```

---

## Dashboards

### Dashboard 1 — Machine Health & Uptime
Monitors the operational status of all machines on the floor.

**Visuals:**
- Total machines tracked
- Average uptime hours
- Total downtime hours
- Uptime by machine (bar chart)
- Status breakdown — Running / Down / Maintenance / Error (donut chart)
- Filter by shift (slicer)

**Key Insight:** Only 58% of machine time is productive — 41% is split between errors, downtime, and maintenance, significantly below the industry standard of 85% OEE.

---

### Dashboard 2 — Production Output
Tracks daily production performance across all lines and shifts.

**Visuals:**
- Total units produced
- Total units failed
- Average efficiency %
- Daily production trend (line chart)
- Units produced vs planned by line (bar chart)
- Filter by shift and date (slicers)

**Key Insight:** Average efficiency is 90.43% with 1,809 failed units out of 47K produced — a 3.8% failure rate across all lines.

---

### Dashboard 3 — Maintenance Work Orders
Provides visibility into open, overdue, and completed maintenance activities.

**Visuals:**
- Total work orders
- Overdue work orders
- Total maintenance cost
- Status breakdown (donut chart)
- Work orders by type — Preventive / Corrective / Emergency (bar chart)
- Detailed work order table
- Filter by priority (slicer)

**Key Insight:** 73% of work orders are completed but 24 are overdue — these need immediate attention to prevent further machine downtime.

---

### Dashboard 4 — Quality & Defects
Identifies defect patterns by type, machine, and severity to support quality improvement.

**Visuals:**
- Total defects
- Total units affected
- Total rework cost
- Defects by type (bar chart)
- Defects by machine (bar chart)
- Severity breakdown — Critical / Major / Minor (bar chart)
- Smart narrative (auto-generated insight)
- Filter by production line (slicer)

**Key Insight:** Firmware errors are the most common defect type at 16% of all incidents. M001 (CNC Lathe A) has the highest defect count — consistent with its lower uptime shown in Dashboard 1.

---

## How to Run

### 1. Install dependencies
```bash
pip install pandas openpyxl mysql-connector-python
```

### 2. Run ETL pipeline
```bash
cd python_etl
python etl_mysql_v2.py
```

### 3. Export CSVs for Power BI
```bash
python export_csv.py
```

### 4. Open Power BI
- Open `PowerBI/AutomationAnalytics.pbix` in Power BI Desktop
- All 4 dashboards will load automatically

---

## Author
Pavani Burra
PerScholas — Data Analytics Program
