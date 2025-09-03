-- Create ENUM type for status (PostgreSQL specific)
CREATE TYPE status_enum AS ENUM ('success', 'fail', 'skip', 'pending');

-- Create the table with enhanced constraints
CREATE TABLE IF NOT EXISTS samples (
    id SERIAL PRIMARY KEY,
    sample_name VARCHAR(30) NOT NULL,
    dataset_name VARCHAR(30) NOT NULL,
    is_10x BOOLEAN DEFAULT true,
    status status_enum NOT NULL DEFAULT 'pending',
    library_type VARCHAR(100),
    sanger_id VARCHAR(50) UNIQUE,  -- Assuming Sanger IDs should be unique
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

-- Composite unique constraint (if needed)
UNIQUE(dataset_name, sample_name) );