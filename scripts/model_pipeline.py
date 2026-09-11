# ==============================================================================
# PREDICTIVE LOGISTICS & THERMAL EXCURSION ANALYTICS IN COLD-CHAIN OPERATIONS
# Module 3: Gradient Boosting Machine Learning Risk Pipeline
# ==============================================================================

import os
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

def build_features(df):
    """
    Domain feature engineering for cold-chain logistics operations.
    """
    X = pd.DataFrame(index=df.index)
    
    # Direct thermal telemetry
    X["Reefer_Internal_Temp_C"] = df["Reefer_Internal_Temp_C"]
    X["Reefer_Max_Internal_Temp_C"] = df["Reefer_Max_Internal_Temp_C"]
    X["Thermal_Excursion_Minutes"] = df["Thermal_Excursion_Minutes"]
    X["Mean_Kinetic_Temp_C"] = df["Mean_Kinetic_Temp_C"]
    
    # Ambient climate differential
    X["Ambient_Peak_Temp_C"] = df["Ambient_Peak_Temp_C"]
    X["Thermal_Delta_C"] = df["Ambient_Peak_Temp_C"] - df["Reefer_Set_Point_C"]
    
    # Door breach intensity
    X["Door_Open_Total_Mins"] = df["Door_Open_Total_Mins"]
    X["Door_Open_Per_100KM"] = df["Door_Open_Total_Mins"] / (df["Route_Distance_KM"] / 100.0)
    
    # Mechanical & asset health
    X["Compressor_Run_Hours"] = df["Compressor_Run_Hours"]
    X["Compressor_Vibration_RMS"] = df["Compressor_Vibration_RMS"]
    X["Compressor_Stress_Index"] = df["Compressor_Run_Hours"] * df["Compressor_Vibration_RMS"]
    X["Insulation_Seal_Score"] = df["Insulation_Seal_Score"]
    
    # Cargo indicator (AB InBev Beer vs Pharma vs Dairy vs Frozen)
    cargo_encoded = pd.get_dummies(df["Cargo_Type"], prefix="Cargo", drop_first=False, dtype=float)
    X = pd.concat([X, cargo_encoded], axis=1)
    
    # Route indicator
    route_encoded = pd.get_dummies(df["Route_Type"], prefix="Route", drop_first=False, dtype=float)
    X = pd.concat([X, route_encoded], axis=1)
    
    return X

def train_and_evaluate_model():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    model_dir = base_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    raw_csv = data_dir / "cold_chain_telemetry.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"Telemetry data not found at {raw_csv}")
        
    df = pd.read_csv(raw_csv)
    print(f"[ML PIPELINE] Loaded raw dataset: {len(df)} records.")
    
    X = build_features(df)
    y = df["Spoilage_Flag"]
    
    feature_names = list(X.columns)
    
    # 80/20 Stratified Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    print(f"[ML PIPELINE] Training set: {len(X_train)} samples | Test set: {len(X_test)} samples")
    
    # Gradient Boosting Classifier
    gbm = GradientBoostingClassifier(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=4,
        subsample=0.85,
        random_state=42
    )
    
    gbm.fit(X_train, y_train)
    
    # Predictions & Probabilities
    y_pred = gbm.predict(X_test)
    y_prob = gbm.predict_proba(X_test)[:, 1]
    
    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    print("\n" + "="*50)
    print("      GRADIENT BOOSTING RISK MODEL EVALUATION")
    print("="*50)
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall:    {rec * 100:.2f}%")
    print(f"F1-Score:  {f1 * 100:.2f}%")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print("\nConfusion Matrix:")
    print(np.array(cm))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Safe Quality", "Degraded / Spoiled"]))
    
    # Feature Importances
    importances = dict(zip(feature_names, [round(float(v), 4) for v in gbm.feature_importances_]))
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    
    print("Top 8 Influential Risk Factors:")
    for k, v in list(sorted_importances.items())[:8]:
        print(f"  - {k:<30}: {v * 100:.2f}%")
        
    # Save Model & Metadata
    model_path = model_dir / "cold_chain_gbm_model.joblib"
    meta_path = model_dir / "model_metadata.json"
    
    joblib.dump(gbm, model_path)
    
    metadata = {
        "model_type": "GradientBoostingClassifier",
        "n_estimators": 120,
        "learning_rate": 0.08,
        "max_depth": 4,
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "confusion_matrix": cm
        },
        "feature_names": feature_names,
        "feature_importances": sorted_importances
    }
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\n[ML PIPELINE] Saved trained model to: {model_path}")
    print(f"[ML PIPELINE] Saved evaluation metadata to: {meta_path}")
    
    # --------------------------------------------------------------------------
    # Generate Batch Risk Scoring & Prescriptive Actions
    # --------------------------------------------------------------------------
    all_prob = gbm.predict_proba(X)[:, 1]
    df_scored = df.copy()
    df_scored["Predicted_Spoilage_Risk"] = np.round(all_prob, 4)
    
    def assign_risk_category(prob):
        if prob >= 0.70:
            return "Critical Risk (Immediate Action)"
        elif prob >= 0.35:
            return "Moderate Risk (Monitor)"
        else:
            return "Low Risk (Safe)"
            
    def assign_prescriptive_action(row):
        cargo = row["Cargo_Type"]
        risk = row["Predicted_Spoilage_Risk"]
        if risk >= 0.70:
            if "Beer" in cargo:
                return "CRITICAL: Inspect for Flavour Skunking & Colloidal Haze at Inbound Gate; Reroute to Priority Cross-Dock"
            elif "Vaccines" in cargo:
                return "CRITICAL: Quash for Biologics Potency & Cold-Chain Excursion Audit; Do Not Release to Cold-Room"
            else:
                return "CRITICAL: High Quality Degradation Detected; Expedite Destination QA Inspection"
        elif risk >= 0.35:
            return "WARNING: Schedule Reefer Compressor Inspection & Door Seal Re-calibration at Hub"
        else:
            return "OPTIMAL: Thermal Profile Compliant; Clear for Immediate Inbound Put-away"
            
    df_scored["Risk_Category"] = df_scored["Predicted_Spoilage_Risk"].apply(assign_risk_category)
    df_scored["Prescriptive_Action"] = df_scored.apply(assign_prescriptive_action, axis=1)
    
    final_csv = data_dir / "final_coldchain_analytics.csv"
    df_scored.to_csv(final_csv, index=False)
    print(f"[ML PIPELINE] Enriched analytical dataset saved to: {final_csv}")

if __name__ == "__main__":
    train_and_evaluate_model()
