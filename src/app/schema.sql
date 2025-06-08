-- schema.sql
-- Initializes the PostgreSQL schema for analysis result ingestion.

CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommended indexes
CREATE INDEX IF NOT EXISTS idx_analysis_symbol_time ON analysis_results (symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_analysis_source ON analysis_results (source);
CREATE INDEX IF NOT EXISTS idx_analysis_data_gin ON analysis_results USING GIN (data);
