-- ==============================================================================
-- PREDICTIVE LOGISTICS & THERMAL EXCURSION ANALYTICS IN COLD-CHAIN OPERATIONS
-- Production SQL Queries: Window Functions, CTEs, and Conditional Aggregations
-- ==============================================================================

-- 1. Route Haul & Thermal Risk Profiling

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
    

-- 2. LAG() Window Function: Step-by-Step Thermal Drift Rate (Delta T)

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
    

-- 3. Carrier Scorecard & OTIF Quality Compliance (CTE + DENSE_RANK)

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
    

-- 4. AB InBev Keg Beer / Premium Lager Corridor Vulnerability

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
    
