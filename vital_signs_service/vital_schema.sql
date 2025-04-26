CREATE TABLE vital_signs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(24) NOT NULL,
    systolic_bp INT CHECK (systolic_bp BETWEEN 70 AND 250),
    diastolic_bp INT CHECK (diastolic_bp BETWEEN 40 AND 150),
    heart_rate INT CHECK (heart_rate BETWEEN 30 AND 200),
    blood_glucose DECIMAL(5,2) CHECK (blood_glucose BETWEEN 2.0 AND 25.0),
    temperature DECIMAL(4,2) CHECK (temperature BETWEEN 32.0 Avital_signsND 43.0),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX user_index (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;