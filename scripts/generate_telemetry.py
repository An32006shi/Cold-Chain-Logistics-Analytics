# ==============================================================================
# PREDICTIVE LOGISTICS & THERMAL EXCURSION ANALYTICS IN COLD-CHAIN OPERATIONS
# Module 1: Synthetic IoT Telemetry Generator
# Focus: Multi-Cargo Telemetry with AB InBev Keg Beer / Premium Lager & Pharma
# ==============================================================================

import os
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_cold_chain_datasets(n_shipments=1200, seed=42):
    np.random.seed(seed)
    
    # Resolve directory paths reliably
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    cargo_types = [
        "Pasteurized Keg Beer / Premium Lager",
        "Pharma Biologics & Vaccines",
        "Fresh Dairy & Perishables",
        "Frozen Foods & Confectionery"
    ]
    cargo_weights = [0.40, 0.25, 0.20, 0.15]  # 40% AB InBev Portfolio representation
    
    carriers = [
        "ColdFleet Express",
        "PolarTrans Logistics",
        "ArcticLogistics Global",
        "ThermoHaul Freight"
    ]
    
    origins = [
        "AB InBev Brewery - Bengaluru Hub",
        "Maharashtra Distribution Center",
        "Haryana Bottling Facility",
        "Gujarat BioPharma Park",
        "Punjab Regional Cold Hub"
    ]
    
    destinations = [
        "Goa Coastal Transit Hub",
        "Mumbai Urban Distribution Center",
        "Delhi NCR Mega Fulfillment",
        "Hyderabad Metro Depot",
        "Kolkata Eastern Terminal"
    ]
    
    shipments = []
    waypoints = []
    
    base_time = datetime(2026, 3, 1, 6, 0, 0)
    
    for i in range(n_shipments):
        shipment_id = f"SHP-{1000 + i}"
        tracking_code = f"AB-REEFER-{8000 + i}"
        cargo = np.random.choice(cargo_types, p=cargo_weights)
        carrier = np.random.choice(carriers)
        origin = np.random.choice(origins)
        dest = np.random.choice([d for d in destinations if d != origin])
        
        # Route distance and classification
        dist_km = int(np.random.triangular(80, 520, 1400))
        if dist_km < 300:
            route_type = "Short Haul"
        elif dist_km < 650:
            route_type = "Mid Haul"
        elif dist_km < 1000:
            route_type = "Long Haul"
        else:
            route_type = "Cross-Country"
            
        # Specific cargo physics & degradation thresholds
        if cargo == "Pasteurized Keg Beer / Premium Lager":
            target_temp = 3.5
            max_tolerable_temp = 8.0
            critical_temp = 15.0
            cargo_val = round(float(np.random.uniform(22000, 52000)), 2)
        elif cargo == "Pharma Biologics & Vaccines":
            target_temp = 4.0
            max_tolerable_temp = 8.0
            critical_temp = 12.0
            cargo_val = round(float(np.random.uniform(90000, 280000)), 2)
        elif cargo == "Fresh Dairy & Perishables":
            target_temp = 2.5
            max_tolerable_temp = 5.5
            critical_temp = 10.0
            cargo_val = round(float(np.random.uniform(12000, 34000)), 2)
        else:  # Frozen Foods
            target_temp = -20.0
            max_tolerable_temp = -14.0
            critical_temp = -8.0
            cargo_val = round(float(np.random.uniform(16000, 42000)), 2)
            
        # External Ambient Weather (Subcontinental corridor temperatures)
        ambient_avg = round(float(np.random.uniform(26.0, 42.0)), 2)
        ambient_peak = round(ambient_avg + float(np.random.uniform(2.5, 7.5)), 2)
        
        # Mechanical reefer status & wear indicators
        compressor_age = round(float(np.random.uniform(0.5, 8.5)), 1)
        est_transit_hours = dist_km / np.random.uniform(42, 65)
        compressor_hours = round(est_transit_hours * np.random.uniform(0.85, 1.25), 2)
        vibration_rms = round(float(np.random.uniform(0.18, 0.95)), 3)
        seal_score = round(float(np.random.uniform(62.0, 99.0)), 1)
        
        # Multi-drop door operations
        num_drops = int(np.random.choice([1, 2, 3, 5, 8, 12, 16], p=[0.25, 0.20, 0.20, 0.15, 0.10, 0.06, 0.04]))
        door_open_mins = int(num_drops * np.random.uniform(4.0, 14.0))
        
        # Internal thermal physics simulation
        heat_ingress = ((ambient_peak - 25.0) * 0.045) + ((door_open_mins / 30.0) * 0.38) + (vibration_rms * 1.6) + ((100.0 - seal_score) * 0.06)
        reefer_avg_temp = round(target_temp + np.random.normal(0.35, 0.55) + (heat_ingress * 0.38), 2)
        reefer_max_temp = round(reefer_avg_temp + np.random.uniform(1.2, 3.8) + (door_open_mins * 0.055), 2)
        
        # Thermal excursion duration (minutes above safe threshold)
        if reefer_max_temp > max_tolerable_temp:
            excursion_mins = int(np.random.exponential(scale=38) + (reefer_max_temp - max_tolerable_temp) * 18)
        else:
            excursion_mins = int(np.random.choice([0, 5, 10], p=[0.85, 0.10, 0.05]))
            
        # Mean Kinetic Temperature (MKT approximation)
        mkt_c = round(reefer_avg_temp + (reefer_max_temp - reefer_avg_temp) * 0.38, 2)
        
        # Domain degradation scoring
        # For Keg Beer / Lager: exposure to >8C over 90 mins or >15C flash excursion triggers oxidative staling & hazing
        degradation_score = 0.0
        if cargo == "Pasteurized Keg Beer / Premium Lager":
            if reefer_max_temp > critical_temp:
                degradation_score += 48.0
            if excursion_mins > 90:
                degradation_score += 38.0
            elif excursion_mins > 40:
                degradation_score += 18.0
            degradation_score += (heat_ingress * 3.6)
        else:
            if reefer_max_temp > critical_temp:
                degradation_score += 52.0
            if excursion_mins > 60:
                degradation_score += 36.0
            degradation_score += (heat_ingress * 3.2)
            
        degradation_score = float(np.clip(degradation_score + np.random.normal(0, 3.5), 0.0, 100.0))
        spoilage_flag = 1 if degradation_score >= 50.0 else 0
        
        shipments.append({
            "Shipment_ID": shipment_id,
            "Tracking_Code": tracking_code,
            "Carrier_Name": carrier,
            "Origin_Facility": origin,
            "Destination_Facility": dest,
            "Cargo_Type": cargo,
            "Cargo_Value_USD": cargo_val,
            "Route_Distance_KM": dist_km,
            "Route_Type": route_type,
            "Ambient_Avg_Temp_C": ambient_avg,
            "Ambient_Peak_Temp_C": ambient_peak,
            "Reefer_Set_Point_C": target_temp,
            "Reefer_Internal_Temp_C": reefer_avg_temp,
            "Reefer_Max_Internal_Temp_C": reefer_max_temp,
            "Compressor_Age_Years": compressor_age,
            "Compressor_Run_Hours": compressor_hours,
            "Compressor_Vibration_RMS": vibration_rms,
            "Door_Open_Events": num_drops,
            "Door_Open_Total_Mins": door_open_mins,
            "Insulation_Seal_Score": seal_score,
            "Thermal_Excursion_Minutes": excursion_mins,
            "Mean_Kinetic_Temp_C": mkt_c,
            "Quality_Degradation_Score": round(degradation_score, 2),
            "Spoilage_Flag": spoilage_flag
        })
        
        # Generate Waypoint telemetry for the first 350 shipments (for SQL window function queries)
        if i < 350:
            num_waypoints = int(np.random.choice([8, 10, 12]))
            curr_time = base_time + timedelta(hours=i * 2)
            curr_temp = target_temp + np.random.uniform(-0.4, 0.4)
            
            for wp in range(1, num_waypoints + 1):
                door_state = "OPEN" if (wp in [3, 7] and num_drops > 2) else "CLOSED"
                if door_state == "OPEN":
                    temp_delta = np.random.uniform(1.8, 4.4)
                    comp_power = 4.8
                else:
                    cooling_recovery = -1.2 if curr_temp > target_temp + 1.0 else np.random.uniform(-0.3, 0.3)
                    temp_delta = cooling_recovery
                    comp_power = 2.4
                    
                curr_temp = round(curr_temp + temp_delta, 2)
                speed = 0 if door_state == "OPEN" else int(np.random.uniform(45, 78))
                
                waypoints.append({
                    "Ping_ID": f"PING-{i * 100 + wp}",
                    "Shipment_ID": shipment_id,
                    "Waypoint_Seq": wp,
                    "Recorded_At": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Vehicle_Speed_KMH": speed,
                    "Instantaneous_Temp_C": curr_temp,
                    "Ambient_Temp_C": round(ambient_avg + np.random.uniform(-2.5, 3.0), 2),
                    "Compressor_Power_KW": comp_power,
                    "Door_State": door_state
                })
                curr_time += timedelta(minutes=int(np.random.uniform(35, 60)))
                
    df_shipments = pd.DataFrame(shipments)
    df_waypoints = pd.DataFrame(waypoints)
    
    shipments_csv = data_dir / "cold_chain_telemetry.csv"
    waypoints_csv = data_dir / "reefer_waypoint_telemetry.csv"
    
    df_shipments.to_csv(shipments_csv, index=False)
    df_waypoints.to_csv(waypoints_csv, index=False)
    
    print(f"[DATA GEN] Successfully created: {shipments_csv} ({len(df_shipments)} rows)")
    print(f"[DATA GEN] Successfully created: {waypoints_csv} ({len(df_waypoints)} waypoints for SQL LAG window functions)")
    print(f"[DATA GEN] Global Spoilage Rate: {df_shipments['Spoilage_Flag'].mean() * 100:.2f}%")
    beer_spoilage = df_shipments[df_shipments['Cargo_Type'] == 'Pasteurized Keg Beer / Premium Lager']['Spoilage_Flag'].mean() * 100
    print(f"[DATA GEN] AB InBev Beer / Lager Degradation Rate: {beer_spoilage:.2f}%")

if __name__ == "__main__":
    generate_cold_chain_datasets()
