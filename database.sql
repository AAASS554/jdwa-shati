CREATE DATABASE IF NOT EXISTS exam_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE exam_db;

CREATE TABLE IF NOT EXISTS card_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_key VARCHAR(32) NOT NULL UNIQUE,
    valid_days INT NOT NULL,
    create_time DATETIME NOT NULL,
    status TINYINT NOT NULL DEFAULT 0,
    use_time DATETIME NULL,
    device_id VARCHAR(64) NULL,
    bind_time DATETIME NULL,
    expiry_time DATETIME NULL
);

CREATE TABLE IF NOT EXISTS card_status_change (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_key VARCHAR(32) NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    change_time DATETIME NOT NULL
); 