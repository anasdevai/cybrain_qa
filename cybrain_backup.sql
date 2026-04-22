--
-- PostgreSQL database dump
--

\restrict cX4FmOBZFfBZnulpWkxyvUs9HFmqcsILCMBrrVZb1vf7WbEEkQqFTkSSeMr39Ap

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_decision_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_decision_links (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    audit_finding_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    link_reason character varying(100),
    confidence_score double precision,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    rationale_text text
);


ALTER TABLE public.audit_decision_links OWNER TO postgres;

--
-- Name: audit_findings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_findings (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    external_id character varying(255),
    audit_number character varying(100),
    finding_number character varying(100),
    authority character varying(100),
    site character varying(100),
    audit_date timestamp without time zone,
    question_text text,
    finding_text text,
    response_text text,
    acceptance_status character varying(50),
    source_system character varying(100),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_findings OWNER TO postgres;

--
-- Name: capa_audit_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.capa_audit_links (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    capa_id uuid NOT NULL,
    audit_finding_id uuid NOT NULL,
    link_reason character varying(100),
    confidence_score double precision,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    rationale_text text
);


ALTER TABLE public.capa_audit_links OWNER TO postgres;

--
-- Name: capas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.capas (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    external_id character varying(255),
    capa_number character varying(100) NOT NULL,
    title character varying(255) NOT NULL,
    external_status character varying(50),
    action_type character varying(50),
    action_text text,
    effectiveness_text text,
    owner_name character varying(255),
    due_date timestamp without time zone,
    effectiveness_status character varying(50),
    source_system character varying(100),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capas OWNER TO postgres;

--
-- Name: decision_sop_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.decision_sop_links (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    sop_id uuid NOT NULL,
    sop_version_id uuid,
    link_reason character varying(100),
    confidence_score double precision,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    rationale_text text
);


ALTER TABLE public.decision_sop_links OWNER TO postgres;

--
-- Name: decisions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.decisions (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    external_id character varying(255),
    decision_number character varying(100),
    decision_type character varying(100),
    title character varying(255) NOT NULL,
    decision_statement text NOT NULL,
    rationale_text text,
    risk_assessment_text text,
    alternatives_text text,
    final_conclusion text,
    decision_date timestamp without time zone,
    decided_by_role character varying(100),
    source_system character varying(100),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.decisions OWNER TO postgres;

--
-- Name: deviation_capa_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.deviation_capa_links (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    deviation_id uuid NOT NULL,
    capa_id uuid NOT NULL,
    link_reason character varying(100),
    confidence_score double precision,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    rationale_text text
);


ALTER TABLE public.deviation_capa_links OWNER TO postgres;

--
-- Name: deviations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.deviations (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    external_id character varying(255),
    deviation_number character varying(100) NOT NULL,
    title character varying(255) NOT NULL,
    category character varying(100),
    site character varying(100),
    product_line character varying(100),
    external_status character varying(50),
    description_text text,
    root_cause_text text,
    impact_level character varying(50),
    source_system character varying(100),
    event_date timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.deviations OWNER TO postgres;

--
-- Name: document_versions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.document_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    version_number integer NOT NULL,
    doc_json jsonb NOT NULL,
    change_summary text,
    status character varying(50) DEFAULT 'draft'::character varying NOT NULL,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.document_versions OWNER TO postgres;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    title character varying(255) NOT NULL,
    profile character varying(50) DEFAULT 'sop'::character varying NOT NULL,
    current_version_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- Name: knowledge_chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knowledge_chunks (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    entity_version_id uuid,
    chunk_type character varying(50),
    block_id character varying(100),
    chunk_text text NOT NULL,
    chunk_order integer NOT NULL,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.knowledge_chunks OWNER TO postgres;

--
-- Name: lifecycle_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lifecycle_configs (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    entity_type character varying(50) NOT NULL,
    config_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.lifecycle_configs OWNER TO postgres;

--
-- Name: sop_deviation_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sop_deviation_links (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    sop_id uuid NOT NULL,
    deviation_id uuid NOT NULL,
    link_reason character varying(100),
    confidence_score double precision,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    rationale_text text
);


ALTER TABLE public.sop_deviation_links OWNER TO postgres;

--
-- Name: sop_versions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sop_versions (
    id uuid NOT NULL,
    sop_id uuid NOT NULL,
    external_version_id character varying(100),
    version_number character varying(50) NOT NULL,
    external_status character varying(50),
    effective_date timestamp without time zone,
    review_date timestamp without time zone,
    content_json jsonb NOT NULL,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    superseded_by_version_id uuid
);


ALTER TABLE public.sop_versions OWNER TO postgres;

--
-- Name: sops; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sops (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    external_id character varying(255),
    sop_number character varying(100) NOT NULL,
    title character varying(255) NOT NULL,
    department character varying(100),
    source_system character varying(100),
    is_active boolean,
    current_version_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sops OWNER TO postgres;

--
-- Name: source_references; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.source_references (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    reference_type character varying(50) NOT NULL,
    reference_label character varying(255),
    reference_value character varying(255) NOT NULL,
    metadata_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.source_references OWNER TO postgres;

--
-- Data for Name: audit_decision_links; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_decision_links (id, tenant_id, audit_finding_id, decision_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
\.


--
-- Data for Name: audit_findings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_findings (id, tenant_id, external_id, audit_number, finding_number, authority, site, audit_date, question_text, finding_text, response_text, acceptance_status, source_system, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: capa_audit_links; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.capa_audit_links (id, tenant_id, capa_id, audit_finding_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
\.


--
-- Data for Name: capas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.capas (id, tenant_id, external_id, capa_number, title, external_status, action_type, action_text, effectiveness_text, owner_name, due_date, effectiveness_status, source_system, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: decision_sop_links; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.decision_sop_links (id, tenant_id, decision_id, sop_id, sop_version_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
\.


--
-- Data for Name: decisions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.decisions (id, tenant_id, external_id, decision_number, decision_type, title, decision_statement, rationale_text, risk_assessment_text, alternatives_text, final_conclusion, decision_date, decided_by_role, source_system, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: deviation_capa_links; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.deviation_capa_links (id, tenant_id, deviation_id, capa_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
\.


--
-- Data for Name: deviations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.deviations (id, tenant_id, external_id, deviation_number, title, category, site, product_line, external_status, description_text, root_cause_text, impact_level, source_system, event_date, created_at, updated_at) FROM stdin;
cc1726dd-c72c-47cd-bc01-e688ebdec08a	11111111-1111-1111-1111-111111111111	\N	DEV-IT-089	Unauthorized Remote Access	IT/OT Security	Main Plant	\N	closed	Vendor 'Siemens' accessed PLC node without 24h notice.	Manual VPN gate bypass.	Major	\N	\N	2026-04-08 19:38:49.658269	2026-04-08 19:38:49.658269
\.


--
-- Data for Name: document_versions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.document_versions (id, document_id, version_number, doc_json, change_summary, status, metadata_json, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.documents (id, title, profile, current_version_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: knowledge_chunks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.knowledge_chunks (id, tenant_id, entity_type, entity_id, entity_version_id, chunk_type, block_id, chunk_text, chunk_order, metadata_json, created_at) FROM stdin;
\.


--
-- Data for Name: lifecycle_configs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lifecycle_configs (id, tenant_id, entity_type, config_json, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sop_deviation_links; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sop_deviation_links (id, tenant_id, sop_id, deviation_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
\.


--
-- Data for Name: sop_versions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sop_versions (id, sop_id, external_version_id, version_number, external_status, effective_date, review_date, content_json, metadata_json, created_at, updated_at, superseded_by_version_id) FROM stdin;
b67aa40a-3291-4ec4-9453-bcefb8043cbe	a73ff058-d807-4f59-bcd5-2e72269c0f95	\N	1	under_review	\N	\N	{"type": "doc", "content": [{"type": "paragraph", "attrs": {"block-id": "78ec5c77-4467-414b-93bc-15af01ba97ab"}}]}	{"sopStatus": "under_review", "variables": {}, "approvedBy": "", "auditTrail": [], "sopMetadata": {"title": "Untitled SOP", "author": "System", "reviewer": "arhiyan", "riskLevel": "Low", "department": "Quality", "documentId": "SOP-95BA293A", "references": ["eddede"], "reviewDate": "", "effectiveDate": "", "regulatoryReferences": []}, "versionNote": "", "obsoleteReason": "", "approvalSignature": "", "replacementDocumentId": ""}	2026-04-08 18:38:52.318306	2026-04-08 18:40:21.608927	\N
\.


--
-- Data for Name: sops; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sops (id, tenant_id, external_id, sop_number, title, department, source_system, is_active, current_version_id, created_at, updated_at) FROM stdin;
a73ff058-d807-4f59-bcd5-2e72269c0f95	11111111-1111-1111-1111-111111111111	\N	SOP-95BA293A	Untitled SOP	Quality	\N	t	b67aa40a-3291-4ec4-9453-bcefb8043cbe	2026-04-08 18:38:52.318306	2026-04-08 18:38:52.318306
\.


--
-- Data for Name: source_references; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.source_references (id, tenant_id, entity_type, entity_id, reference_type, reference_label, reference_value, metadata_json, created_at) FROM stdin;
\.


--
-- Name: audit_decision_links audit_decision_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_decision_links
    ADD CONSTRAINT audit_decision_links_pkey PRIMARY KEY (id);


--
-- Name: audit_findings audit_findings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_findings
    ADD CONSTRAINT audit_findings_pkey PRIMARY KEY (id);


--
-- Name: capa_audit_links capa_audit_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capa_audit_links
    ADD CONSTRAINT capa_audit_links_pkey PRIMARY KEY (id);


--
-- Name: capas capas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capas
    ADD CONSTRAINT capas_pkey PRIMARY KEY (id);


--
-- Name: decision_sop_links decision_sop_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_pkey PRIMARY KEY (id);


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


--
-- Name: deviation_capa_links deviation_capa_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deviation_capa_links
    ADD CONSTRAINT deviation_capa_links_pkey PRIMARY KEY (id);


--
-- Name: deviations deviations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deviations
    ADD CONSTRAINT deviations_pkey PRIMARY KEY (id);


--
-- Name: document_versions document_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: knowledge_chunks knowledge_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT knowledge_chunks_pkey PRIMARY KEY (id);


--
-- Name: lifecycle_configs lifecycle_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lifecycle_configs
    ADD CONSTRAINT lifecycle_configs_pkey PRIMARY KEY (id);


--
-- Name: sop_deviation_links sop_deviation_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sop_deviation_links
    ADD CONSTRAINT sop_deviation_links_pkey PRIMARY KEY (id);


--
-- Name: sop_versions sop_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sop_versions
    ADD CONSTRAINT sop_versions_pkey PRIMARY KEY (id);


--
-- Name: sops sops_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sops
    ADD CONSTRAINT sops_pkey PRIMARY KEY (id);


--
-- Name: source_references source_references_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.source_references
    ADD CONSTRAINT source_references_pkey PRIMARY KEY (id);


--
-- Name: idx_document_versions_document_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_document_versions_document_id ON public.document_versions USING btree (document_id);


--
-- Name: idx_document_versions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_document_versions_status ON public.document_versions USING btree (status);


--
-- Name: idx_documents_profile; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_profile ON public.documents USING btree (profile);


--
-- Name: audit_decision_links audit_decision_links_audit_finding_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_decision_links
    ADD CONSTRAINT audit_decision_links_audit_finding_id_fkey FOREIGN KEY (audit_finding_id) REFERENCES public.audit_findings(id);


--
-- Name: audit_decision_links audit_decision_links_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_decision_links
    ADD CONSTRAINT audit_decision_links_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES public.decisions(id);


--
-- Name: capa_audit_links capa_audit_links_audit_finding_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capa_audit_links
    ADD CONSTRAINT capa_audit_links_audit_finding_id_fkey FOREIGN KEY (audit_finding_id) REFERENCES public.audit_findings(id);


--
-- Name: capa_audit_links capa_audit_links_capa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capa_audit_links
    ADD CONSTRAINT capa_audit_links_capa_id_fkey FOREIGN KEY (capa_id) REFERENCES public.capas(id);


--
-- Name: decision_sop_links decision_sop_links_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES public.decisions(id);


--
-- Name: decision_sop_links decision_sop_links_sop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_sop_id_fkey FOREIGN KEY (sop_id) REFERENCES public.sops(id);


--
-- Name: decision_sop_links decision_sop_links_sop_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_sop_version_id_fkey FOREIGN KEY (sop_version_id) REFERENCES public.sop_versions(id);


--
-- Name: deviation_capa_links deviation_capa_links_capa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deviation_capa_links
    ADD CONSTRAINT deviation_capa_links_capa_id_fkey FOREIGN KEY (capa_id) REFERENCES public.capas(id);


--
-- Name: deviation_capa_links deviation_capa_links_deviation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deviation_capa_links
    ADD CONSTRAINT deviation_capa_links_deviation_id_fkey FOREIGN KEY (deviation_id) REFERENCES public.deviations(id);


--
-- Name: document_versions document_versions_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: documents fk_current_version; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_current_version FOREIGN KEY (current_version_id) REFERENCES public.document_versions(id) ON DELETE SET NULL;


--
-- Name: sop_deviation_links sop_deviation_links_deviation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sop_deviation_links
    ADD CONSTRAINT sop_deviation_links_deviation_id_fkey FOREIGN KEY (deviation_id) REFERENCES public.deviations(id);


--
-- Name: sop_deviation_links sop_deviation_links_sop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sop_deviation_links
    ADD CONSTRAINT sop_deviation_links_sop_id_fkey FOREIGN KEY (sop_id) REFERENCES public.sops(id);


--
-- Name: sop_versions sop_versions_sop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sop_versions
    ADD CONSTRAINT sop_versions_sop_id_fkey FOREIGN KEY (sop_id) REFERENCES public.sops(id) ON DELETE CASCADE;


--
-- Name: sop_versions sop_versions_superseded_by_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sop_versions
    ADD CONSTRAINT sop_versions_superseded_by_version_id_fkey FOREIGN KEY (superseded_by_version_id) REFERENCES public.sop_versions(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO editor_user;


--
-- Name: TABLE audit_decision_links; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.audit_decision_links TO editor_user;


--
-- Name: TABLE audit_findings; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.audit_findings TO editor_user;


--
-- Name: TABLE capa_audit_links; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.capa_audit_links TO editor_user;


--
-- Name: TABLE capas; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.capas TO editor_user;


--
-- Name: TABLE decision_sop_links; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.decision_sop_links TO editor_user;


--
-- Name: TABLE decisions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.decisions TO editor_user;


--
-- Name: TABLE deviation_capa_links; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.deviation_capa_links TO editor_user;


--
-- Name: TABLE deviations; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.deviations TO editor_user;


--
-- Name: TABLE document_versions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.document_versions TO editor_user;


--
-- Name: TABLE documents; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.documents TO editor_user;


--
-- Name: TABLE knowledge_chunks; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.knowledge_chunks TO editor_user;


--
-- Name: TABLE lifecycle_configs; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.lifecycle_configs TO editor_user;


--
-- Name: TABLE sop_deviation_links; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.sop_deviation_links TO editor_user;


--
-- Name: TABLE sop_versions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.sop_versions TO editor_user;


--
-- Name: TABLE sops; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.sops TO editor_user;


--
-- Name: TABLE source_references; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.source_references TO editor_user;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO editor_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO editor_user;


--
-- PostgreSQL database dump complete
--

\unrestrict cX4FmOBZFfBZnulpWkxyvUs9HFmqcsILCMBrrVZb1vf7WbEEkQqFTkSSeMr39Ap

