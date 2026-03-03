-- Create database (run as MySQL user with CREATE privilege)
CREATE DATABASE IF NOT EXISTS meta_poc
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE meta_poc;

-- Create tables:

-- user:
CREATE TABLE IF NOT EXISTS `user` (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NULL,
  phone VARCHAR(64) NULL
);

-- workspace:
CREATE TABLE IF NOT EXISTS workspace (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  workspace_name VARCHAR(255) NOT NULL,
  INDEX ix_workspace_user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES `user`(id)
);

-- integration:
CREATE TABLE IF NOT EXISTS integration (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  workspace_id INT NOT NULL,
  ad_platform VARCHAR(64) NOT NULL,
  status TINYINT(1) NOT NULL DEFAULT 1,
  email VARCHAR(255) NULL,
  ad_login_userinfo JSON NULL,
  ads_account JSON NULL,
  tokens JSON NULL,
  refresh_tokens JSON NULL,
  access_removed TINYINT(1) NOT NULL DEFAULT 0,
  last_authenticated DATETIME(6) NULL,
  updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX ix_integration_workspace_id (workspace_id),
  INDEX ix_integration_ad_platform (ad_platform),
  FOREIGN KEY (user_id) REFERENCES `user`(id)
);

-- platform_data (Meta ETL result: campaigns only)
CREATE TABLE IF NOT EXISTS platform_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  workspace_id INT NOT NULL,
  campaigns JSON NULL,
  created_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_platform_data_workspace_id (workspace_id),
  INDEX ix_platform_data_workspace_id (workspace_id)
);
