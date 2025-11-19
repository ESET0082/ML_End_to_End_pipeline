-- Create required databases
CREATE DATABASE meter_db;
CREATE DATABASE mlflow;

-- Connect to meter_db to create tables
\connect meter_db;


DROP TABLE IF EXISTS meter_data CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    meter_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    mobile_number BIGINT UNIQUE NOT NULL,
    address TEXT,
    city TEXT,
    pincode VARCHAR(10),
    connection_type VARCHAR(20),   -- Domestic / Commercial / Industrial
    tariff_plan VARCHAR(20),       -- LT-1, LT-2, LT-3, etc.
    connection_date DATE DEFAULT CURRENT_DATE - (random() * INTERVAL '2000 days')
);


CREATE TABLE meter_data (
    id SERIAL PRIMARY KEY,
    meter_id TEXT NOT NULL,
    reading_date TIMESTAMP NOT NULL,
    units NUMERIC(10,3),
    voltage NUMERIC(6,2),
    temperature NUMERIC(5,2),
    power_factor NUMERIC(4,3),
    load_kw NUMERIC(8,3),
    frequency_hz NUMERIC(5,3),
    phase VARCHAR(10),              -- Single / Three
    status VARCHAR(10),             -- OK / CHECK / ALERT
    FOREIGN KEY (meter_id) REFERENCES customers(meter_id) ON DELETE CASCADE
);

INSERT INTO customers (meter_id, name, mobile_number, address, city, pincode, connection_type, tariff_plan)
SELECT
    'MTR' || lpad(gs::text, 7, '0') AS meter_id,
    'Customer ' || gs,
    6000000000 + floor(random() * 999999999)::BIGINT AS mobile_number,
    'Address ' || gs,
    (ARRAY['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar'])[floor(random()*5)+1],
    lpad((380000 + floor(random() * 60000))::text, 6, '0'),
    (ARRAY['Domestic', 'Commercial', 'Industrial'])[floor(random()*3)+1],
    (ARRAY['LT-1', 'LT-2', 'LT-3', 'HT-1'])[floor(random()*4)+1]
FROM generate_series(1, 1000) AS gs;

select count(*) from customers;
INSERT INTO meter_data (
    meter_id, reading_date, units, voltage, temperature, power_factor,
    load_kw, frequency_hz, phase, status
)
SELECT
    'MTR' || lpad((floor(random() * 1000) + 1)::text, 7, '0'),
    NOW() - (random() * INTERVAL '365 days'),
    round((random() * 50)::numeric, 3),              -- Units consumed
    round((210 + random() * 40)::numeric, 2),        -- Voltage 210–250
    round((20 + random() * 20)::numeric, 2),         -- Temperature 20–40°C
    round((0.75 + random() * 0.25)::numeric, 3),     -- PF 0.75–1.00
    round((random() * 10)::numeric, 3),              -- Load 0–10 kW
    round((49.5 + random() * 1.0)::numeric, 3),      -- Frequency 49.5–50.5 Hz
    (ARRAY['Single', 'Three'])[floor(random()*2)+1],
    (CASE
        WHEN random() < 0.92 THEN 'OK'
        WHEN random() < 0.97 THEN 'CHECK'
        ELSE 'ALERT'
     END)
FROM generate_series(1, 3000);
select count(*) from meter_data;