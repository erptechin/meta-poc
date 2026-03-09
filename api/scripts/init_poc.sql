-- Create database (run as MySQL user with CREATE privilege)
CREATE DATABASE IF NOT EXISTS meta_poc
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE meta_poc;

-- Create tables:

-- integration (matches api/models.py Integration)
CREATE TABLE IF NOT EXISTS integration (
  id INT AUTO_INCREMENT PRIMARY KEY,
  workspace_id INT NOT NULL DEFAULT 1,
  ad_platform VARCHAR(64) NOT NULL,
  status TINYINT(1) NOT NULL DEFAULT 1,
  ads_userinfo JSON NULL,
  ads_accounts JSON NULL,
  tokens JSON NULL,
  refresh_tokens JSON NULL,
  access_removed TINYINT(1) NOT NULL DEFAULT 0,
  last_authenticated DATETIME(6) NULL,
  updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX ix_integration_workspace_id (workspace_id),
  INDEX ix_integration_ad_platform (ad_platform)
);

-- platform_data (one row per integration per report_date per campaign; type = meta | google | linkedin)
CREATE TABLE IF NOT EXISTS platform_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  integration_id INT NOT NULL,
  type VARCHAR(32) NOT NULL DEFAULT 'meta',
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
  INDEX ix_platform_data_type (type),
  INDEX ix_platform_data_integration_report_date (integration_id, report_date),
  INDEX ix_platform_data_campaign_name (campaign_name),
  FOREIGN KEY (integration_id) REFERENCES integration(id) ON DELETE CASCADE
);