-- Create schema for credit operations
CREATE TABLE counterparty_risk_profiles (
    counterparty_id VARCHAR(50) PRIMARY KEY,
    legal_entity_name VARCHAR(150) NOT NULL,
    sector VARCHAR(50),
    current_ratio NUMERIC(5,2),
    leverage_ratio NUMERIC(5,2),
    altman_z_score NUMERIC(5,2),
    model_default_probability NUMERIC(5,4), -- Filled by Python ML model later
    risk_rating_tier VARCHAR(10),           -- E.g., GS-1 (Safe) to GS-10 (High Risk)
    exception_status VARCHAR(20),           -- PASS or CRITICAL EXCEPTION
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE operational_settlement_logs (
    log_id SERIAL PRIMARY KEY,
    counterparty_id VARCHAR(50) REFERENCES counterparty_risk_profiles(counterparty_id),
    pending_trade_volume_millions NUMERIC(10,2),
    exposure_at_default_millions NUMERIC(10,2),
    settlement_status VARCHAR(30) -- APPROVED, HOLD_FOR_COLLATERAL, REJECTED
);
CREATE DATABASE credit_ops_db;
