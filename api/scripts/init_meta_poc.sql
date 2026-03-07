-- Create database (run as MySQL user with CREATE privilege)
CREATE DATABASE IF NOT EXISTS meta_poc
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE meta_poc;

-- Create tables:

-- integration (columns match meta-poc init_postgres.sql 5-15)
CREATE TABLE IF NOT EXISTS integration (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_email VARCHAR(255) NULL,
  access_token VARCHAR(2048) NULL,
  refresh_token VARCHAR(2048) NULL,
  token_expiry DATETIME(6) NULL,
  google_ads_customer_id VARCHAR(64) NULL,
  account_name VARCHAR(255) NULL,
  access_removed INT NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
);

-- platform_data (columns match meta-poc init_postgres.sql campaign_data 20-34)
CREATE TABLE IF NOT EXISTS platform_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  integration_id INT NOT NULL,
  report_date DATE NULL,
  campaign_name VARCHAR(512) NULL,
  campaign_type VARCHAR(128) NULL,
  source VARCHAR(128) NULL,
  impressions INT NULL,
  clicks INT NULL,
  cpm DECIMAL(14, 4) NULL,
  cpc DECIMAL(14, 4) NULL,
  ctr DECIMAL(14, 4) NULL,
  amount_spent DECIMAL(14, 4) NULL,
  data JSON NULL,
  created_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX ix_platform_data_integration_id (integration_id),
  INDEX ix_platform_data_integration_report_date (integration_id, report_date),
  INDEX ix_platform_data_campaign_name (campaign_name),
  FOREIGN KEY (integration_id) REFERENCES integration(id) ON DELETE CASCADE
);

-- report_summary (columns match meta-poc init_postgres.sql 42-51)
CREATE TABLE IF NOT EXISTS report_summary (
  id INT AUTO_INCREMENT PRIMARY KEY,
  integration_id INT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  total_impressions BIGINT NOT NULL DEFAULT 0,
  total_clicks BIGINT NOT NULL DEFAULT 0,
  total_amount_spent DECIMAL(14, 4) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_report_summary_integration_dates (integration_id, start_date, end_date),
  INDEX ix_report_summary_integration_dates (integration_id, start_date, end_date),
  FOREIGN KEY (integration_id) REFERENCES integration(id) ON DELETE CASCADE
);
