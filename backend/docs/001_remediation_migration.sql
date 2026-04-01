-- Migration: Cybrain QS Remediation
-- Description: Adding version lineage, AI metadata to link tables, and config-driven lifecycle table

-- 1. Version Lineage (SOP Replacement)
ALTER TABLE sop_versions 
ADD COLUMN superseded_by_version_id UUID REFERENCES sop_versions(id);

-- 2. Expand Link Tables for AI Explanations
ALTER TABLE sop_deviation_links ADD COLUMN rationale_text TEXT;
ALTER TABLE deviation_capa_links ADD COLUMN rationale_text TEXT;
ALTER TABLE capa_audit_links ADD COLUMN rationale_text TEXT;
ALTER TABLE audit_decision_links ADD COLUMN rationale_text TEXT;
ALTER TABLE decision_sop_links ADD COLUMN rationale_text TEXT;

-- 3. Decouple Lifecycle Logic (Config-Driven)
CREATE TABLE IF NOT EXISTS lifecycle_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    config_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
