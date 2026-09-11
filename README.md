# Predictive Logistics & Thermal Excursion Analytics in Cold-Chain Operations

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-SQLite%20%7C%20Window%20Functions-orange.svg)](https://sqlite.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Gradient%20Boosting-green.svg)](https://scikit-learn.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Executive%20App-red.svg)](https://streamlit.io/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Executive%20DAX-yellow.svg)](https://powerbi.microsoft.com/)

> **Enterprise Cold-Chain Operations Intelligence**: An end-to-end analytics platform designed for FMCG supply chain leaders (such as **AB InBev Brewing Operations**), life sciences, and temperature-controlled freight. Integrates IoT sensor telemetry ingestion, SQL window functions, Gradient Boosting machine learning, and an interactive executive command center.

---

## 📌 Executive Narrative & Industry Impact

In temperature-controlled logistics, preserving cargo integrity during long-haul highway transit is a mission-critical operational challenge:
- **Brewery Cold-Chain (AB InBev Portfolio)**: Draft keg beer and premium lagers (Budweiser, Corona, Stella Artois) are biologically active and chemically fragile. Exposure to temperatures $>8^\circ\text{C}$ initiates accelerated oxidative staling (cardboard off-flavor via *trans-2-nonenal*) and colloidal hazing. Flash spikes above $>15^\circ\text{C}$ ruin carbonation retention and batch stability.
- **Biologics & Life Sciences**: Vaccines and protein biotherapeutics undergo permanent denaturation outside strict 2°C–8°C boundaries.
- **Root Cause Factors**: External ambient heat corridors, aging reefer compressors with high mechanical vibration, damaged door seals, and multi-drop door opening events.

This platform bridges the gap between raw IoT telematics and executive dispatch decisions:
1. Ingests and processes **1,200 multi-modal shipments** and **3,400+ waypoint telemetry pings** in SQLite.
2. Applies **`LAG()` window functions** to measure instantaneous thermal drift rates ($\Delta T / \Delta t$) across routes.
3. Deploys a **Gradient Boosting Classifier (ROC-AUC: 0.9767)** predicting quality degradation risk 6+ hours before gate arrival.
4. Provides an interactive **Streamlit Command Center** with real-time What-If scenario simulations and pre-configured **Power BI DAX measures**.

---

## 🏛️ System Architecture

```
                                 [ IoT Telematics Stream ]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
          [ cold_chain_telemetry.csv ]               [ reefer_waypoint_telemetry.csv ]
         (1,200 Shipment Summaries)                  (3,400+ Multi-Stop Waypoint Pings)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             ▼
                             [ SQLite Operational Database ]
                               (logistics_operations.db)
                                             │
             ┌───────────────────────────────┴──────────────────────────────┐
             ▼                                                              ▼
    [ Enterprise SQL Engine ]                                   [ Machine Learning Pipeline ]
  - LAG() Window Functions (ΔT Drift)                         - Mean Kinetic Temp (MKT)
  - Carrier OTIF Benchmarking (DENSE_RANK)                    - Compressor Stress Index
  - Route Haul Aggregations                                   - Gradient Boosting Classifier
  - Beer Logistics Corridor Vulnerability                     - 0.9767 ROC-AUC | 93.3% Accuracy
             │                                                              │
             └───────────────────────────────┬──────────────────────────────┘
                                             ▼
                            [ final_coldchain_analytics.csv ]
                           (Scored Telemetry + Prescriptions)
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
        [ Streamlit Executive Command Center ]       [ Power BI / Tableau Dashboards ]
        - Live KPI Cards (OTIF %, Value at Risk)     - Fact & Dimension Data Model
        - Thermal Drift Scatter & Excursions         - Production DAX Measures
        - Interactive What-If Risk Simulator         - Executive KPI Canvas
        - Embedded Live SQL Query Console            - Root-Cause Decomposition
```

---

## 📁 Repository Structure

```
cold_chain_logistics_analytics/
│
├── data/
│   ├── cold_chain_telemetry.csv         # Raw synthetic IoT telemetry (1,200 shipments)
│   ├── reefer_waypoint_telemetry.csv    # Time-series telemetry (3,400+ pings for SQL windowing)
│   ├── logistics_operations.db          # SQLite relational database
│   ├── final_coldchain_analytics.csv    # Scored dataset with predicted risks & prescriptions
│   ├── sql_thermal_drift_window.csv     # LAG() window function thermal drift output
│   ├── carrier_reliability_benchmarks.csv# Carrier OTIF scorecards & DENSE_RANK() output
│   ├── sql_route_risk_summary.csv       # Route haul risk profiling
│   ├── sql_beer_corridor_analysis.csv   # AB InBev beer route vulnerability analysis
│   └── queries.sql                      # Production formatted SQL script
│
├── models/
│   ├── cold_chain_gbm_model.joblib      # Trained Gradient Boosting model artifact
│   └── model_metadata.json              # Hyperparameters, evaluation metrics & feature importances
│
├── scripts/
│   ├── generate_telemetry.py            # IoT telemetry generator with AB InBev beer profile
│   ├── sql_analytics.py                 # SQLite database setup & LAG/LEAD window analytical queries
│   └── model_pipeline.py                # ML feature engineering, training & risk scoring
│
├── app.py                               # Interactive Streamlit Executive Command Center
├── run_pipeline.py                      # One-click end-to-end pipeline execution runner
├── POWER_BI_DASHBOARD_GUIDE.md          # Step-by-step Power BI DAX & visual layout guide
├── INTERVIEW_TALKING_POINTS.md          # AB InBev/FMCG interview narrative, resume bullets & FAQs
├── requirements.txt                     # Project dependencies
└── README.md                            # Comprehensive documentation
```

---

## 🚀 Quick Start & How to Run

### 1. Installation
Clone the repository and install required packages:
```bash
git clone https://github.com/An32006shi/Cold-Chain-Logistics-Analytics.git
cd cold-chain-logistics-analytics
pip install -r requirements.txt
```

### 2. Run the Complete Data & ML Pipeline (One-Click)
Execute the master runner to generate synthetic data, ingest into SQLite, execute window queries, and train the ML model:
```bash
python run_pipeline.py
```

### 3. Launch the Executive Command Center
Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🗄️ SQL Analytics Highlights

### Query: Consecutive Thermal Drift Rate with `LAG()`
Measures temperature variation between adjacent waypoint pings to identify sudden door-open thermal surges:
```sql
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
```

---

## 🧠 Machine Learning Model Performance

- **Algorithm**: `GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, max_depth=4)`
- **Evaluation Metrics**:
  - **Accuracy**: `93.33%`
  - **Precision**: `83.33%`
  - **Recall**: `79.55%`
  - **F1-Score**: `81.40%`
  - **ROC-AUC**: `0.9767`

### Key Feature Importances:
1. `Thermal_Excursion_Minutes`: **42.32%**
2. `Reefer_Max_Internal_Temp_C`: **15.74%**
3. `Door_Open_Total_Mins`: **10.73%**
4. `Insulation_Seal_Score`: **10.05%**
5. `Door_Open_Per_100KM`: **3.03%**
6. `Mean_Kinetic_Temp_C`: **2.99%**
7. `Compressor_Vibration_RMS`: **2.85%**

---




