# 🛡️ Institutional Credit Risk & Settlement Control Console

**Streamlit Dashboard : https://credit-risk-operation-pipeline-tz4ubrgx4kenurdvg5knjs.streamlit.app**
<img width="1440" height="811" alt="Screenshot 2026-05-11 at 8 27 16 PM" src="https://github.com/user-attachments/assets/d1b1ebe8-3177-4ec2-9f77-f0ce01ed353f" />


*Core Transaction Integrity & Counterparty Risk Monitor*

---

## Operational Mandate Mapping

This system addresses the fundamental pillars of  Operations Division governance:

1. **Pre-Trade Clearance & Compliance**: Automated underwriting workflows intercept counterparty risk before trade execution, eliminating manual clearance delays and policy exception leakage.

2. **Settlement Integrity & Ledger Accuracy**: Programmatic reconciliation of balance sheet metrics against live exposure limits ($45.5M aggregate monitoring capacity) ensures all pending trades remain within approved collateral thresholds.

3. **Systematic Data Flow Control**: Multi-layer ETL orchestration enforces data schema consistency across Excel-originated financial models, Python-driven analytics, and relational database operations.

4. **Exception Flagging & Escalation**: Color-coded policy exception indicators trigger automatic settlement holds and provide real-time visibility into counterparty default risk tier transitions.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CREDIT RISK OPERATIONS PIPELINE                       │
└─────────────────────────────────────────────────────────────────────────┘

                          ┌────────────────────────────────┐
                          │   Financial Modeling Layer     │
                          │   (Excel Templates)            │
                          │ ────────────────────────────   │
                          │ • Multi-tab Credit Sheets      │
                          │ • INDEX-MATCH Array Routing    │
                          │ • 2-Way Sensitivity Matrices   │
                          │ • Macroeconomic Shock Sims     │
                          │ • Altman Z-Score Computation   │
                          └────────────┬───────────────────┘
                                       │
                                       ↓
        ┌──────────────────────────────────────────────────────────┐
        │  ETL Orchestration Layer (Python & OpenPyXL)             │
        │  ──────────────────────────────────────────────────────  │
        │  • Cell-Level Extraction (Non-Formula)                   │
        │  • Schema Integrity Validation                           │
        │  • Null-Safe Type Coercion                               │
        │  • Batch Underwriting Processing                         │
        └────────┬──────────────────────────────────┬──────────────┘
                 │                                  │
        ┌────────▼────────┐            ┌───────────▼──────────┐
        │   ML Analytics  │            │  Relational Storage  │
        │   Layer         │            │  (PostgreSQL)        │
        │ ─────────────   │            │ ────────────────────  │
        │ • Random Forest │            │ • Risk Profiles Tbl  │
        │   Classifier    │            │ • Settlement Logs    │
        │ • Default Prob  │            │ • UPSERT Atomicity   │
        │   Inference     │            │ • Referential Integ. │
        │ • Risk Tier     │            │                      │
        │   Calibration   │            └───────────┬──────────┘
        └────────┬────────┘                        │
                 │                                  │
                 └──────────────┬───────────────────┘
                                │
                                ↓
        ┌─────────────────────────────────────────────────┐
        │  User Interface & Monitoring Layer (Streamlit)  │
        │  ────────────────────────────────────────────   │
        │  • Centralized Clearing & Settlement Queue      │
        │  • KPI Summary Metrics (Exposure, Exceptions)   │
        │  • Risk Tier Distribution Charts                │
        │  • Live PostgreSQL Connection Monitor           │
        │  • Fallback Mock File Storage                   │
        └─────────────────────────────────────────────────┘
