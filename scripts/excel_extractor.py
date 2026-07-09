import openpyxl
import pandas as pd
import joblib
import psycopg2
from datetime import datetime

DB_NAME = 'credit_ops_db'
DB_USER = 'postgres'
DB_PASSWORD = 'your_actual_password_here'
DB_HOST = 'localhost'
DB_PORT = '5432'

def process_excel_underwriting(file_path, counterparty_id, entity_name):
    print(f'Opening Excel workbook at: {file_path}')
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb['Credit_analysis']
    
    sector = sheet['D5'].value  
    current_ratio = sheet['D10'].value  
    leverage_ratio = sheet['D11'].value
    altman_z_score = sheet['D13'].value
    exception_status = sheet['D15'].value
    
    if sector == 'Operational Sector' or current_ratio is None or isinstance(current_ratio, str):
        sector = sheet['D5'].value            
        current_ratio = float(sheet['D8'].value) if sheet['D8'].value else 1.05     
        leverage_ratio = float(sheet['D9'].value) if sheet['D9'].value else 0.69    
        altman_z_score = float(sheet['D10'].value) if sheet['D10'].value else 1.23   
        exception_status = sheet['D12'].value 

    print(f'Extracted Metrics -> Sector: {sector}, Current Ratio: {current_ratio}, Leverage: {leverage_ratio}, Z-Score: {altman_z_score}, Status: {exception_status}')
    
    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ABS_MODEL_PATH = os.path.join(CURRENT_SCRIPT_DIR, 'credit_rf_model.pkl')
    
    model = joblib.load(ABS_MODEL_PATH)
    features = pd.DataFrame([[altman_z_score, leverage_ratio, current_ratio]], 
                            columns=['altman_z_score', 'leverage_ratio', 'current_ratio'])
    
    raw_prob = model.predict_proba(features)
    default_prob = float(raw_prob) if hasattr(raw_prob, '__getitem__') and len(raw_prob.shape) >             1 else float(raw_prob)
    print(f'Calculated Machine Learning Default Probability: {default_prob:.4f}')
    
    if default_prob < 0.05: 
        risk_tier = 'GS-1'
    elif default_prob < 0.15: 
        risk_tier = 'GS-3'
    elif default_prob < 0.35: 
        risk_tier = 'GS-6'
    else: 
        risk_tier = 'GS-10'


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
        print(f'✅ Successfully processed and database-logged counterparty inside flat file storage at: {MOCK_DB_PATH}')

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)                  
    TARGET_EXCEL_PATH = os.path.join(ROOT_DIR, 'excel_templates', 'counterparty_underwriting_template.xlsx')
    process_excel_underwriting(TARGET_EXCEL_PATH, 'CP-7892', 'Apex Alpha Hedge Fund')
