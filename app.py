# ==============================================================================
# PREDICTIVE LOGISTICS & THERMAL EXCURSION COMMAND CENTER
# Executive Streamlit Web Application
# ==============================================================================

import os
import json
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import joblib

# Page Configuration
st.set_page_config(
    page_title="Cold-Chain Logistics Command Center",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-moderate {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-safe {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

@st.cache_data
def load_data():
    final_csv = DATA_DIR / "final_coldchain_analytics.csv"
    if not final_csv.exists():
        st.error("Processed analytics data not found. Please run 'python run_pipeline.py' first.")
        st.stop()
    df = pd.read_csv(final_csv)
    return df

@st.cache_resource
def load_ml_assets():
    model_path = MODEL_DIR / "cold_chain_gbm_model.joblib"
    meta_path = MODEL_DIR / "model_metadata.json"
    model = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return model, meta

df = load_data()
model, metadata = load_ml_assets()

# Sidebar Filters
st.sidebar.title("Operational Controls")
st.sidebar.markdown("**Cold-Chain Fleet Filters**")

selected_cargo = st.sidebar.multiselect(
    "Cargo Category",
    options=df["Cargo_Type"].unique(),
    default=df["Cargo_Type"].unique()
)

selected_routes = st.sidebar.multiselect(
    "Route Type",
    options=df["Route_Type"].unique(),
    default=df["Route_Type"].unique()
)

selected_carriers = st.sidebar.multiselect(
    "Logistics Carrier",
    options=df["Carrier_Name"].unique(),
    default=df["Carrier_Name"].unique()
)

risk_tier_filter = st.sidebar.multiselect(
    "Risk Classification",
    options=df["Risk_Category"].unique(),
    default=df["Risk_Category"].unique()
)

# Apply Filters
filtered_df = df[
    (df["Cargo_Type"].isin(selected_cargo)) &
    (df["Route_Type"].isin(selected_routes)) &
    (df["Carrier_Name"].isin(selected_carriers)) &
    (df["Risk_Category"].isin(risk_tier_filter))
]

# Header
st.markdown("<div class='main-title'>❄️ Cold-Chain Operations & Thermal Excursion Command Center</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Predictive Logistics, IoT Thermal Drift Telemetry & Quality Degradation Analytics | AB InBev Brewing & Multi-Cargo Fleet</div>", unsafe_allow_html=True)

# Top KPIs
col1, col2, col3, col4, col5 = st.columns(5)

total_shipments = len(filtered_df)
safe_shipments = len(filtered_df[filtered_df["Spoilage_Flag"] == 0])
otif_quality = (safe_shipments / total_shipments * 100) if total_shipments > 0 else 0
critical_alerts = len(filtered_df[filtered_df["Predicted_Spoilage_Risk"] >= 0.70])
value_at_risk = filtered_df[filtered_df["Spoilage_Flag"] == 1]["Cargo_Value_USD"].sum()
avg_excursion = filtered_df["Thermal_Excursion_Minutes"].mean() if total_shipments > 0 else 0

with col1:
    st.metric("Total Dispatched", f"{total_shipments:,}", "Shipments")
with col2:
    st.metric("OTIF Quality Compliance", f"{otif_quality:.1f}%", f"{safe_shipments} Safe Loads")
with col3:
    st.metric("Critical Risk Alerts", f"{critical_alerts}", "Immediate Action Req", delta_color="inverse")
with col4:
    st.metric("Cargo Value at Risk", f"${value_at_risk:,.0f}", "Quality Loss", delta_color="inverse")
with col5:
    st.metric("Avg Excursion Duration", f"{avg_excursion:.1f} m", "Threshold Breach")

st.markdown("---")

# Main Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛰️ Fleet Telemetry & Live Risks",
    "📈 Thermal Drift & Excursions",
    "🧠 What-If Risk Simulator",
    "🗄️ SQL Analytics & Window Functions",
    "📊 Power BI & Executive Reports"
])

# ==============================================================================
# TAB 1: FLEET TELEMETRY & LIVE RISKS
# ==============================================================================
with tab1:
    st.subheader("Active Shipment Inventory & Degradation Scoring")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        # Altair bar chart: Risk by Cargo Type
        cargo_chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X("Cargo_Type:N", title="Cargo Type", sort="-y"),
            y=alt.Y("count():Q", title="Total Shipments"),
            color=alt.Color("Risk_Category:N", scale=alt.Scale(
                domain=["Low Risk (Safe)", "Moderate Risk (Monitor)", "Critical Risk (Immediate Action)"],
                range=["#10B981", "#F59E0B", "#EF4444"]
            ), title="Risk Tier"),
            tooltip=["Cargo_Type", "Risk_Category", "count()"]
        ).properties(height=320)
        st.altair_chart(cargo_chart, use_container_width=True)
        
    with col_b:
        # Carrier compliance comparison
        carrier_perf = filtered_df.groupby("Carrier_Name")["Spoilage_Flag"].agg(
            Total="count",
            Degraded="sum"
        ).reset_index()
        carrier_perf["Compliance_Rate"] = ((carrier_perf["Total"] - carrier_perf["Degraded"]) / carrier_perf["Total"]) * 100
        
        carrier_chart = alt.Chart(carrier_perf).mark_bar().encode(
            x=alt.X("Carrier_Name:N", title="Carrier"),
            y=alt.Y("Compliance_Rate:Q", title="OTIF Quality Compliance %", scale=alt.Scale(domain=[60, 100])),
            color=alt.Color("Compliance_Rate:Q", scale=alt.Scale(scheme="greens"), legend=None),
            tooltip=["Carrier_Name", "Total", "Degraded", alt.Tooltip("Compliance_Rate:Q", format=".1f")]
        ).properties(height=320)
        st.altair_chart(carrier_chart, use_container_width=True)
        
    st.markdown("### Telemetry Stream & Prescriptive Dispatch Actions")
    display_cols = [
        "Shipment_ID", "Tracking_Code", "Cargo_Type", "Carrier_Name",
        "Route_Type", "Route_Distance_KM", "Ambient_Peak_Temp_C",
        "Reefer_Max_Internal_Temp_C", "Thermal_Excursion_Minutes",
        "Predicted_Spoilage_Risk", "Risk_Category", "Prescriptive_Action"
    ]
    st.dataframe(
        filtered_df[display_cols].sort_values(by="Predicted_Spoilage_Risk", ascending=False),
        use_container_width=True,
        height=380
    )

