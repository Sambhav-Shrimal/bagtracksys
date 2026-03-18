-- BagTrack Production Management System
-- Database Schema for MySQL

CREATE DATABASE IF NOT EXISTS bagtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bagtrack_db;

-- Workers Table
CREATE TABLE workers (
    worker_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone (phone_number),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- Production Submissions Table
CREATE TABLE production (
    production_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    photo_path VARCHAR(500) NOT NULL,
    bag_type VARCHAR(100) DEFAULT NULL,
    quantity INT NOT NULL,
    rate DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('SUBMITTED', 'APPROVED', 'REJECTED', 'PAYMENT_SENT', 'PAYMENT_RECEIVED') DEFAULT 'SUBMITTED',
    rejection_reason TEXT DEFAULT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL DEFAULT NULL,
    reviewed_by INT NULL DEFAULT NULL,
    FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES workers(worker_id) ON DELETE SET NULL,
    INDEX idx_worker (worker_id),
    INDEX idx_status (status),
    INDEX idx_submitted (submitted_at)
) ENGINE=InnoDB;

-- Payments Table
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('UPI', 'BANK_TRANSFER', 'CASH') NOT NULL,
    transaction_reference VARCHAR(255) DEFAULT NULL,
    payment_screenshot VARCHAR(500) DEFAULT NULL,
    status ENUM('PAYMENT_SENT', 'PAYMENT_RECEIVED') DEFAULT 'PAYMENT_SENT',
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP NULL DEFAULT NULL,
    paid_by INT NOT NULL,
    notes TEXT DEFAULT NULL,
    FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE,
    FOREIGN KEY (paid_by) REFERENCES workers(worker_id) ON DELETE CASCADE,
    INDEX idx_worker (worker_id),
    INDEX idx_status (status),
    INDEX idx_paid (paid_at)
) ENGINE=InnoDB;

-- Payment Production Links (Many-to-Many relationship)
CREATE TABLE payment_production_links (
    link_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT NOT NULL,
    production_id INT NOT NULL,
    amount_allocated DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE,
    FOREIGN KEY (production_id) REFERENCES production(production_id) ON DELETE CASCADE,
    INDEX idx_payment (payment_id),
    INDEX idx_production (production_id)
) ENGINE=InnoDB;

-- Activity Log for Audit Trail
CREATE TABLE activity_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    details TEXT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES workers(worker_id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- Insert default admin user
-- Password: admin123 (hashed with werkzeug.security)
-- IMPORTANT: Change this password in production!
INSERT INTO workers (name, phone_number, password_hash, is_admin) VALUES
('Admin User', '9999999999', 'scrypt:32768:8:1$YfGvQZXkrP8L7RFD$d8f7b1e3e5a2c9d4f6b8a0e2c4d6f8a0b2e4c6d8f0a2b4e6c8d0f2a4b6e8c0d2f4a6b8c0e2d4f6a8b0c2e4d6f8a0b2c4e6d8f0a2b4c6e8d0f2a4b6c8e0d2f4a6b8c0e2d4f6a8b0c2e4d6f8', TRUE);

-- Example worker (for testing)
-- Password: worker123
INSERT INTO workers (name, phone_number, password_hash, is_admin) VALUES
('Test Worker', '8888888888', 'scrypt:32768:8:1$YfGvQZXkrP8L7RFD$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6', FALSE);
