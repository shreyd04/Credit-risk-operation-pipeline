import openpyxl
import pandas as pd
import joblib
import psycopg2
from datetime import datetime

def process_excel_underwriting(file_path, counterparty_id, entity_name):
    # Load Excel Workbook (data_only=True evaluates the values behind formulas)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb['Credit_Analysis']
    
    # Read values from specific cells where your Excel formulas live
    # Adjust cell coordinates based on your exact sheet design
    current_ratio = sheet['B5'].value  
    leverage_ratio = sheet['B6'].value
    altman_z_score = sheet['B7'].value
    exception_status = sheet['B8'].value
    sector = sheet['B2'].value
    
    # Load Trained ML model to predict precise default probability
    model = joblib.load('scripts/credit_rf_model.pkl')
    features = pd.DataFrame([[altman_z_score, leverage_ratio, current_ratio]], 
                            columns=['altman_z_score', 'leverage_ratio', 'current_ratio'])
    default_prob = model.predict_proba(features)[0][1] # Probability of Class 1 (Default)
    
    # Map default probability to an institutional credit tier
    if default_prob < 0.05: risk_tier = "GS-1"
    elif default_prob < 0.15: risk_tier = "GS-3"
    elif default_prob < 0.35: risk_tier = "GS-6"
    else: risk_tier = "GS-10"
    
    # Calculate Exposure Metrics
    pending_volume = 45.5 # Hardcoded example: $45.5M pending stock trade
    ead = pending_volume * leverage_ratio # Exposure formula variant
    
    settlement_status = "APPROVED"
    if exception_status == "CRITICAL EXCEPTION" or risk_tier == "GS-10":
        settlement_status = "HOLD_FOR_COLLATERAL"

    # Connect and Write to PostgreSQL Database
    conn = psycopg2.connect(
        dbname="your_db", user="your_user", password="your_password", host="localhost", port="5432"
    )
    cursor = conn.cursor()
    
    # Upsert into risk profiles
    cursor.execute("""
        INSERT INTO counterparty_risk_profiles 
        (counterparty_id, legal_entity_name, sector, current_ratio, leverage_ratio, altman_z_score, model_default_probability, risk_rating_tier, exception_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (counterparty_id) DO UPDATE SET 
        current_ratio=EXCLUDED.current_ratio, leverage_ratio=EXCLUDED.leverage_ratio, altman_z_score=EXCLUDED.altman_z_score,
        model_default_probability=EXCLUDED.model_default_probability, risk_rating_tier=EXCLUDED.risk_rating_tier, exception_status=EXCLUDED.exception_status;
    """, (counterparty_id, entity_name, sector, current_ratio, leverage_ratio, altman_z_score, float(default_prob), risk_tier, exception_status))
    
    # Insert transaction logs
    cursor.execute("""
        INSERT INTO operational_settlement_logs (counterparty_id, pending_trade_volume_millions, exposure_at_default_millions, settlement_status)
        VALUES (%s, %s, %s, %s);
    """, (counterparty_id, pending_volume, ead, settlement_status))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Successfully processed and database-logged counterparty: {entity_name}")

if __name__ == "__main__":
    # Test script execution
    process_excel_underwriting('excel_templates/counterparty_underwriting_template.xlsx', 'CP-7892', 'Apex Alpha Hedge Fund')
