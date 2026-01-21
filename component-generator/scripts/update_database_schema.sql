-- Database Schema Updates for Success Patterns Tracking
-- Run this to add success patterns tracking to the learning database

-- Create success_patterns table
CREATE TABLE IF NOT EXISTS success_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    framework TEXT,
    complexity_score REAL,
    attempts INTEGER DEFAULT 1,
    cost_usd REAL,
    tokens INTEGER,
    success_score INTEGER,
    success_factors TEXT,  -- JSON array of success factors
    metadata TEXT,  -- Full JSON metadata
    code_hash TEXT,  -- Hash of generated code for deduplication
    created_at TEXT NOT NULL,
    updated_at TEXT,
    UNIQUE(component_name, created_at)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_success_category ON success_patterns(category);
CREATE INDEX IF NOT EXISTS idx_success_subcategory ON success_patterns(subcategory);
CREATE INDEX IF NOT EXISTS idx_success_framework ON success_patterns(framework);
CREATE INDEX IF NOT EXISTS idx_success_complexity ON success_patterns(complexity_score);
CREATE INDEX IF NOT EXISTS idx_success_attempts ON success_patterns(attempts);
CREATE INDEX IF NOT EXISTS idx_success_score ON success_patterns(success_score);
CREATE INDEX IF NOT EXISTS idx_success_created ON success_patterns(created_at);

-- Create pattern_features table for detailed feature tracking
CREATE TABLE IF NOT EXISTS pattern_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT,
    feature_type TEXT,  -- 'boolean', 'string', 'number'
    FOREIGN KEY (pattern_id) REFERENCES success_patterns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pattern_features_pattern ON pattern_features(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_features_name ON pattern_features(feature_name);

-- Create pattern_usage table to track when patterns are used
CREATE TABLE IF NOT EXISTS pattern_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    used_for_component TEXT NOT NULL,
    relevance_score REAL,
    resulted_in_success BOOLEAN,
    used_at TEXT NOT NULL,
    FOREIGN KEY (pattern_id) REFERENCES success_patterns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pattern_usage_pattern ON pattern_usage(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_usage_used_at ON pattern_usage(used_at);

-- Create analytics views
CREATE VIEW IF NOT EXISTS success_rate_by_category AS
SELECT
    category,
    COUNT(*) as total_components,
    SUM(CASE WHEN attempts = 1 THEN 1 ELSE 0 END) as first_attempt_success,
    ROUND(100.0 * SUM(CASE WHEN attempts = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate,
    ROUND(AVG(cost_usd), 4) as avg_cost,
    ROUND(AVG(complexity_score), 2) as avg_complexity,
    ROUND(AVG(success_score), 2) as avg_success_score
FROM success_patterns
WHERE category IS NOT NULL
GROUP BY category
ORDER BY success_rate DESC;

CREATE VIEW IF NOT EXISTS success_rate_by_complexity AS
SELECT
    CASE
        WHEN complexity_score < 15 THEN 'low'
        WHEN complexity_score < 30 THEN 'medium'
        WHEN complexity_score < 50 THEN 'high'
        ELSE 'very_high'
    END as complexity_range,
    COUNT(*) as total_components,
    SUM(CASE WHEN attempts = 1 THEN 1 ELSE 0 END) as first_attempt_success,
    ROUND(100.0 * SUM(CASE WHEN attempts = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate,
    ROUND(AVG(cost_usd), 4) as avg_cost,
    ROUND(AVG(success_score), 2) as avg_success_score
FROM success_patterns
GROUP BY complexity_range
ORDER BY complexity_score;

CREATE VIEW IF NOT EXISTS top_success_patterns AS
SELECT
    component_name,
    category,
    subcategory,
    framework,
    success_score,
    attempts,
    cost_usd,
    complexity_score,
    created_at
FROM success_patterns
ORDER BY success_score DESC, attempts ASC, cost_usd ASC
LIMIT 20;

-- Insert the NeMo QA Operator as first success pattern
INSERT OR IGNORE INTO success_patterns (
    component_name,
    category,
    subcategory,
    framework,
    complexity_score,
    attempts,
    cost_usd,
    tokens,
    success_score,
    success_factors,
    metadata,
    created_at
) VALUES (
    'NeMoQuestionAnsweringOperator',
    'ml',
    'nlp',
    'nvidia_nemo',
    24.0,
    1,
    0.0522,
    4972,
    165,
    '["Simplified specification (5 inputs vs original 11)", "Automatic parameter ordering", "Medium complexity (24.0 score)", "Mock execution for testing", "Dual Airflow 2.x/3.x compatibility", "Clear naming and structure"]',
    '{"component_type": "operator", "generation_date": "2026-01-20", "validation_results": {"syntax_errors": 0, "import_errors": 0, "security_issues": 0, "warnings": 0}}',
    '2026-01-20T00:00:00'
);

-- Commit changes
COMMIT;
