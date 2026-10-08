CREATE TABLE IF NOT EXISTS ai_requests (
    id SERIAL PRIMARY KEY,
    user_query TEXT NOT NULL,
    task_type TEXT NOT NULL
        CHECK (task_type IN ('Coding', 'General Knowledge', 'Reasoning', 'Creative Writing')),
    experiment_mode TEXT NOT NULL
        CHECK (experiment_mode IN ('baseline', 'proposed')),
    model TEXT,
    primary_model TEXT NOT NULL,
    fallback_model TEXT NOT NULL,
    response_time_ms INTEGER NOT NULL CHECK (response_time_ms >= 0),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    error_type TEXT
        CHECK (
            error_type IS NULL OR error_type IN (
                'timeout',
                'rate_limit',
                'server_error',
                'network_error',
                'authentication_error',
                'invalid_request',
                'unknown_error'
            )
        ),
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    final_status TEXT NOT NULL CHECK (final_status IN ('success', 'failed')),
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ai_requests_created_at_idx
    ON ai_requests (created_at DESC);

CREATE INDEX IF NOT EXISTS ai_requests_experiment_mode_idx
    ON ai_requests (experiment_mode, created_at DESC);
