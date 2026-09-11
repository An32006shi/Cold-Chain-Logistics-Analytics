# ==============================================================================
# PREDICTIVE LOGISTICS & THERMAL EXCURSION ANALYTICS IN COLD-CHAIN OPERATIONS
# Module 2: Enterprise SQL Analytics Engine (Window Functions & CTEs)
# ==============================================================================

import os
import sqlite3
from pathlib import Path
import pandas as pd

def run_sql_analytics():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    db_path = data_dir / "logistics_operations.db"
    
    shipments_csv = data_dir / "cold_chain_telemetry.csv"
    waypoints_csv = data_dir / "reefer_waypoint_telemetry.csv"
    
    if not shipments_csv.exists() or not waypoints_csv.exists():
        raise FileNotFoundError("Raw telemetry files missing. Run generate_telemetry.py first.")
        
    df_shipments = pd.read_csv(shipments_csv)
    df_waypoints = pd.read_csv(waypoints_csv)
    
    conn = sqlite3.connect(str(db_path))
    
    # Ingest into SQLite tables
    df_shipments.to_sql("shipment_telemetry", conn, if_exists="replace", index=False)
    df_waypoints.to_sql("waypoint_telemetry", conn, if_exists="replace", index=False)
    print(f"[SQL ENGINE] Ingested datasets into SQLite: {db_path}")
    
    # --------------------------------------------------------------------------
    # SQL Query 1: Route Haul & Thermal Risk Profiling (Conditional Aggregations)
    # --------------------------------------------------------------------------
    sql_route_profile = """
    SELECT 
        Route_Type,
        COUNT(*) AS Total_Shipments,
        ROUND(AVG(Route_Distance_KM), 1) AS Avg_Distance_KM,
        ROUND(AVG(Ambient_Avg_Temp_C), 2) AS Avg_Ambient_Temp_C,
        ROUND(AVG(Reefer_Internal_Temp_C), 2) AS Avg_Reefer_Internal_Temp_C,
        ROUND(AVG(Thermal_Excursion_Minutes), 1) AS Avg_Excursion_Minutes,
        SUM(Door_Open_Events) AS Total_Door_Open_Events,
        SUM(Spoilage_Flag) AS Degraded_Shipments,
        ROUND(100.0 * SUM(Spoilage_Flag) / COUNT(*), 2) AS Spoilage_Rate_Pct,
        ROUND(SUM(Cargo_Value_USD * Spoilage_Flag), 2) AS Financial_Loss_At_Risk_USD
    FROM shipment_telemetry
    GROUP BY Route_Type
    ORDER BY Spoilage_Rate_Pct DESC;
    """
    df_route_summary = pd.read_sql_query(sql_route_profile, conn)
    df_route_summary.to_csv(data_dir / "sql_route_risk_summary.csv", index=False)
    print("\n=== QUERY 1: ROUTE HAUL RISK PROFILING ===")
    print(df_route_summary.to_string(index=False))
    
    # --------------------------------------------------------------------------
    # SQL Query 2: LAG() Window Function - Consecutive Thermal Drift Rate Analysis
    # Calculates consecutive waypoint temp delta (Delta T) to flag thermal spikes
    # --------------------------------------------------------------------------
    sql_thermal_drift = """
    WITH WaypointDrift AS (
        SELECT 
            Shipment_ID,
            Waypoint_Seq,
            Recorded_At,
            Door_State,
            Instantaneous_Temp_C,
            Ambient_Temp_C,
            LAG(Instantaneous_Temp_C, 1) OVER (
                PARTITION BY Shipment_ID 
                ORDER BY Waypoint_Seq
            ) AS Prev_Reefer_Temp_C,
            ROUND(Instantaneous_Temp_C - LAG(Instantaneous_Temp_C, 1) OVER (
                PARTITION BY Shipment_ID 
                ORDER BY Waypoint_Seq
            ), 2) AS Thermal_Drift_Rate_C
        FROM waypoint_telemetry
    )
    SELECT 
        Shipment_ID,
        Waypoint_Seq,
        Recorded_At,
        Door_State,
        Prev_Reefer_Temp_C,
        Instantaneous_Temp_C,
        Thermal_Drift_Rate_C,
        CASE 
            WHEN Thermal_Drift_Rate_C >= 2.5 THEN 'CRITICAL THERMAL SPIKE (>2.5C)'
            WHEN Thermal_Drift_Rate_C >= 1.0 THEN 'MODERATE DRIFT (1.0C - 2.5C)'
            WHEN Thermal_Drift_Rate_C <= -1.0 THEN 'ACTIVE REFRIGERATION PULL-DOWN'
            ELSE 'STEADY STATE'
        END AS Excursion_Status
    FROM WaypointDrift
    WHERE Prev_Reefer_Temp_C IS NOT NULL
    ORDER BY Thermal_Drift_Rate_C DESC
    LIMIT 25;
    """
    df_drift_summary = pd.read_sql_query(sql_thermal_drift, conn)
    df_drift_summary.to_csv(data_dir / "sql_thermal_drift_window.csv", index=False)
    print("\n=== QUERY 2: LAG() WINDOW FUNCTION - TOP THERMAL DRIFT SPIKES ===")
    print(df_drift_summary.head(10).to_string(index=False))
    
    # --------------------------------------------------------------------------
    # SQL Query 3: Carrier Scorecard & OTIF Quality Compliance (CTE + RANK())
    # --------------------------------------------------------------------------
    sql_carrier_benchmark = """
    WITH CarrierMetrics AS (
        SELECT 
            Carrier_Name,
            COUNT(*) AS Total_Dispatched,
            SUM(CASE WHEN Spoilage_Flag = 0 THEN 1 ELSE 0 END) AS Perfect_Quality_Deliveries,
            SUM(CASE WHEN Spoilage_Flag = 1 THEN 1 ELSE 0 END) AS Degraded_Deliveries,
            ROUND(AVG(Thermal_Excursion_Minutes), 1) AS Avg_Excursion_Mins,
            ROUND(AVG(Compressor_Vibration_RMS), 3) AS Avg_Compressor_Vibration,
            ROUND(AVG(Insulation_Seal_Score), 1) AS Avg_Seal_Integrity,
            ROUND(SUM(Cargo_Value_USD * Spoilage_Flag), 2) AS Cumulative_Cargo_Loss_USD
        FROM shipment_telemetry
        GROUP BY Carrier_Name
    )
    SELECT 
        Carrier_Name,
        Total_Dispatched,
        Perfect_Quality_Deliveries,
        Degraded_Deliveries,
        ROUND(100.0 * Perfect_Quality_Deliveries / Total_Dispatched, 2) AS OTIF_Quality_Compliance_Pct,
        Avg_Excursion_Mins,
        Avg_Compressor_Vibration,
        Avg_Seal_Integrity,
        Cumulative_Cargo_Loss_USD,
        DENSE_RANK() OVER (
            ORDER BY (100.0 * Perfect_Quality_Deliveries / Total_Dispatched) DESC
        ) AS Quality_Rank
    FROM CarrierMetrics
    ORDER BY Quality_Rank ASC;
    """
    df_carrier_benchmark = pd.read_sql_query(sql_carrier_benchmark, conn)
    df_carrier_benchmark.to_csv(data_dir / "carrier_reliability_benchmarks.csv", index=False)
    print("\n=== QUERY 3: CARRIER OTIF QUALITY BENCHMARKS & DENSE_RANK() ===")
    print(df_carrier_benchmark.to_string(index=False))
    
    # --------------------------------------------------------------------------
    # SQL Query 4: AB InBev Keg Beer / Premium Lager Corridor Vulnerability
    # --------------------------------------------------------------------------
    sql_beer_corridor = """
    SELECT 
        Origin_Facility,
        Destination_Facility,
        COUNT(*) AS Beer_Shipments,
        ROUND(AVG(Ambient_Peak_Temp_C), 2) AS Corridor_Peak_Ambient_C,
        ROUND(AVG(Reefer_Max_Internal_Temp_C), 2) AS Max_Internal_Temp_C,
        ROUND(AVG(Door_Open_Total_Mins), 1) AS Avg_Door_Open_Mins,
        SUM(Spoilage_Flag) AS Spoiled_Beer_Loads,
        ROUND(100.0 * SUM(Spoilage_Flag) / COUNT(*), 2) AS Beer_Degradation_Rate_Pct,
        ROUND(SUM(Cargo_Value_USD * Spoilage_Flag), 2) AS Total_Beer_Value_Lost_USD
    FROM shipment_telemetry
    WHERE Cargo_Type = 'Pasteurized Keg Beer / Premium Lager'
    GROUP BY Origin_Facility, Destination_Facility
    HAVING COUNT(*) >= 10
    ORDER BY Beer_Degradation_Rate_Pct DESC;
    """
    df_beer_corridor = pd.read_sql_query(sql_beer_corridor, conn)
    df_beer_corridor.to_csv(data_dir / "sql_beer_corridor_analysis.csv", index=False)
    print("\n=== QUERY 4: AB INBEV BEER LOGISTICS CORRIDOR ANALYSIS ===")
    print(df_beer_corridor.head(8).to_string(index=False))
    
    # Save formatted pure SQL script
    pure_sql = f"""-- ==============================================================================
-- PREDICTIVE LOGISTICS & THERMAL EXCURSION ANALYTICS IN COLD-CHAIN OPERATIONS
-- Production SQL Queries: Window Functions, CTEs, and Conditional Aggregations
-- ==============================================================================

-- 1. Route Haul & Thermal Risk Profiling
{sql_route_profile}

-- 2. LAG() Window Function: Step-by-Step Thermal Drift Rate (Delta T)
{sql_thermal_drift}

-- 3. Carrier Scorecard & OTIF Quality Compliance (CTE + DENSE_RANK)
{sql_carrier_benchmark}

-- 4. AB InBev Keg Beer / Premium Lager Corridor Vulnerability
{sql_beer_corridor}
"""
    with open(data_dir / "queries.sql", "w", encoding="utf-8") as f:
        f.write(pure_sql)
        
    conn.close()
    print(f"\n[SQL ENGINE] Generated queries.sql and analytical summary CSVs successfully.")

if __name__ == "__main__":
    run_sql_analytics()