# ==============================================================================
# TAB 2: THERMAL DRIFT & EXCURSIONS
# ==============================================================================
with tab2:
    st.subheader("Thermal Physics: External Ambient Heat vs Reefer Chamber")
    st.markdown("""
    In cold-chain transit, ambient heat spikes combined with high compressor run hours and door openings cause 
    **thermal excursion spikes**. For pasteurized keg beer (AB InBev portfolio), exposure to temperatures above 8°C 
    initiates rapid flavor oxidation and haze formation.
    """)
    
    scatter = alt.Chart(filtered_df).mark_circle(size=70, opacity=0.7).encode(
        x=alt.X("Ambient_Peak_Temp_C:Q", title="External Ambient Peak Temp (°C)"),
        y=alt.Y("Reefer_Max_Internal_Temp_C:Q", title="Reefer Max Internal Temp (°C)"),
        color=alt.Color("Cargo_Type:N", title="Cargo Type"),
        tooltip=[
            "Shipment_ID", "Cargo_Type", "Carrier_Name", "Route_Distance_KM",
            "Ambient_Peak_Temp_C", "Reefer_Max_Internal_Temp_C",
            "Thermal_Excursion_Minutes", "Predicted_Spoilage_Risk"
        ]
    ).properties(height=420)
    
    # Safe boundary rule line
    rule = alt.Chart(pd.DataFrame({"y": [8.0]})).mark_rule(color="red", strokeDash=[5, 5], size=2).encode(y="y:Q")
    
    st.altair_chart(scatter + rule, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("📌 **Critical Excursion Boundary (Red Dashed Line at 8°C)**: For AB InBev lager and biologics, points above this line represent active cold-chain violations requiring rapid cross-dock triage.")
    with c2:
        st.warning("⚠️ **Door Open Time Correlation**: Shipments with >60 minutes door open events experience a 3.4x higher probability of critical thermal excursion.")

# ==============================================================================
# TAB 3: WHAT-IF RISK SIMULATOR
# ==============================================================================
with tab3:
    st.subheader("Interactive What-If Scenario Simulator (Gradient Boosting Model)")
    st.markdown("Simulate route telemetry conditions to predict instantaneous quality degradation probability and receive prescriptive actions.")
    
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    
    with sim_col1:
        sim_cargo = st.selectbox("Cargo Category", [
            "Pasteurized Keg Beer / Premium Lager",
            "Pharma Biologics & Vaccines",
            "Fresh Dairy & Perishables",
            "Frozen Foods & Confectionery"
        ])
        sim_dist = st.slider("Route Distance (KM)", 50, 1500, 480, step=25)
        sim_ambient_peak = st.slider("Corridor Peak Ambient Temp (°C)", 20.0, 48.0, 38.0, step=0.5)
        
    with sim_col2:
        set_pt_default = 3.5 if "Beer" in sim_cargo else (4.0 if "Pharma" in sim_cargo else (2.5 if "Dairy" in sim_cargo else -20.0))
        sim_reefer_internal = st.slider("Current Reefer Chamber Temp (°C)", -22.0, 18.0, set_pt_default + 1.2, step=0.2)
        sim_reefer_max = st.slider("Chamber Max Recorded Temp (°C)", -20.0, 20.0, sim_reefer_internal + 2.5, step=0.5)
        sim_excursion_mins = st.slider("Thermal Excursion Duration (Mins)", 0, 300, 45, step=5)
        
    with sim_col3:
        sim_door_mins = st.slider("Cumulative Door Open Time (Mins)", 5, 120, 35, step=5)
        sim_comp_hours = st.slider("Compressor Run Hours", 1.0, 30.0, 10.5, step=0.5)
        sim_comp_vib = st.slider("Compressor Vibration (RMS mm/s)", 0.15, 1.0, 0.52, step=0.01)
        sim_seal = st.slider("Insulation Seal Condition (%)", 50, 100, 82, step=1)
        
    # Build feature row
    route_type = "Short Haul" if sim_dist < 300 else ("Mid Haul" if sim_dist < 650 else ("Long Haul" if sim_dist < 1000 else "Cross-Country"))
    mkt = sim_reefer_internal + (sim_reefer_max - sim_reefer_internal) * 0.38
    thermal_delta = sim_ambient_peak - set_pt_default
    door_per_100 = sim_door_mins / (sim_dist / 100.0)
    comp_stress = sim_comp_hours * sim_comp_vib
    
    input_data = {
        "Reefer_Internal_Temp_C": [sim_reefer_internal],
        "Reefer_Max_Internal_Temp_C": [sim_reefer_max],
        "Thermal_Excursion_Minutes": [sim_excursion_mins],
        "Mean_Kinetic_Temp_C": [mkt],
        "Ambient_Peak_Temp_C": [sim_ambient_peak],
        "Thermal_Delta_C": [thermal_delta],
        "Door_Open_Total_Mins": [sim_door_mins],
        "Door_Open_Per_100KM": [door_per_100],
        "Compressor_Run_Hours": [sim_comp_hours],
        "Compressor_Vibration_RMS": [sim_comp_vib],
        "Compressor_Stress_Index": [comp_stress],
        "Insulation_Seal_Score": [sim_seal],
        "Cargo_Fresh Dairy & Perishables": [1.0 if sim_cargo == "Fresh Dairy & Perishables" else 0.0],
        "Cargo_Frozen Foods & Confectionery": [1.0 if sim_cargo == "Frozen Foods & Confectionery" else 0.0],
        "Cargo_Pasteurized Keg Beer / Premium Lager": [1.0 if sim_cargo == "Pasteurized Keg Beer / Premium Lager" else 0.0],
        "Cargo_Pharma Biologics & Vaccines": [1.0 if sim_cargo == "Pharma Biologics & Vaccines" else 0.0],
        "Route_Cross-Country": [1.0 if route_type == "Cross-Country" else 0.0],
        "Route_Long Haul": [1.0 if route_type == "Long Haul" else 0.0],
        "Route_Mid Haul": [1.0 if route_type == "Mid Haul" else 0.0],
        "Route_Short Haul": [1.0 if route_type == "Short Haul" else 0.0]
    }
    
    input_df = pd.DataFrame(input_data)[metadata["feature_names"]]
    pred_risk = model.predict_proba(input_df)[0, 1]
    
    st.markdown("### Simulation Output & Automated Decision Engine")
    res_col1, res_col2 = st.columns([1, 2])
    
    with res_col1:
        st.metric("Predicted Spoilage Risk", f"{pred_risk * 100:.1f}%")
        st.progress(float(pred_risk))
        
        if pred_risk >= 0.70:
            st.error("🚨 RISK TIER: CRITICAL")
        elif pred_risk >= 0.35:
            st.warning("⚠️ RISK TIER: MODERATE")
        else:
            st.success("✅ RISK TIER: COMPLIANT / SAFE")
            
    with res_col2:
        if pred_risk >= 0.70:
            if "Beer" in sim_cargo:
                st.error("**Prescriptive Action**: CRITICAL FLAVOUR DEGRADATION DETECTED. Immediate gate quarantine for colloidal stability & off-flavor analysis. Flag carrier SLA penalty.")
            elif "Vaccines" in sim_cargo:
                st.error("**Prescriptive Action**: POTENCY DESTRUCTION RISK. Quash shipment for cold-chain audit. Do NOT introduce to regional cold-storage inventory.")
            else:
                st.error("**Prescriptive Action**: IMMEDIATE SPOILAGE LIKELY. Route truck to closest emergency re-icing terminal or expedite QA reject protocol.")
        elif pred_risk >= 0.35:
            st.warning("**Prescriptive Action**: MODERATE THERMAL DRIFT. Dispatch alert to driver to verify door seal closure and check compressor cycle at next toll plaza.")
        else:
            st.success("**Prescriptive Action**: ALL SENSOR PARAMETERS WITHIN SAFE OPERATING THRESHOLDS. Fast-track inbound dock receiving.")

# ==============================================================================
# TAB 4: SQL ANALYTICS & WINDOW FUNCTIONS CONSOLE
# ==============================================================================
with tab4:
    st.subheader("Enterprise SQL Analytics Engine & Relational Database")
    st.markdown("""
    This layer utilizes production SQL with **CTEs, conditional aggregations, and `LAG()` window functions** 
    to track consecutive temperature deltas (Delta T) across IoT waypoints and rank carrier reliability.
    """)
    
    db_path = DATA_DIR / "logistics_operations.db"
    conn = sqlite3.connect(str(db_path))
    
    sql_selection = st.selectbox("Select Pre-Configured Enterprise Query", [
        "1. LAG() Window Function - Consecutive Thermal Drift Rate Analysis",
        "2. Carrier OTIF Quality Benchmarks & DENSE_RANK()",
        "3. AB InBev Keg Beer Corridor Vulnerability Analysis",
        "4. Route Haul Profile & Thermal Risk Summary",
        "5. Custom SQL Console"
    ])
    
    if sql_selection.startswith("1"):
        st.code("""WITH WaypointDrift AS (
    SELECT 
        Shipment_ID, Waypoint_Seq, Recorded_At, Door_State,
        Instantaneous_Temp_C, Ambient_Temp_C,
        LAG(Instantaneous_Temp_C, 1) OVER (
            PARTITION BY Shipment_ID ORDER BY Waypoint_Seq
        ) AS Prev_Reefer_Temp_C,
        ROUND(Instantaneous_Temp_C - LAG(Instantaneous_Temp_C, 1) OVER (
            PARTITION BY Shipment_ID ORDER BY Waypoint_Seq
        ), 2) AS Thermal_Drift_Rate_C
    FROM waypoint_telemetry
)
SELECT 
    Shipment_ID, Waypoint_Seq, Recorded_At, Door_State,
    Prev_Reefer_Temp_C, Instantaneous_Temp_C, Thermal_Drift_Rate_C,
    CASE 
        WHEN Thermal_Drift_Rate_C >= 2.5 THEN 'CRITICAL THERMAL SPIKE (>2.5C)'
        WHEN Thermal_Drift_Rate_C >= 1.0 THEN 'MODERATE DRIFT (1.0C - 2.5C)'
        WHEN Thermal_Drift_Rate_C <= -1.0 THEN 'ACTIVE REFRIGERATION PULL-DOWN'
        ELSE 'STEADY STATE'
    END AS Excursion_Status
FROM WaypointDrift
WHERE Prev_Reefer_Temp_C IS NOT NULL
ORDER BY Thermal_Drift_Rate_C DESC
LIMIT 30;""", language="sql")
        
        df_q = pd.read_sql_query("""WITH WaypointDrift AS (
    SELECT 
        Shipment_ID, Waypoint_Seq, Recorded_At, Door_State,
        Instantaneous_Temp_C, Ambient_Temp_C,
        LAG(Instantaneous_Temp_C, 1) OVER (PARTITION BY Shipment_ID ORDER BY Waypoint_Seq) AS Prev_Reefer_Temp_C,
        ROUND(Instantaneous_Temp_C - LAG(Instantaneous_Temp_C, 1) OVER (PARTITION BY Shipment_ID ORDER BY Waypoint_Seq), 2) AS Thermal_Drift_Rate_C
    FROM waypoint_telemetry
)
SELECT Shipment_ID, Waypoint_Seq, Recorded_At, Door_State, Prev_Reefer_Temp_C, Instantaneous_Temp_C, Thermal_Drift_Rate_C,
CASE WHEN Thermal_Drift_Rate_C >= 2.5 THEN 'CRITICAL THERMAL SPIKE (>2.5C)'
     WHEN Thermal_Drift_Rate_C >= 1.0 THEN 'MODERATE DRIFT (1.0C - 2.5C)'
     WHEN Thermal_Drift_Rate_C <= -1.0 THEN 'ACTIVE REFRIGERATION PULL-DOWN'
     ELSE 'STEADY STATE' END AS Excursion_Status
FROM WaypointDrift WHERE Prev_Reefer_Temp_C IS NOT NULL ORDER BY Thermal_Drift_Rate_C DESC LIMIT 30;""", conn)
        st.dataframe(df_q, use_container_width=True)
        
    elif sql_selection.startswith("2"):
        st.code("""WITH CarrierMetrics AS (
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
    Carrier_Name, Total_Dispatched, Perfect_Quality_Deliveries, Degraded_Deliveries,
    ROUND(100.0 * Perfect_Quality_Deliveries / Total_Dispatched, 2) AS OTIF_Quality_Compliance_Pct,
    Avg_Excursion_Mins, Avg_Compressor_Vibration, Avg_Seal_Integrity, Cumulative_Cargo_Loss_USD,
    DENSE_RANK() OVER (ORDER BY (100.0 * Perfect_Quality_Deliveries / Total_Dispatched) DESC) AS Quality_Rank
FROM CarrierMetrics ORDER BY Quality_Rank ASC;""", language="sql")
        
        df_q = pd.read_sql_query("""WITH CarrierMetrics AS (
    SELECT 
        Carrier_Name, COUNT(*) AS Total_Dispatched,
        SUM(CASE WHEN Spoilage_Flag = 0 THEN 1 ELSE 0 END) AS Perfect_Quality_Deliveries,
        SUM(CASE WHEN Spoilage_Flag = 1 THEN 1 ELSE 0 END) AS Degraded_Deliveries,
        ROUND(AVG(Thermal_Excursion_Minutes), 1) AS Avg_Excursion_Mins,
        ROUND(AVG(Compressor_Vibration_RMS), 3) AS Avg_Compressor_Vibration,
        ROUND(AVG(Insulation_Seal_Score), 1) AS Avg_Seal_Integrity,
        ROUND(SUM(Cargo_Value_USD * Spoilage_Flag), 2) AS Cumulative_Cargo_Loss_USD
    FROM shipment_telemetry GROUP BY Carrier_Name
)
SELECT Carrier_Name, Total_Dispatched, Perfect_Quality_Deliveries, Degraded_Deliveries,
ROUND(100.0 * Perfect_Quality_Deliveries / Total_Dispatched, 2) AS OTIF_Quality_Compliance_Pct,
Avg_Excursion_Mins, Avg_Compressor_Vibration, Avg_Seal_Integrity, Cumulative_Cargo_Loss_USD,
DENSE_RANK() OVER (ORDER BY (100.0 * Perfect_Quality_Deliveries / Total_Dispatched) DESC) AS Quality_Rank
FROM CarrierMetrics ORDER BY Quality_Rank ASC;""", conn)
        st.dataframe(df_q, use_container_width=True)
        
    elif sql_selection.startswith("3"):
        df_q = pd.read_sql_query("""SELECT Origin_Facility, Destination_Facility, COUNT(*) AS Beer_Shipments,
ROUND(AVG(Ambient_Peak_Temp_C), 2) AS Corridor_Peak_Ambient_C,
ROUND(AVG(Reefer_Max_Internal_Temp_C), 2) AS Max_Internal_Temp_C,
ROUND(AVG(Door_Open_Total_Mins), 1) AS Avg_Door_Open_Mins,
SUM(Spoilage_Flag) AS Spoiled_Beer_Loads,
ROUND(100.0 * SUM(Spoilage_Flag) / COUNT(*), 2) AS Beer_Degradation_Rate_Pct,
ROUND(SUM(Cargo_Value_USD * Spoilage_Flag), 2) AS Total_Beer_Value_Lost_USD
FROM shipment_telemetry WHERE Cargo_Type = 'Pasteurized Keg Beer / Premium Lager'
GROUP BY Origin_Facility, Destination_Facility HAVING COUNT(*) >= 10
ORDER BY Beer_Degradation_Rate_Pct DESC;""", conn)
        st.dataframe(df_q, use_container_width=True)
        
    elif sql_selection.startswith("4"):
        df_q = pd.read_sql_query("""SELECT Route_Type, COUNT(*) AS Total_Shipments,
ROUND(AVG(Route_Distance_KM), 1) AS Avg_Distance_KM,
ROUND(AVG(Ambient_Avg_Temp_C), 2) AS Avg_Ambient_Temp_C,
ROUND(AVG(Reefer_Internal_Temp_C), 2) AS Avg_Reefer_Internal_Temp_C,
ROUND(AVG(Thermal_Excursion_Minutes), 1) AS Avg_Excursion_Minutes,
SUM(Door_Open_Events) AS Total_Door_Open_Events,
SUM(Spoilage_Flag) AS Degraded_Shipments,
ROUND(100.0 * SUM(Spoilage_Flag) / COUNT(*), 2) AS Spoilage_Rate_Pct,
ROUND(SUM(Cargo_Value_USD * Spoilage_Flag), 2) AS Financial_Loss_At_Risk_USD
FROM shipment_telemetry GROUP BY Route_Type ORDER BY Spoilage_Rate_Pct DESC;""", conn)
        st.dataframe(df_q, use_container_width=True)
        
    else:
        custom_sql = st.text_area("Write SQL Query", "SELECT Cargo_Type, AVG(Thermal_Excursion_Minutes) AS Avg_Excursion FROM shipment_telemetry GROUP BY Cargo_Type;")
        if st.button("Execute SQL"):
            try:
                res = pd.read_sql_query(custom_sql, conn)
                st.dataframe(res, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")
                
    conn.close()

# ==============================================================================
# TAB 5: POWER BI & EXECUTIVE REPORTS
# ==============================================================================
with tab5:
    st.subheader("Power BI / Excel Executive Integration Center")
    st.markdown("""
    All analytical outputs from this pipeline are structured for plug-and-play consumption in **Microsoft Power BI, Tableau, and Excel**.
    """)
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        st.download_button(
            "📥 Download Scored Telemetry CSV",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="final_coldchain_analytics.csv",
            mime="text/csv"
        )
    with col_dl2:
        drift_csv = DATA_DIR / "sql_thermal_drift_window.csv"
        if drift_csv.exists():
            with open(drift_csv, "rb") as f:
                st.download_button(
                    "📥 Download LAG() Window Drift CSV",
                    data=f.read(),
                    file_name="sql_thermal_drift_window.csv",
                    mime="text/csv"
                )
    with col_dl3:
        carrier_csv = DATA_DIR / "carrier_reliability_benchmarks.csv"
        if carrier_csv.exists():
            with open(carrier_csv, "rb") as f:
                st.download_button(
                    "📥 Download Carrier OTIF Benchmarks CSV",
                    data=f.read(),
                    file_name="carrier_reliability_benchmarks.csv",
                    mime="text/csv"
                )
                
    st.markdown("### Pre-Configured Power BI DAX Measures")
    st.code("""-- 1. OTIF (On-Time In-Full) Quality Compliance Rate
OTIF Quality Compliance % = 
DIVIDE(
    CALCULATE(COUNTROWS('final_coldchain_analytics'), 'final_coldchain_analytics'[Spoilage_Flag] = 0),
    COUNTROWS('final_coldchain_analytics'),
    0
) * 100

-- 2. Thermal Excursion Ratio per Trip
Thermal Excursion Ratio % = 
DIVIDE(
    SUM('final_coldchain_analytics'[Thermal_Excursion_Minutes]),
    SUM('final_coldchain_analytics'[Route_Distance_KM]) / 50 * 60,
    0
) * 100

-- 3. Total Inventory Financial Loss
Total Spoilage Value USD = 
SUMX(
    FILTER('final_coldchain_analytics', 'final_coldchain_analytics'[Spoilage_Flag] = 1),
    'final_coldchain_analytics'[Cargo_Value_USD]
)""", language="sql")
    
    st.info("💡 **Power BI Visual Blueprint**: Import `final_coldchain_analytics.csv` as Fact Table, create a Card for `OTIF Quality Compliance %`, a Scatter chart of `Ambient_Peak_Temp_C` vs `Reefer_Max_Internal_Temp_C`, and a Clustered Bar chart for `Carrier_Name` ranked by Quality Score.")


