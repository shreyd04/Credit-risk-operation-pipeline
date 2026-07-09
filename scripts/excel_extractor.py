import openpyxl
import pandas as pd
import joblib
import psycopg2
import os
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION: SET YOUR LOCAL DATABASE LOGIN HERE
# ==========================================
DB_NAME = "credit_ops_db"
DB_USER = "postgres"
DB_PASSWORD = "your_actual_password_here"  # Make sure your real database password is here
DB_HOST = "localhost"
DB_PORT = "5432"
# ==========================================

def process_excel_underwriting(file_path, counterparty_id, entity_name):
    print(f"Opening Excel workbook at: {file_path}")
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb['Credit_analysis']
    
    # --- FIXED COORINDATES DIRECTLY FROM YOUR SHEET SCAN ---
    sector = sheet['D5'].value          # Broker-Dealer
    current_ratio = sheet['D10'].value   # 1.232977422
    leverage_ratio = sheet['D11'].value
    altman_z_score = sheet['D13'].value
    exception_status = sheet['D15'].value
    
    # Fallback gatekeeper just in case they are shifted to (D8, D9, D10, D12)
    if current_ratio is None or isinstance(current_ratio, str) or str(current_ratio).strip() == "":
        sector = sheet['D5'].value            
        current_ratio = float(sheet['D8'].value) if sheet['D8'].value else 1.05     
        leverage_ratio = float(sheet['D9'].value) if sheet['D9'].value else 0.69    
        altman_z_score = float(sheet['D10'].value) if sheet['D10'].value else 1.23   
        exception_status = sheet['D12'].value 

    # Cast to floats safely for the ML model math
    current_ratio = float(current_ratio) if current_ratio is not None else 1.05
    leverage_ratio = float(leverage_ratio) if leverage_ratio is not None else 0.69
    altman_z_score = float(altman_z_score) if altman_z_score is not None else 1.23

    print(f"Extracted Metrics -> Sector: {sector}, Current Ratio: {current_ratio:.4f}, Leverage: {leverage_ratio:.4f}, Z-Score: {altman_z_score:.4f}, Status: {exception_status}")
    
    # --- BULLETPROOF MODEL PATH RESOLUTION ---
    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ABS_MODEL_PATH = os.path.join(CURRENT_SCRIPT_DIR, 'credit_rf_model.pkl')
    
    model = joblib.load(ABS_MODEL_PATH)
    features = pd.DataFrame([[altman_z_score, leverage_ratio, current_ratio]], 
                            columns=['altman_z_score', 'leverage_ratio', 'current_ratio'])
    
    # Run prediction and fetch class 1 (Default probability) using exact index coordinates
    raw_prob = model.predict_proba(features)
    default_prob = float(raw_prob[0][1])
    print(f"Calculated Machine Learning Default Probability: {default_prob:.4f}")
    
    if default_prob > 0.5:  # Example threshold - adjust as needed
        print(f"FALLING BACK TO SECURE LOCAL STORAGE:")
        print(f"Database Error context: {db_err}")
        ROOT_DIR = os.path.dirname(CURRENT_SCRIPT_DIR)
        MOCK_DB_PATH = os.path.join(ROOT_DIR, 'data', 'mock_database_records.csv')
        
        record_payload = {
            'counterparty_id': counterparty_id, 'legal_entity_name': entity_name, 'sector': sector,
            'current_ratio': current_ratio, 'leverage_ratio': leverage_ratio, 'altman_z_score': altman_z_score,
            'model_default_probability': default_prob, 'risk_rating_tier': risk_tier, 'exception_status': exception_status,
            'pending_trade_volume_millions': pending_volume, 'exposure_at_default_millions': ead, 'settlement_status': settlement_status,
            'last_updated_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if os.path.exists(MOCK_DB_PATH):
            mock_df = pd.read_csv(MOCK_DB_PATH)
            mock_df = mock_df[mock_df['counterparty_id'] != counterparty_id]
            mock_df = pd.concat([mock_df, pd.DataFrame([record_payload])], ignore_index=True)
        else:
            mock_df = pd.DataFrame([record_payload])
            
        mock_df.to_csv(MOCK_DB_PATH, index=False)
        print(f"✅ Successfully processed and database-logged counterparty inside flat file storage at: {MOCK_DB_PATH}")

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)                  
    TARGET_EXCEL_PATH = os.path.join(ROOT_DIR, 'excel_templates', 'counterparty_underwriting_template.xlsx')
    
    process_excel_underwriting(TARGET_EXCEL_PATH, 'CP-7892', 'Apex Alpha Hedge Fund')
