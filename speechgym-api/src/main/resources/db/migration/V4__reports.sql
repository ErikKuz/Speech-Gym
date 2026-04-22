CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    pdf_artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE RESTRICT,
    overall_score INTEGER NOT NULL,
    clarity INTEGER NOT NULL,
    pace_wpm INTEGER NOT NULL,
    filler_words_count INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    structure_score INTEGER NOT NULL,
    emotional_tone VARCHAR(64) NOT NULL,
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvements JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reports_job UNIQUE (job_id),
    CONSTRAINT uq_reports_pdf_artifact UNIQUE (pdf_artifact_id)
);

CREATE INDEX idx_reports_user_created_at
    ON reports (user_id, created_at DESC);
