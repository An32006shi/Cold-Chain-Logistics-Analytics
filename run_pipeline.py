# ==============================================================================
# PREDICTIVE LOGISTICS & THERMAL EXCURSION ANALYTICS IN COLD-CHAIN OPERATIONS
# Master Pipeline Orchestrator (One-Click Runner)
# ==============================================================================

import sys
import time
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def print_banner():
    banner = """
================================================================================
 [COLD-CHAIN ANALYTICS] PREDICTIVE LOGISTICS & THERMAL EXCURSION PIPELINE
 Industry Vertical: AB InBev Brewing, Cold-Chain Logistics & Life Sciences
================================================================================
"""
    print(banner)

def run_step(step_name, script_path):
    print(f"\n>> [PIPELINE EXECUTION] Starting: {step_name}...")
    start = time.time()
    env = dict(sys.orig_argv[0] and {})
    result = subprocess.run([sys.executable, str(script_path)])
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"[ERROR] {step_name} failed with return code {result.returncode}!")
        sys.exit(1)
    print(f"[SUCCESS] {step_name} completed in {elapsed:.2f} seconds.")

def main():
    print_banner()
    base_dir = Path(__file__).resolve().parent
    scripts_dir = base_dir / "scripts"
    
    total_start = time.time()
    
    # Step 1: Telemetry Generation
    run_step("Step 1: IoT Cold-Chain Telemetry Generation", scripts_dir / "generate_telemetry.py")
    
    # Step 2: SQL Analytics Engine (Window Functions & CTEs)
    run_step("Step 2: SQLite Relational Ingestion & Window Functions", scripts_dir / "sql_analytics.py")
    
    # Step 3: Gradient Boosting Risk Pipeline
    run_step("Step 3: Feature Engineering & Gradient Boosting Model Training", scripts_dir / "model_pipeline.py")
    
    total_elapsed = time.time() - total_start
    print("\n" + "="*80)
    print(f"[COMPLETE] FULL PIPELINE EXECUTED SUCCESSFULLY in {total_elapsed:.2f} seconds!")
    print("="*80)
    print("Generated Artifacts:")
    print("  * data/cold_chain_telemetry.csv          - 1,200 raw shipment records")
    print("  * data/reefer_waypoint_telemetry.csv     - 3,400+ waypoint readings for SQL window functions")
    print("  * data/logistics_operations.db           - SQLite production relational DB")
    print("  * data/final_coldchain_analytics.csv     - Scored dataset with predicted spoilage risks")
    print("  * data/sql_thermal_drift_window.csv      - LAG() window function thermal drift analysis")
    print("  * data/carrier_reliability_benchmarks.csv- Carrier OTIF compliance scorecards")
    print("  * models/cold_chain_gbm_model.joblib     - Trained Gradient Boosting ML model")
    print("  * models/model_metadata.json             - Hyperparameters & ROC-AUC evaluation metrics")
    print("\nTo launch the Executive Command Center dashboard, execute:")
    print("  streamlit run app.py")
    print("="*80)

if __name__ == "__main__":
    main()