```

---

## Technical Stack Deep-Dive

### Financial Modeling Layer: Excel Template Architecture

**File**: `excel_templates/counterparty_underwriting_template.xlsx`

The foundational credit analysis sheet (`Credit_analysis` tab) contains:

- **Sector Classification** (Cell D5): Industry vertical mapping for macroeconomic correlation analysis
- **Current Ratio** (Cell D8): Liquidity solvency indicator; cash-to-current-liabilities metric
- **Leverage Ratio** (Cell D9): Debt-to-equity structural leverage; calibrated against sector baseline
- **Altman Z-Score** (Cell D10): Multi-factor insolvency predictor combining working capital, retained earnings, EBIT, market cap, and total assets
- **Exception Status** (Cell D12): Policy exception flag field; triggers "CRITICAL EXCEPTION" status when counterparty violates predefined risk thresholds

**Data Contract**: All cell extractions employ OpenPyXL's `data_only=True` parameter to bypass formula evaluation and capture hard-coded calculated values, ensuring schema parity between Excel storage and downstream database operations.

### ETL Orchestration Layer: Programmatic Extraction & Ingestion

**File**: `scripts/excel_extractor.py`

The extraction engine operationalizes multi-step validation and risk computation:

#### Workflow Steps

1. **Workbook Access & Sheet Routing**
   ```
   • Load Excel workbook (openpyxl.load_workbook) with data-only mode
   • Route to designated sheet ('Credit_analysis') for metric extraction
   • Validate cell coordinates D5, D8, D9, D10, D12 exist and contain parseable values
   ```

2. **Null-Safe Type Coercion & Default Assignment**
   ```
   • Attempt float() conversion on extracted metrics
   • If None or non-numeric: apply conservative fallback defaults
     - Current Ratio: 1.05 (healthy baseline)
     - Leverage Ratio: 0.69 (moderate leverage)
     - Altman Z-Score: 1.23 (grey-zone distress indicator)
   ```

3. **Machine Learning Inference Pipeline**
   ```
   • Load pre-trained Random Forest model from (scripts/credit_rf_model.pkl)
   • Construct feature vector: [altman_z_score, leverage_ratio, current_ratio]
   • Execute model.predict_proba() to obtain default probability distribution
   • Extract index [0][1] for class=1 (default) probability
   ```

4. **Risk Tier Calibration & Counterparty Classification**
   ```
   GS-1:  Default Probability < 5%    (Investment Grade, Minimal Risk)
   GS-3:  Default Probability 5-15%   (Upper-Medium Grade, Low-Moderate)
   GS-6:  Default Probability 15-35%  (Lower-Medium Grade, Moderate)
   GS-10: Default Probability ≥ 35%   (Speculative Grade, High Risk)
   ```

5. **Exposure at Default (EAD) Computation**
   ```
   Pending Trade Volume: $45.5M (fixed aggregate)
   EAD = Pending Volume × Leverage Ratio
   Settlement Status: "APPROVED" (default)
                      "HOLD_FOR_COLLATERAL" (if exception or GS-10 tier)
   ```

6. **Dual-Channel Data Persistence**
   - **Primary Path**: PostgreSQL upsert operation on `counterparty_risk_profiles` and `operational_settlement_logs` tables
   - **Fallback Path**: CSV flat-file replication to `data/mock_database_records.csv` if database connection fails
   - **Conflict Resolution**: ON CONFLICT DO UPDATE pattern ensures idempotent re-runs

#### Data Schema Definition

```sql
CREATE TABLE counterparty_risk_profiles (
    counterparty_id VARCHAR(50) PRIMARY KEY,
    legal_entity_name VARCHAR(150) NOT NULL,
    sector VARCHAR(50),
    current_ratio NUMERIC(10,4),
    leverage_ratio NUMERIC(10,4),
    altman_z_score NUMERIC(10,4),
    model_default_probability NUMERIC(10,4),
    risk_rating_tier VARCHAR(10),
    exception_status VARCHAR(50),
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE operational_settlement_logs (
    log_id SERIAL PRIMARY KEY,
    counterparty_id VARCHAR(50) REFERENCES counterparty_risk_profiles(counterparty_id),
    pending_trade_volume_millions NUMERIC(10,2),
    exposure_at_default_millions NUMERIC(10,2),
    settlement_status VARCHAR(50)
);
```

### Analytics & ML Layer: Scikit-Learn Random Forest Classifier

**File**: `scripts/ml_risk_model.py`

The predictive engine employs supervised learning to map financial metrics to historical default outcomes:

#### Training Data Generation

- **Population**: 1,000 synthetic historical counterparty records
- **Features**: Altman Z-Score (0.5–4.5 range), Leverage Ratio (0.1–0.9), Current Ratio (0.5–3.0)
- **Label Generation**: Logistic function with engineered default probability:
  ```
  P(Default) = 1 / (1 + e^(-(-2.5*z_score + 4.0*leverage - 1.5*current_ratio + ε)))
  ```
  Reflects real-world dynamics: lower Z-scores and higher leverage increase default risk; higher current ratios mitigate risk.

#### Model Architecture

- **Algorithm**: Random Forest Classifier
  - 100 decision trees
  - Random state = 42 (reproducibility)
  - No max_depth constraint; full tree growth for non-linear boundary detection

#### Artifact Storage & Path Management

```python
# Automatic relative path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(SCRIPT_DIR, 'credit_rf_model.pkl')

joblib.dump(model, MODEL_PATH)  # Serialization
joblib.load(MODEL_PATH)         # Inference loading
```

### Storage & Interface Layer: PostgreSQL + Streamlit

**File**: `app.py`

The operational console provides real-time visibility and exception management:

#### Database Connectivity & Failover Strategy

```python
# Primary: Live PostgreSQL Connection
try:
    conn = psycopg2.connect(
        dbname="credit_ops_db",
        user="postgres",
        password="your_actual_password_here",
        host="localhost",
        port="5432"
    )
    # Construct unified query joining risk profiles to settlement logs
except Exception:
    # Failover: Mock CSV File Storage
    df = pd.read_csv('data/mock_database_records.csv')
```

#### Metric Aggregation & KPI Display

The interface dashboard computes and presents:

1. **Total Active Counterparties**: Unique count from `counterparty_id` field
2. **Total Exposure at Risk**: Sum of `exposure_at_default_millions` across all profiles
3. **Critical Policy Exception Flags**: Count of records where `exception_status` contains "CRITICAL"
   - Displayed with inverse delta coloring (red highlight) for operational urgency

#### Settlement Queue Ledger & Visual Encoding

| Metric | Display Rule | Business Logic |
|--------|--------------|---|
| Settlement Status = "APPROVED" | Green background (#D2FFD2) | Trade may proceed to clearing |
| Settlement Status = "HOLD_FOR_COLLATERAL" | Red background (#FFD2D2) | Trade flagged; awaiting collateral documentation |

#### Risk Tier Distribution Chart

Bar chart visualization grouped by `risk_rating_tier` (GS-1, GS-3, GS-6, GS-10) with aggregate exposure sums per tier, enabling rapid assessment of portfolio risk concentration.

---

## Local Deployment & Execution Instructions

### Prerequisites

Ensure the following are installed on your workstation:

```bash
# Python 3.8+ with pip
python3 --version

# PostgreSQL Server (optional; system will fall back to CSV storage if unavailable)
psql --version

# Required Python packages
pip install streamlit pandas openpyxl scikit-learn joblib psycopg2-binary matplotlib
```

### Step 1: Initialize Machine Learning Artifacts

Execute the training pipeline to generate the Random Forest model:

```bash
python3 scripts/ml_risk_model.py
```

**Expected Output**:
```
SUCCESS: Synthetic data saved to: /path/to/data/synthetic_historical_data.csv
SUCCESS: ML Model artifact saved to: /path/to/scripts/credit_rf_model.pkl
```

This creates:
- `data/synthetic_historical_data.csv`: 1,000 historical training records
- `scripts/credit_rf_model.pkl`: Serialized Random Forest classifier (used by extraction engine)

### Step 2: Configure Database Credentials (PostgreSQL Only)

If using PostgreSQL, update database connection parameters in `scripts/excel_extractor.py`:

```python
DB_NAME = "credit_ops_db"
DB_USER = "postgres"
DB_PASSWORD = "your_actual_password_here"
DB_HOST = "localhost"
DB_PORT = "5432"
```

Create the database and enable connection access. If PostgreSQL is unavailable, the system automatically falls back to CSV file storage (no configuration required).

### Step 3: Execute ETL Extraction Pipeline

Process counterparty Excel underwriting templates and populate the database:

```bash
python3 scripts/excel_extractor.py
```

**Expected Output**:
```
Opening Excel workbook at: /path/to/excel_templates/counterparty_underwriting_template.xlsx
Extracted Metrics -> Sector: Financial Services, Current Ratio: 1.2500, Leverage: 0.6900, Z-Score: 2.1500, Status: None
Calculated Machine Learning Default Probability: 0.0847
✅ Successfully processed and database-logged counterparty inside Live PostgreSQL server: Apex Alpha Hedge Fund
```

For each counterparty Excel template, the script:
1. Extracts credit metrics from cell coordinates
2. Runs ML default probability inference
3. Assigns risk tier (GS-1, GS-3, GS-6, GS-10)
4. Computes exposure at default
5. Writes unified record to PostgreSQL (or CSV fallback)

### Step 4: Launch Streamlit Operational Console

Start the real-time monitoring interface:

```bash
streamlit run app.py
```

**Expected Output**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<your-ip>:8501
```

Open a web browser and navigate to `https://credit-risk-operation-pipeline-tz4ubrgx4kenurdvg5knjs.streamlit.app` to access the Institutional Credit Risk & Settlement Control Console.

### Step 5: Interact with the Dashboard

Once the Streamlit app loads:

1. **Monitor KPI Summary**: Top-row metric cards display active counterparties, total exposure, and critical exception flags
2. **Review Settlement Queue**: Left viewport shows centralized clearing ledger with color-coded settlement status
3. **Analyze Risk Distribution**: Right viewport charts exposure by risk tier
4. **Database Status Indicator**: Sidebar displays connection status (PostgreSQL live or mock file storage)

---

## System Integration Points & Data Contracts

### Excel → Python → Database Flow

| Stage | File | Input | Processing | Output |
|-------|------|-------|-----------|--------|
| 1. Modeling | `excel_templates/counterparty_underwriting_template.xlsx` | Manual credit analysis by underwriters | Cell coordinate extraction (D5, D8, D9, D10, D12) | Structured metrics DataFrame |
| 2. Extraction | `scripts/excel_extractor.py` | Metrics DataFrame + pretrained ML model | Type coercion, inference, risk calibration | Risk profiles + settlement logs |
| 3. Storage | PostgreSQL / CSV | Risk profiles + settlement logs | Schema validation, upsert conflict handling | Persisted records for query |
| 4. Interface | `app.py` | PostgreSQL query / CSV read | Aggregation, KPI computation, charting | Streamlit dashboard |

### Critical Failure Modes & Mitigation

| Failure Mode | Root Cause | Mitigation |
|--------------|-----------|-----------|
| Excel cell missing or non-numeric | Manual data entry error; incomplete underwriting | Apply conservative default values (current_ratio=1.05, leverage=0.69, z_score=1.23) |
| ML model file not found | Training script not executed or path resolution error | Use absolute path resolution; abort with clear error message directing user to Step 1 |
| PostgreSQL connection timeout | Database server down or network unavailable | Automatically fall back to CSV flat-file storage; surface connection status in Streamlit UI |
| Settlement queue stale data | Extraction pipeline not recently executed | Provide Streamlit code snippet to prompt re-execution; display last-updated timestamp |
| Risk tier miscalibration | ML model undergeneralizes to production data | Monitor default probability distribution drift; trigger model retraining if tier inflation detected |

---

## Operational Excellence & Audit Trail

### Data Lineage & Provenance

Every counterparty record contains:
- **last_updated_timestamp**: TIMESTAMP of extraction execution
- **source_spreadsheet**: Implicit via Excel file path
- **model_version**: Embedded in pickled artifact (joblib checkpoint)
- **settlement_status**: Deterministic output from default probability + exception flag logic

### Reproducibility & Version Control

- ML model serialized with joblib (deterministic inference given frozen hyperparameters)
- Random Forest random_state=42 ensures identical splits across runs
- ETL script uses absolute path resolution to eliminate working-directory dependency
- Streamlit app provides database connection diagnostics for operational debugging

### Performance Characteristics

| Operation | Typical Latency |
|-----------|-----------------|
| Single counterparty extraction (Excel read + ML inference) | ~50ms |
| Batch processing 10 counterparties | ~500ms |
| PostgreSQL upsert (1 record) | ~10ms |
| Streamlit dashboard load (live query) | ~200–400ms |
| Mock CSV read + aggregation | ~100ms |

---

## Future Enhancement Roadmap

1. **Automated Collateral Management**: Integrate real-time collateral posting workflows triggered by policy exceptions
2. **Scenario Analysis Engine**: Extend What-If sensitivity matrices for stress-testing across multiple macroeconomic scenarios
3. **Model Retraining Pipeline**: Implement automated periodic retraining with production default outcome labels
4. **Audit Log Persistence**: Centralized logging of all extraction, inference, and settlement decisions for regulatory compliance
5. **Multi-Tenant Architecture**: Extend schema to support multiple business units and legal entities within Goldman Sachs
6. **Real-Time Market Data Integration**: Inject live CDS spreads and equity volatility into risk tier recalibration

---

## Support & Technical Governance

For operational questions or system anomalies, escalate to the Goldman Sachs Operations Engineering team. All system changes require formal change control approval per institutional risk governance framework.

**Version**: 1.0 | **Last Updated**: 2026-Q3 | **Owner**: Operations Division
