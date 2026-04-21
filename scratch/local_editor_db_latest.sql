--
-- PostgreSQL database dump
--

\restrict idIosmj1EihkJpMb8aJHAKRwKj4G842AZ8cfuNxYEzRxAdI3gNQ4CdyzRYaNW2v

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
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_action_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_action_logs (
    id uuid NOT NULL,
    user_id uuid,
    action character varying(50) NOT NULL,
    sop_title character varying(255),
    section_name character varying(255),
    section_type character varying(100),
    original_text text NOT NULL,
    suggested_text text NOT NULL,
    explanation text,
    structured_data json,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: ai_link_suggestions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_link_suggestions (
    id uuid NOT NULL,
    source_entity_type character varying(50) NOT NULL,
    source_entity_id uuid NOT NULL,
    target_entity_type character varying(50) NOT NULL,
    target_entity_id uuid NOT NULL,
    suggested_link_type character varying(50) NOT NULL,
    score double precision NOT NULL,
    reason text,
    status character varying(30) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    approved_by character varying(255),
    approved_at timestamp without time zone
);


--
-- Name: audit_decision_links; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: audit_findings; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: capa_audit_links; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: capas; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    citations json,
    retrieval_metadata json,
    metadata_snapshot json,
    audit_log_snapshot json,
    action_metadata json,
    category_filter character varying(100),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    title character varying(500),
    collection_name character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    is_active boolean
);


--
-- Name: decision_sop_links; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: decisions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: deviation_capa_links; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: deviations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: document_versions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    title character varying(255) NOT NULL,
    profile character varying(50) DEFAULT 'sop'::character varying NOT NULL,
    current_version_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: embedding_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.embedding_jobs (
    id uuid NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id uuid NOT NULL,
    version_id uuid,
    job_type character varying(50) NOT NULL,
    status character varying(30) NOT NULL,
    error_message text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    started_at timestamp without time zone,
    finished_at timestamp without time zone
);


--
-- Name: knowledge_chunks; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: lifecycle_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lifecycle_configs (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    entity_type character varying(50) NOT NULL,
    config_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: sop_deviation_links; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: sop_versions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: sops; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: source_references; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    last_login timestamp with time zone
);


--
-- Data for Name: ai_action_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_action_logs (id, user_id, action, sop_title, section_name, section_type, original_text, suggested_text, explanation, structured_data, created_at) FROM stdin;
3ae62030-910d-4411-9eb6-25b3a10560f5	d81bf2d5-bbcb-4d3a-a3fa-161eae3b27fe	improve	Test SOP	Procedure	procedure	Do the procedure.	<h3>Improved Version</h3><p>Do the procedure. Ensure the responsible role verifies completion, records the result, and escalates any deviation through the QA workflow.</p><h3>Reason for Improvement</h3><p>The wording is more explicit about ownership, documentation, and deviation handling, which makes the SOP section more audit-ready.</p>	Selected content was strengthened for clarity and QA control.	{"improved_version": "Do the procedure. Ensure the responsible role verifies completion, records the result, and escalates any deviation through the QA workflow.", "reason_for_improvement": "The wording is more explicit about ownership, documentation, and deviation handling, which makes the SOP section more audit-ready.", "prompt_used": "Improve the selected SOP text while preserving intent. Return only an Improved version and a Reason for improvement. Context: SOP title: Test SOP | Section name: Procedure | Section type: procedure. Text: Do the procedure."}	2026-04-20 19:20:03.103989+05
\.


--
-- Data for Name: ai_link_suggestions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_link_suggestions (id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, suggested_link_type, score, reason, status, created_at, approved_by, approved_at) FROM stdin;
7c485782-84dc-4141-a94a-6a7898b090fc	sop	78e490ca-620b-42a0-bbba-c000a4e183b1	deviation	33333333-3333-3333-3333-333333333331	sop-deviation	0.91	manual test accept	accepted	2026-04-21 18:13:42.724062	\N	2026-04-21 13:13:42.856336
9f839b28-eb8f-4d9f-8c32-e57579966bd7	sop	78e490ca-620b-42a0-bbba-c000a4e183b1	deviation	33333333-3333-3333-3333-333333333332	sop-deviation	0.88	manual test reject	rejected	2026-04-21 18:13:42.978379	\N	2026-04-21 13:13:43.020115
6fcf7ccc-607a-440b-b92e-3309fd70ec00	deviation	38d8b8f8-d54c-4ad7-aeb6-72a7f35a942a	capa	18cc74c8-6fb3-4a03-9c57-eacebb8b1604	deviation-capa	0.9	manual chain test	accepted	2026-04-21 18:15:23.032916	\N	2026-04-21 13:15:23.116818
892cce09-2c07-4b8d-9549-ec5f5442b952	sop	78e490ca-620b-42a0-bbba-c000a4e183b1	deviation	33333333-3333-3333-3333-333333333332	sop-deviation	0.9	e2e accept test	accepted	2026-04-21 18:50:27.529017	\N	2026-04-21 13:50:27.574928
3fa45595-f428-497e-9731-12f3026a6b4c	sop	78e490ca-620b-42a0-bbba-c000a4e183b1	deviation	33333333-3333-3333-3333-333333333333	sop-deviation	0.85	e2e reject test	rejected	2026-04-21 18:50:27.584739	\N	2026-04-21 13:50:27.628904
9a6ccbce-fce9-4752-9422-220d18f4c5d3	deviation	5d3abd48-7dfa-4af9-b0c2-c892451c7f54	capa	44444444-4444-4444-4444-444444444441	deviation-capa	0.6801127	Semantic similarity (BAAI/bge-m3) score 0.680 exceeded threshold 0.62.	pending	2026-04-21 18:51:40.889053	\N	\N
898c9e7a-06c2-4745-9eab-db1f2bc8cc0e	sop	11111111-1111-1111-1111-111111111111	deviation	5d3abd48-7dfa-4af9-b0c2-c892451c7f54	sop-deviation	0.7483697	Semantic similarity (BAAI/bge-m3) score 0.748 exceeded threshold 0.63.	pending	2026-04-21 18:51:57.078735	\N	\N
\.


--
-- Data for Name: audit_decision_links; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_decision_links (id, tenant_id, audit_finding_id, decision_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
e3620b51-74d8-4e60-a1a9-a48781584dbc	11111111-1111-1111-1111-111111111111	892a68fc-8d74-44a0-8de8-21b9a1e7d34c	eda497e7-eb79-4c85-a183-5c8b1a372fdb	\N	\N	\N	2026-04-20 17:41:43.650757	\N
d7f57de3-b0f5-4a9d-80e8-eeb5ccd82961	11111111-1111-1111-1111-111111111111	d4bdbf48-4b3e-42a4-b8ba-4817b96b5410	f63d4bbf-7f71-4c89-bae8-31e5d6c56db1	\N	\N	\N	2026-04-20 17:41:43.650757	\N
cfcb07da-d24e-43c9-abff-28e8274357c2	11111111-1111-1111-1111-111111111111	0e76f838-3888-4087-8a65-7c2b91b881a7	0c9e52d4-df77-4c13-8150-dfd636d9626e	\N	\N	\N	2026-04-20 17:41:43.650757	\N
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1	00000000-0000-0000-0000-000000000001	44444444-4444-4444-4444-444444444441	55555555-5555-5555-5555-555555555551	Decision created in response to audit concern	0.96	{}	2026-04-21 16:39:58.106846	QA approval rule addresses the audit finding.
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2	00000000-0000-0000-0000-000000000001	44444444-4444-4444-4444-444444444442	55555555-5555-5555-5555-555555555552	Trend decision linked to audit observation	0.96	{}	2026-04-21 16:39:58.106846	Repeat excursions now have explicit trigger rule.
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3	00000000-0000-0000-0000-000000000001	44444444-4444-4444-4444-444444444443	55555555-5555-5555-5555-555555555553	Utility decision linked to audit observation	0.96	{}	2026-04-21 16:39:58.106846	QA release restriction decision addresses utility finding.
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa12	22222222-2222-2222-2222-222222222222	55555555-5555-5555-5555-555555555551	66666666-6666-6666-6666-666666666671	Decision created from escalation audit finding	0.96	{}	2026-04-21 16:54:51.569732	QA approval rule addresses escalation weakness.
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa22	22222222-2222-2222-2222-222222222222	55555555-5555-5555-5555-555555555552	66666666-6666-6666-6666-666666666672	Decision created from documentation audit finding	0.96	{}	2026-04-21 16:54:51.569732	Mandatory evidence decision addresses documentation gap.
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4	22222222-2222-2222-2222-222222222222	55555555-5555-5555-5555-555555555553	66666666-6666-6666-6666-666666666673	Decision created from repeat incident audit finding	0.96	{}	2026-04-21 16:54:51.569732	CAPA trigger decision addresses repeat trend gap.
\.


--
-- Data for Name: audit_findings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_findings (id, tenant_id, external_id, audit_number, finding_number, authority, site, audit_date, question_text, finding_text, response_text, acceptance_status, source_system, created_at, updated_at) FROM stdin;
0e76f838-3888-4087-8a65-7c2b91b881a7	11111111-1111-1111-1111-111111111111	AUD-EXT-703	AUD-2026-703	AF-703	Internal QA	\N	\N	How is utility monitoring failure managed for aseptic support systems?	Compressed air monitoring failures were not consistently tied to documented operational release restrictions.	\N	pending	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
892a68fc-8d74-44a0-8de8-21b9a1e7d34c	11111111-1111-1111-1111-111111111111	AUD-EXT-701	AUD-2026-701	AF-701	Internal QA	\N	\N	How are environmental monitoring excursions investigated and closed?	Excursion investigations did not consistently document immediate containment and batch impact assessment.	\N	pending	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
d4bdbf48-4b3e-42a4-b8ba-4817b96b5410	11111111-1111-1111-1111-111111111111	AUD-EXT-702	AUD-2026-702	AF-702	Internal QA	\N	\N	How is repeat excursion trend escalation controlled?	Repeat excursion trend review was not formally linked to preventive CAPA initiation criteria.	\N	pending	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
44444444-4444-4444-4444-444444444441	00000000-0000-0000-0000-000000000001	AUD-EXT-701	AUD-2026-701	AF-701	Internal QA	Plant-01	2026-04-21 16:39:58.106846	How are environmental monitoring excursions investigated and closed?	Containment and impact assessment were not documented consistently.	QA committed to strengthen excursion handling and containment documentation.	pending	manual_insert	2026-04-21 16:39:58.106846	2026-04-21 16:39:58.106846
44444444-4444-4444-4444-444444444442	00000000-0000-0000-0000-000000000001	AUD-EXT-702	AUD-2026-702	AF-702	Internal QA	Plant-01	2026-04-21 16:39:58.106846	How is repeat excursion trend escalation controlled?	Repeat excursion trend review was not formally linked to preventive CAPA criteria.	Trending and escalation criteria will be embedded in SOP.	pending	manual_insert	2026-04-21 16:39:58.106846	2026-04-21 16:39:58.106846
44444444-4444-4444-4444-444444444443	00000000-0000-0000-0000-000000000001	AUD-EXT-703	AUD-2026-703	AF-703	Internal QA	Plant-01	2026-04-21 16:39:58.106846	How are utility monitoring failures managed?	Compressed air failures were not consistently tied to release restrictions.	Utility failure response will be linked to QA release decision steps.	pending	manual_insert	2026-04-21 16:39:58.106846	2026-04-21 16:39:58.106846
55555555-5555-5555-5555-555555555551	22222222-2222-2222-2222-222222222222	AUD-EXT-801	AUD-2026-801	AF-801	Internal QA	Plant-02	2026-04-21 16:54:51.569732	How are incidents escalated from the packaging line?	Packaging incidents were not escalated to QA within the required timeline.	Escalation controls will be strengthened and monitored.	pending	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
55555555-5555-5555-5555-555555555552	22222222-2222-2222-2222-222222222222	AUD-EXT-802	AUD-2026-802	AF-802	Internal QA	Plant-02	2026-04-21 16:54:51.569732	How is investigation evidence controlled?	Investigation files lacked mandatory supporting attachments.	Checklist controls will be revised to enforce documentation completeness.	pending	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
55555555-5555-5555-5555-555555555553	22222222-2222-2222-2222-222222222222	AUD-EXT-803	AUD-2026-803	AF-803	Internal QA	Plant-02	2026-04-21 16:54:51.569732	How are repeat compliance incidents escalated?	Repeat incidents were not always linked to formal CAPA initiation.	Trend escalation criteria will be defined and enforced.	pending	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
\.


--
-- Data for Name: capa_audit_links; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.capa_audit_links (id, tenant_id, capa_id, audit_finding_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
61d8cf28-e608-4119-a030-8ec450dec380	11111111-1111-1111-1111-111111111111	9909aa05-ad75-450a-8016-a167222e1aa7	892a68fc-8d74-44a0-8de8-21b9a1e7d34c	\N	\N	\N	2026-04-20 17:41:43.650757	\N
9d68cdd3-d4bd-4af2-9c42-26202ab617c5	11111111-1111-1111-1111-111111111111	18cc74c8-6fb3-4a03-9c57-eacebb8b1604	d4bdbf48-4b3e-42a4-b8ba-4817b96b5410	\N	\N	\N	2026-04-20 17:41:43.650757	\N
317557c7-9462-4bf0-b87e-d5ddadd2ad4f	11111111-1111-1111-1111-111111111111	26c9babb-19e9-442a-a514-57f38e48c760	0e76f838-3888-4087-8a65-7c2b91b881a7	\N	\N	\N	2026-04-20 17:41:43.650757	\N
99999999-9999-9999-9999-999999999991	22222222-2222-2222-2222-222222222222	44444444-4444-4444-4444-444444444441	55555555-5555-5555-5555-555555555551	Audit supports escalation CAPA	0.97	{}	2026-04-21 16:54:51.569732	Audit identified weak escalation control.
99999999-9999-9999-9999-999999999992	22222222-2222-2222-2222-222222222222	44444444-4444-4444-4444-444444444442	55555555-5555-5555-5555-555555555552	Audit supports documentation CAPA	0.97	{}	2026-04-21 16:54:51.569732	Audit identified missing supporting evidence.
99999999-9999-9999-9999-999999999993	22222222-2222-2222-2222-222222222222	44444444-4444-4444-4444-444444444443	55555555-5555-5555-5555-555555555553	Audit supports repeat incident CAPA	0.97	{}	2026-04-21 16:54:51.569732	Audit highlighted missing trend escalation.
\.


--
-- Data for Name: capas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.capas (id, tenant_id, external_id, capa_number, title, external_status, action_type, action_text, effectiveness_text, owner_name, due_date, effectiveness_status, source_system, created_at, updated_at) FROM stdin;
18cc74c8-6fb3-4a03-9c57-eacebb8b1604	11111111-1111-1111-1111-111111111111	CAPA-EXT-602	CAPA-2026-602	Balance corridor airflow and review material movement controls	planned	Preventive	Perform HVAC airflow rebalance study and restrict non-essential movement during pre-operation sterile staging.	\N	Engineering Manager	\N	\N	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
26c9babb-19e9-442a-a514-57f38e48c760	11111111-1111-1111-1111-111111111111	CAPA-EXT-603	CAPA-2026-603	Tighten compressed air filter maintenance and release verification	open	Corrective	Revise preventive maintenance frequency and require QA review of utility monitoring before operational release.	\N	Engineering Manager	\N	\N	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
9909aa05-ad75-450a-8016-a167222e1aa7	11111111-1111-1111-1111-111111111111	CAPA-EXT-601	CAPA-2026-601	Revise transfer disinfection controls for movable equipment	in_progress	Corrective	Update SOP-controlled transfer checklist to include wheel disinfection verification before classified area entry.	\N	Production Supervisor	\N	\N	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
44444444-4444-4444-4444-444444444441	22222222-2222-2222-2222-222222222222	CAPA-EXT-701	CAPA-2026-701	Strengthen packaging incident escalation workflow	in_progress	Corrective	Update packaging incident escalation workflow and require same-shift QA notification.	No late escalations for 60 days after implementation.	Packaging Supervisor	2026-05-01 16:54:51.569732	pending	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
44444444-4444-4444-4444-444444444442	22222222-2222-2222-2222-222222222222	CAPA-EXT-702	CAPA-2026-702	Revise investigation evidence checklist	planned	Preventive	Revise investigation checklist to require mandatory evidence attachments before submission.	All investigations contain supporting evidence across 3 review cycles.	QA Documentation Lead	2026-05-03 16:54:51.569732	pending	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
44444444-4444-4444-4444-444444444443	22222222-2222-2222-2222-222222222222	CAPA-EXT-703	CAPA-2026-703	Define trend-based CAPA escalation rule	open	Corrective	Implement a rule that repeat compliance incidents must trigger CAPA initiation.	No repeat compliance incidents remain without CAPA review.	Site Compliance Manager	2026-05-05 16:54:51.569732	pending	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_messages (id, session_id, role, content, citations, retrieval_metadata, metadata_snapshot, audit_log_snapshot, action_metadata, category_filter, created_at) FROM stdin;
d6a9b66c-3ff2-4781-8e47-3f927aba8491	0e644f46-ac95-45e4-baa3-4ed9e2c7bf75	user	Test message from e2e	null	null	null	null	null	\N	2026-04-20 19:20:03.06721+05
\.


--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_sessions (id, user_id, title, collection_name, created_at, updated_at, is_active) FROM stdin;
0e644f46-ac95-45e4-baa3-4ed9e2c7bf75	d81bf2d5-bbcb-4d3a-a3fa-161eae3b27fe	E2E Session	docs_sops	2026-04-20 19:20:02.959533+05	\N	t
\.


--
-- Data for Name: decision_sop_links; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.decision_sop_links (id, tenant_id, decision_id, sop_id, sop_version_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
\.


--
-- Data for Name: decisions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.decisions (id, tenant_id, external_id, decision_number, decision_type, title, decision_statement, rationale_text, risk_assessment_text, alternatives_text, final_conclusion, decision_date, decided_by_role, source_system, created_at, updated_at) FROM stdin;
0c9e52d4-df77-4c13-8150-dfd636d9626e	11111111-1111-1111-1111-111111111111	DEC-EXT-803	DEC-2026-803	\N	Utility monitoring failures require documented release restriction review	Any failed microbiological utility monitoring result must trigger documented QA review before further operational release.	\N	\N	\N	\N	\N	\N	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
eda497e7-eb79-4c85-a183-5c8b1a372fdb	11111111-1111-1111-1111-111111111111	DEC-EXT-801	DEC-2026-801	\N	Major EM excursions require QA approval before closure	No major environmental monitoring excursion may be closed without documented QA approval of investigation, impact assessment, and CAPA status.	\N	\N	\N	\N	\N	\N	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
f63d4bbf-7f71-4c89-bae8-31e5d6c56db1	11111111-1111-1111-1111-111111111111	DEC-EXT-802	DEC-2026-802	\N	Repeat monitoring excursions must trigger preventive CAPA	Two or more repeat excursions in the same classified area within a defined review window require preventive CAPA initiation.	\N	\N	\N	\N	\N	\N	import	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
55555555-5555-5555-5555-555555555551	00000000-0000-0000-0000-000000000001	DEC-EXT-801	DEC-2026-801	Approval Rule	Major EM excursions require QA approval	No major environmental monitoring excursion may be closed without QA approval.	Major excursions can affect contamination control and GMP compliance.	High contamination and compliance risk.	Area supervisor closure only was considered but rejected.	QA approval remains mandatory for major excursion closure.	2026-04-21 16:39:58.106846	Qualified Person	manual_insert	2026-04-21 16:39:58.106846	2026-04-21 16:39:58.106846
55555555-5555-5555-5555-555555555552	00000000-0000-0000-0000-000000000001	DEC-EXT-802	DEC-2026-802	Trend Rule	Repeat excursions must trigger preventive CAPA	Two or more repeat excursions in same area require preventive CAPA.	Repeat excursions indicate systemic weakness.	Medium to high process control risk if trends are not escalated.	Case-by-case review without trigger criteria was rejected.	Repeat excursion trigger is mandatory.	2026-04-21 16:39:58.106846	QA Head	manual_insert	2026-04-21 16:39:58.106846	2026-04-21 16:39:58.106846
55555555-5555-5555-5555-555555555553	00000000-0000-0000-0000-000000000001	DEC-EXT-803	DEC-2026-803	Utility Rule	Utility failures require QA release restriction review	Any failed microbiological utility result must trigger QA review before release.	Utilities affect aseptic support reliability.	High sterility assurance risk if not formally reviewed.	Engineering-only disposition was rejected.	QA-controlled release restriction review is required.	2026-04-21 16:39:58.106846	Site Compliance Manager	manual_insert	2026-04-21 16:39:58.106846	2026-04-21 16:39:58.106846
66666666-6666-6666-6666-666666666671	22222222-2222-2222-2222-222222222222	DEC-EXT-901	DEC-2026-901	Approval Rule	Major incident escalations require QA approval	No major incident may be closed without QA approval of escalation and investigation.	Major incidents can affect compliance and quality oversight.	High compliance risk if closure occurs without QA review.	Supervisor-only closure was rejected.	QA approval remains mandatory.	2026-04-21 16:54:51.569732	Qualified Person	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
66666666-6666-6666-6666-666666666672	22222222-2222-2222-2222-222222222222	DEC-EXT-902	DEC-2026-902	Documentation Rule	Investigations without evidence cannot be finalized	No investigation may be finalized if required supporting evidence is missing.	Incomplete evidence weakens audit readiness and traceability.	Moderate documentation integrity risk.	Retrospective evidence completion without hold was rejected.	Evidence is mandatory before finalization.	2026-04-21 16:54:51.569732	QA Head	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
66666666-6666-6666-6666-666666666673	22222222-2222-2222-2222-222222222222	DEC-EXT-903	DEC-2026-903	Trend Rule	Repeat compliance incidents must trigger CAPA	Any repeated compliance incident must be escalated to CAPA review.	Repeat incidents indicate systemic failure in controls.	High compliance risk if trends are not escalated.	Case-by-case handling without trigger criteria was rejected.	CAPA trigger is mandatory for repeat incidents.	2026-04-21 16:54:51.569732	Site Compliance Manager	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
\.


--
-- Data for Name: deviation_capa_links; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.deviation_capa_links (id, tenant_id, deviation_id, capa_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
48c20100-0ce9-45da-b1c7-c74dc82c4ffa	11111111-1111-1111-1111-111111111111	bd68d770-d560-4cb6-8daa-da85437f5a14	9909aa05-ad75-450a-8016-a167222e1aa7	\N	\N	\N	2026-04-20 17:41:43.650757	\N
035f5d14-3f4f-4a06-bc84-3d308a886200	11111111-1111-1111-1111-111111111111	ca419055-af9e-4574-a31f-2306023053c6	18cc74c8-6fb3-4a03-9c57-eacebb8b1604	\N	\N	\N	2026-04-20 17:41:43.650757	\N
e3087e40-d0de-4561-b014-aff05fa77cfd	11111111-1111-1111-1111-111111111111	38d8b8f8-d54c-4ad7-aeb6-72a7f35a942a	26c9babb-19e9-442a-a514-57f38e48c760	\N	\N	\N	2026-04-20 17:41:43.650757	\N
88888888-8888-8888-8888-888888888881	22222222-2222-2222-2222-222222222222	33333333-3333-3333-3333-333333333331	44444444-4444-4444-4444-444444444441	Corrective CAPA for delayed escalation	0.98	{}	2026-04-21 16:54:51.569732	Workflow strengthening addresses escalation delay.
88888888-8888-8888-8888-888888888882	22222222-2222-2222-2222-222222222222	33333333-3333-3333-3333-333333333332	44444444-4444-4444-4444-444444444442	Preventive CAPA for incomplete investigation records	0.98	{}	2026-04-21 16:54:51.569732	Checklist update addresses evidence gap.
88888888-8888-8888-8888-888888888883	22222222-2222-2222-2222-222222222222	33333333-3333-3333-3333-333333333333	44444444-4444-4444-4444-444444444443	Corrective CAPA for repeat incident trend escalation	0.98	{}	2026-04-21 16:54:51.569732	Trend rule addresses systemic escalation failure.
a41e20b1-88de-4179-af3b-d7d2a4ed5081	11111111-1111-1111-1111-111111111111	38d8b8f8-d54c-4ad7-aeb6-72a7f35a942a	18cc74c8-6fb3-4a03-9c57-eacebb8b1604	ai_suggestion	0.9	\N	2026-04-21 18:15:23.108283	manual chain test
\.


--
-- Data for Name: deviations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.deviations (id, tenant_id, external_id, deviation_number, title, category, site, product_line, external_status, description_text, root_cause_text, impact_level, source_system, event_date, created_at, updated_at) FROM stdin;
38d8b8f8-d54c-4ad7-aeb6-72a7f35a942a	11111111-1111-1111-1111-111111111111	DEV-EXT-503	DEV-2026-503	Compressed air sampling result exceeded microbiological acceptance criteria	Utility Monitoring	Plant-01	Injectables	open	Compressed air point used in aseptic support operation failed microbiological acceptance criteria during scheduled monitoring.	Filter replacement interval may not have been followed as per maintenance schedule.	critical	import	\N	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
bd68d770-d560-4cb6-8daa-da85437f5a14	11111111-1111-1111-1111-111111111111	DEV-EXT-501	DEV-2026-501	Grade C viable count exceeded action limit during morning monitoring	Environmental Monitoring	Plant-01	Sterile Filling	open	Routine environmental monitoring in Grade C background area showed viable count above action limit during pre-operation sampling.	Initial review suggests incomplete disinfection of material transfer trolley wheels before area entry.	major	import	\N	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
ca419055-af9e-4574-a31f-2306023053c6	11111111-1111-1111-1111-111111111111	DEV-EXT-502	DEV-2026-502	Repeated settle plate excursion in sterile staging corridor	Environmental Monitoring	Plant-01	Sterile Filling	under_investigation	Two settle plates from the sterile staging corridor showed repeated excursion above alert limit over three consecutive monitoring intervals.	Possible airflow imbalance combined with high material movement frequency in staging corridor.	major	import	\N	2026-04-20 17:30:34.041824	2026-04-20 17:41:43.650757
33333333-3333-3333-3333-333333333331	22222222-2222-2222-2222-222222222222	DEV-EXT-601	DEV-2026-601	Delayed escalation of incident from packaging line	Escalation	Plant-02	Packaging	open	An operational incident on the packaging line was not escalated within the required timeframe.	Supervisor notification workflow was not followed correctly.	major	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
33333333-3333-3333-3333-333333333332	22222222-2222-2222-2222-222222222222	DEV-EXT-602	DEV-2026-602	Incident investigation missing supporting evidence	Documentation	Plant-02	Manufacturing	under_investigation	Investigation was opened but key supporting evidence was not attached.	Investigation checklist did not enforce evidence attachment.	minor	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
33333333-3333-3333-3333-333333333333	22222222-2222-2222-2222-222222222222	DEV-EXT-603	DEV-2026-603	Repeat compliance incident not escalated to CAPA	Compliance	Plant-02	Warehouse	open	A repeat compliance-related incident occurred but was not escalated to formal CAPA review.	Trend escalation criteria were not clearly defined in the process.	critical	manual_insert	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732	2026-04-21 16:54:51.569732
3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	11111111-1111-1111-1111-111111111111	\N	DEV-PERF-002	Perf Test Dev 2	Process	\N	\N	\N	test	test	low	\N	\N	2026-04-21 18:14:41.006253	2026-04-21 18:14:41.006253
5d3abd48-7dfa-4af9-b0c2-c892451c7f54	11111111-1111-1111-1111-111111111111	\N	DEV-SIM-001	Incident escalation process deviation	Process	\N	\N	\N	incident reporting escalation investigation qa closure capa assignment compliance traceability	lack of controlled escalation process and QA review	high	\N	\N	2026-04-21 18:51:19.852333	2026-04-21 18:51:19.852333
\.


--
-- Data for Name: document_versions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.document_versions (id, document_id, version_number, doc_json, change_summary, status, metadata_json, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documents (id, title, profile, current_version_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: embedding_jobs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.embedding_jobs (id, entity_type, entity_id, version_id, job_type, status, error_message, created_at, started_at, finished_at) FROM stdin;
eaecde92-ea0c-4e82-8a82-2c6ef0e07455	sop	78e490ca-620b-42a0-bbba-c000a4e183b1	e492e27b-b401-442d-91cf-50e5d358665b	manual_reindex	running	\N	2026-04-21 18:12:56.096915	2026-04-21 13:12:56.216686	\N
598019c2-978b-4d16-94d0-f3be82fe2f4e	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	entity_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:14:41.023057	2026-04-21 13:14:41.045316	2026-04-21 13:26:02.462575
203b4d25-c4a6-4cbc-af47-efed331dd09f	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:38:18.282331	2026-04-21 13:38:18.404761	2026-04-21 13:38:20.799394
b87dec72-e677-4fdd-8ff7-a296d8f6efc5	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:38:18.204896	2026-04-21 13:38:18.271988	2026-04-21 13:38:20.805908
34d50b28-d340-4e42-b9bd-2f1d1b6e6d2f	capa	44444444-4444-4444-4444-444444444441	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:38:18.422029	2026-04-21 13:38:18.470068	2026-04-21 13:38:20.948235
ecde4009-5a3a-4dfd-be0c-5e0636784bb6	audit_finding	55555555-5555-5555-5555-555555555551	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:38:18.484963	2026-04-21 13:38:18.623835	2026-04-21 13:38:21.014302
2c6fca88-6c34-4f44-8e41-886b704a0424	decision	66666666-6666-6666-6666-666666666671	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:38:18.652351	2026-04-21 13:38:18.738943	2026-04-21 13:38:21.064105
6a3c15a2-6a26-4dab-85d3-1d07b6bb8a1a	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:39:32.433045	2026-04-21 13:39:32.516835	2026-04-21 13:39:33.606565
5d08126e-648f-4b93-bd78-ac87219ac196	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:39:32.523041	2026-04-21 13:39:32.582393	2026-04-21 13:39:33.702835
60675c12-27d6-42b2-adb2-be6f6a976f37	capa	44444444-4444-4444-4444-444444444441	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:39:32.589445	2026-04-21 13:39:32.612414	2026-04-21 13:39:33.806396
b467cd53-2bb6-4112-8016-9f30e961a29a	audit_finding	55555555-5555-5555-5555-555555555551	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:39:32.645002	2026-04-21 13:39:32.676629	2026-04-21 13:39:33.831656
c0a37e90-b9ba-4e22-9068-81904572f6c5	decision	66666666-6666-6666-6666-666666666671	\N	manual_reindex	failed	QDRANT_URL is not configured.	2026-04-21 18:39:32.679486	2026-04-21 13:39:32.721104	2026-04-21 13:39:33.832713
f5c6ecf6-073d-40ca-889b-627626ab4974	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:43:20.140357	2026-04-21 13:43:20.791253	2026-04-21 13:43:52.726543
ecbde79a-bb36-4a46-bbc8-176d41165129	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:44:27.931005	2026-04-21 13:44:27.959871	2026-04-21 13:44:35.631518
a9636907-bad6-42c3-9654-3d2ce611a429	capa	44444444-4444-4444-4444-444444444441	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:44:27.965589	2026-04-21 13:44:28.002612	2026-04-21 13:44:37.282585
2be8d788-aaf6-488b-b4e5-40db9015d014	audit_finding	55555555-5555-5555-5555-555555555551	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:44:28.0244	2026-04-21 13:44:28.062441	2026-04-21 13:44:37.84132
d7cf11f7-9f40-46cd-80de-d753e81123e1	decision	66666666-6666-6666-6666-666666666671	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:44:28.108092	2026-04-21 13:44:28.18078	2026-04-21 13:44:38.176683
271d7d52-5965-4e9d-95d3-5006473fd681	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:44:27.907671	2026-04-21 13:44:27.927695	2026-04-21 13:44:40.31302
de06d73f-5575-442c-9514-e4d06ee70550	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:45:52.167334	2026-04-21 13:45:52.189269	2026-04-21 13:45:59.534325
2fe96992-82ab-4601-8d05-0d7b8ac0ff01	capa	44444444-4444-4444-4444-444444444441	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:45:52.196728	2026-04-21 13:45:52.239378	2026-04-21 13:46:01.56693
94853260-bf43-4644-bea8-7b89f0974a31	audit_finding	55555555-5555-5555-5555-555555555551	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:45:52.262502	2026-04-21 13:45:52.306461	2026-04-21 13:46:01.968351
b7ea9b74-06e7-41c6-a090-9790136cba7e	decision	66666666-6666-6666-6666-666666666671	\N	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:45:52.318935	2026-04-21 13:45:52.38986	2026-04-21 13:46:02.120404
b41df46e-b453-465a-8985-2acef01125cf	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	manual_reindex	failed	'QdrantClient' object has no attribute 'search'	2026-04-21 18:45:52.097921	2026-04-21 13:45:52.162832	2026-04-21 13:46:04.86434
fa1dc8fa-bdb2-4c08-b366-bcdbd0b95ba1	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	manual_direct_test	failed	Unexpected Response: 400 (Bad Request)\nRaw response content:\nb'{"status":{"error":"Bad request: Index required but not found for \\\\"entity_type\\\\" of one of the following types: [keyword]. Help: Create an index for this key or use a different filter."},"time":0. ...'	2026-04-21 18:47:28.391983	2026-04-21 13:47:28.433747	2026-04-21 13:47:50.935806
0f57a242-b856-4494-bb9c-15c86996df9f	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	manual_direct_test_2	completed	\N	2026-04-21 18:48:37.963427	2026-04-21 13:48:38.002385	2026-04-21 13:48:55.418307
4fc83285-52e0-4a76-939c-64ab7bff7e7c	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	manual_direct_test_sop	completed	\N	2026-04-21 18:49:29.753085	2026-04-21 13:49:29.811939	2026-04-21 13:49:53.89305
065004f5-b738-47c4-adf0-001d816d4034	deviation	5d3abd48-7dfa-4af9-b0c2-c892451c7f54	\N	sim_test	completed	\N	2026-04-21 18:51:19.861345	2026-04-21 13:51:19.880771	2026-04-21 13:51:42.624556
2acb4163-4415-427d-be64-b68a37dd3db9	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	sim_test_sop	completed	\N	2026-04-21 18:51:42.721191	2026-04-21 13:51:42.737715	2026-04-21 13:52:02.555472
\.


--
-- Data for Name: knowledge_chunks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.knowledge_chunks (id, tenant_id, entity_type, entity_id, entity_version_id, chunk_type, block_id, chunk_text, chunk_order, metadata_json, created_at) FROM stdin;
62fdcace-39b2-4599-a2eb-3fcbd5447836	11111111-1111-1111-1111-111111111111	capa	44444444-4444-4444-4444-444444444441	\N	semantic_section	\N	title: Strengthen packaging incident escalation workflow\naction: Update packaging incident escalation workflow and require same-shift QA notification.\neffectiveness: No late escalations for 60 days after implementation.	0	{"entity_id": "44444444-4444-4444-4444-444444444441", "version_id": null, "chunk_index": 0, "entity_type": "capa", "section_name": "CAPA", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:45:58.371851
11dcaacd-e412-431f-b095-67ba990c951c	11111111-1111-1111-1111-111111111111	audit_finding	55555555-5555-5555-5555-555555555551	\N	semantic_section	\N	question: How are incidents escalated from the packaging line?\nfinding: Packaging incidents were not escalated to QA within the required timeline.\nresponse: Escalation controls will be strengthened and monitored.	0	{"entity_id": "55555555-5555-5555-5555-555555555551", "version_id": null, "chunk_index": 0, "entity_type": "audit_finding", "section_name": "Audit Finding", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:45:58.482089
b0384112-6461-4719-b356-0191b979e6e4	11111111-1111-1111-1111-111111111111	decision	66666666-6666-6666-6666-666666666671	\N	semantic_section	\N	title: Major incident escalations require QA approval\ndecision_statement: No major incident may be closed without QA approval of escalation and investigation.\nrationale: Major incidents can affect compliance and quality oversight.\nrisk_assessment: High compliance risk if closure occurs without QA review.\nfinal_conclusion: QA approval remains mandatory.	0	{"entity_id": "66666666-6666-6666-6666-666666666671", "version_id": null, "chunk_index": 0, "entity_type": "decision", "section_name": "Decision", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:45:58.578306
d2ba245f-21c8-4db4-a3a9-1ef3bd6fadfe	11111111-1111-1111-1111-111111111111	deviation	3b22c526-9c4a-427c-8baf-e0ab8a12b3ef	\N	semantic_section	\N	title: Perf Test Dev 2\ndescription: test\nroot_cause: test\ncategory: Process\nimpact_level: low	0	{"entity_id": "3b22c526-9c4a-427c-8baf-e0ab8a12b3ef", "version_id": null, "chunk_index": 0, "entity_type": "deviation", "section_name": "Deviation", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:48:53.718642
873d8886-7d0a-4419-b2fc-0ceee02030cf	11111111-1111-1111-1111-111111111111	deviation	5d3abd48-7dfa-4af9-b0c2-c892451c7f54	\N	semantic_section	\N	title: Incident escalation process deviation\ndescription: incident reporting escalation investigation qa closure capa assignment compliance traceability\nroot_cause: lack of controlled escalation process and QA review\ncategory: Process\nimpact_level: high	0	{"entity_id": "5d3abd48-7dfa-4af9-b0c2-c892451c7f54", "version_id": null, "chunk_index": 0, "entity_type": "deviation", "section_name": "Deviation", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:51:40.284336
ed322c8d-cd2d-4683-a607-bd4a597f2acd	11111111-1111-1111-1111-111111111111	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	semantic_section	\N	This SOP defines the controlled process for incident reporting, escalation, impact review, CAPA assignment, and final QA closure.	0	{"entity_id": "11111111-1111-1111-1111-111111111111", "version_id": "aaf18fde-363d-4df4-90dc-c9ad6c5e6f58", "chunk_index": 0, "entity_type": "sop", "section_name": "General", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:51:55.539117
fadbd7ab-92d7-488d-9635-5e6bbf758b0f	11111111-1111-1111-1111-111111111111	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	semantic_section	\N	To define a controlled and auditable process for identifying, documenting, escalating, investigating, and resolving operational incidents that may affect compliance, product quality, or traceability.	1	{"entity_id": "11111111-1111-1111-1111-111111111111", "version_id": "aaf18fde-363d-4df4-90dc-c9ad6c5e6f58", "chunk_index": 1, "entity_type": "sop", "section_name": "Purpose", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:51:55.539117
97f9253f-e576-447e-b95d-0c3bab67ec54	11111111-1111-1111-1111-111111111111	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	semantic_section	\N	This SOP applies to all manufacturing, packaging, warehouse, and QA operations where incidents, process breakdowns, or compliance events require formal escalation and corrective action.	2	{"entity_id": "11111111-1111-1111-1111-111111111111", "version_id": "aaf18fde-363d-4df4-90dc-c9ad6c5e6f58", "chunk_index": 2, "entity_type": "sop", "section_name": "Scope", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:51:55.539117
2b7246b6-0844-4990-b539-9f2a33c00856	11111111-1111-1111-1111-111111111111	sop	11111111-1111-1111-1111-111111111111	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	semantic_section	\N	Operators must report incidents immediately. Supervisors must ensure containment and escalation. QA must assess impact, review investigations, and approve closure. Functional owners must complete CAPAs on time.	3	{"entity_id": "11111111-1111-1111-1111-111111111111", "version_id": "aaf18fde-363d-4df4-90dc-c9ad6c5e6f58", "chunk_index": 3, "entity_type": "sop", "section_name": "Responsibilities", "embedding_model": "BAAI/bge-m3"}	2026-04-21 18:51:55.539117
\.


--
-- Data for Name: lifecycle_configs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.lifecycle_configs (id, tenant_id, entity_type, config_json, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sop_deviation_links; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sop_deviation_links (id, tenant_id, sop_id, deviation_id, link_reason, confidence_score, metadata_json, created_at, rationale_text) FROM stdin;
c87c8449-89dc-4d97-9036-8956e446fc72	11111111-1111-1111-1111-111111111111	78e490ca-620b-42a0-bbba-c000a4e183b1	bd68d770-d560-4cb6-8daa-da85437f5a14	\N	\N	\N	2026-04-20 17:41:43.650757	\N
5705d9fa-51c2-43b6-8788-e9aed2c4e092	11111111-1111-1111-1111-111111111111	78e490ca-620b-42a0-bbba-c000a4e183b1	ca419055-af9e-4574-a31f-2306023053c6	\N	\N	\N	2026-04-20 17:41:43.650757	\N
3dfeec7a-ab14-4d4f-a95b-bc012df7666c	11111111-1111-1111-1111-111111111111	78e490ca-620b-42a0-bbba-c000a4e183b1	38d8b8f8-d54c-4ad7-aeb6-72a7f35a942a	\N	\N	\N	2026-04-20 17:41:43.650757	\N
77777777-7777-7777-7777-777777777771	22222222-2222-2222-2222-222222222222	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333331	SOP governs escalation workflow for this incident	0.99	{}	2026-04-21 16:54:51.569732	This deviation is directly covered by the incident escalation SOP.
77777777-7777-7777-7777-777777777772	22222222-2222-2222-2222-222222222222	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333332	SOP governs investigation quality and documentation	0.99	{}	2026-04-21 16:54:51.569732	This documentation deviation falls under this SOP.
77777777-7777-7777-7777-777777777773	22222222-2222-2222-2222-222222222222	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333333	SOP governs escalation of repeat compliance incidents	0.99	{}	2026-04-21 16:54:51.569732	This repeat incident must be handled under this SOP.
1636ed32-042b-4ddf-964b-9f4376db2573	11111111-1111-1111-1111-111111111111	78e490ca-620b-42a0-bbba-c000a4e183b1	33333333-3333-3333-3333-333333333331	ai_suggestion	0.91	\N	2026-04-21 18:13:42.841022	manual test accept
3e563f6e-3855-4dc7-a238-c7da7addda8b	11111111-1111-1111-1111-111111111111	78e490ca-620b-42a0-bbba-c000a4e183b1	33333333-3333-3333-3333-333333333332	ai_suggestion	0.9	\N	2026-04-21 18:50:27.566315	e2e accept test
\.


--
-- Data for Name: sop_versions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sop_versions (id, sop_id, external_version_id, version_number, external_status, effective_date, review_date, content_json, metadata_json, created_at, updated_at, superseded_by_version_id) FROM stdin;
e492e27b-b401-442d-91cf-50e5d358665b	78e490ca-620b-42a0-bbba-c000a4e183b1	\N	1	draft	\N	\N	{"type": "doc", "content": [{"type": "heading", "attrs": {"level": 3}, "content": [{"text": "Improved Version", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This is a test procedure for environmental monitoring. Ensure the responsible role verifies completion, records the result, and escalates any deviation through the QA workflow.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 3}, "content": [{"text": "Reason for Improvement", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "The wording is more explicit about ownership, documentation, and deviation handling, which makes the SOP section more audit-ready.", "type": "text"}]}, {"type": "paragraph", "content": [{"text": " We need to document all steps clearly and ensure compliance with regulatory requirements.", "type": "text"}]}]}	{"sopStatus": "draft", "auditTrail": [], "sopMetadata": {"title": "Environmental Monitoring Excursion Handling and CAPA Control", "author": "System", "reviewer": "", "riskLevel": "Low", "department": "Quality Assurance", "documentId": "SOP-QA-010", "references": [], "reviewDate": "", "effectiveDate": "", "regulatoryReferences": []}, "versionNote": ""}	2026-04-21 13:53:56.739575	2026-04-21 16:05:50.097862	\N
66666666-6666-6666-6666-666666666661	11111111-1111-1111-1111-111111111111	SOPV-EXT-020-V1	v1.0	effective	2026-04-21 16:54:51.569732	2027-04-21 16:54:51.569732	{"type": "doc", "content": [{"type": "heading", "attrs": {"level": 1}, "content": [{"text": "Incident Escalation and Corrective Action Management", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This SOP defines the controlled process for incident reporting, escalation, impact review, CAPA assignment, and final QA closure.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Purpose", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "To define a controlled and auditable process for identifying, documenting, escalating, investigating, and resolving operational incidents that may affect compliance, product quality, or traceability.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Scope", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This SOP applies to all manufacturing, packaging, warehouse, and QA operations where incidents, process breakdowns, or compliance events require formal escalation and corrective action.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Responsibilities", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Operators must report incidents immediately. Supervisors must ensure containment and escalation. QA must assess impact, review investigations, and approve closure. Functional owners must complete CAPAs on time.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Procedure", "type": "text"}]}, {"type": "orderedList", "attrs": {"type": null, "start": 1}, "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Record the incident as soon as it is identified.", "type": "text"}]}]}, {"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Notify the supervisor and QA within the same shift.", "type": "text"}]}]}, {"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Perform preliminary impact assessment and initiate investigation.", "type": "text"}]}]}, {"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Open CAPA where repeat, systemic, or critical issues are identified.", "type": "text"}]}]}]}, {"type": "paragraph"}]}	{"sopStatus": "draft", "auditTrail": [], "sopMetadata": {"title": "Incident Escalation and Corrective Action Management", "author": "System", "reviewer": "", "riskLevel": "Low", "department": "Quality Assurance", "documentId": "SOP-QA-020", "references": [], "reviewDate": "", "effectiveDate": "", "regulatoryReferences": []}, "versionNote": ""}	2026-04-21 16:54:51.569732	2026-04-21 17:02:40.086605	\N
aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	11111111-1111-1111-1111-111111111111	\N	1	draft	\N	\N	{"type": "doc", "content": [{"type": "heading", "attrs": {"level": 1}}, {"type": "paragraph", "content": [{"text": "This SOP defines the controlled process for incident reporting, escalation, impact review, CAPA assignment, and final QA closure.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Purpose", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "To define a controlled and auditable process for identifying, documenting, escalating, investigating, and resolving operational incidents that may affect compliance, product quality, or traceability.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Scope", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "This SOP applies to all manufacturing, packaging, warehouse, and QA operations where incidents, process breakdowns, or compliance events require formal escalation and corrective action.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Responsibilities", "type": "text"}]}, {"type": "paragraph", "content": [{"text": "Operators must report incidents immediately. Supervisors must ensure containment and escalation. QA must assess impact, review investigations, and approve closure. Functional owners must complete CAPAs on time.", "type": "text"}]}, {"type": "heading", "attrs": {"level": 2}, "content": [{"text": "Procedure", "type": "text"}]}, {"type": "orderedList", "attrs": {"type": null, "start": 1}, "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Record the incident as soon as it is identified.", "type": "text"}]}]}, {"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Notify the supervisor and QA within the same shift.", "type": "text"}]}]}, {"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Perform preliminary impact assessment and initiate investigation.", "type": "text"}]}]}, {"type": "listItem", "content": [{"type": "paragraph", "content": [{"text": "Open CAPA where repeat, systemic, or critical issues are identified.", "type": "text"}]}]}]}, {"type": "paragraph"}]}	{"sopStatus": "draft", "auditTrail": [], "sopMetadata": {"title": "Incident Escalation and Corrective Action Management", "author": "System", "reviewer": "", "riskLevel": "Low", "department": "Quality Assurance", "documentId": "SOP-QA-020", "references": [], "reviewDate": "", "effectiveDate": "", "regulatoryReferences": []}, "versionNote": ""}	2026-04-21 17:03:29.697727	2026-04-21 17:03:38.395534	\N
\.


--
-- Data for Name: sops; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sops (id, tenant_id, external_id, sop_number, title, department, source_system, is_active, current_version_id, created_at, updated_at) FROM stdin;
78e490ca-620b-42a0-bbba-c000a4e183b1	11111111-1111-1111-1111-111111111111	SOP-EXT-010	SOP-QA-010	Environmental Monitoring Excursion Handling and CAPA Control	Quality Assurance	import	t	e492e27b-b401-442d-91cf-50e5d358665b	2026-04-20 17:30:34.041824	2026-04-21 13:53:56.739575
11111111-1111-1111-1111-111111111111	22222222-2222-2222-2222-222222222222	SOP-EXT-020	SOP-QA-020	Incident Escalation and Corrective Action Management	Quality Assurance	manual_insert	t	aaf18fde-363d-4df4-90dc-c9ad6c5e6f58	2026-04-21 16:54:51.569732	2026-04-21 17:03:29.785606
\.


--
-- Data for Name: source_references; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.source_references (id, tenant_id, entity_type, entity_id, reference_type, reference_label, reference_value, metadata_json, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, username, hashed_password, is_active, is_verified, role, created_at, updated_at, last_login) FROM stdin;
18a66122-c6ac-45b4-b53c-ebad56db1f39	e2e_b2b968fb@example.com	e2e_b2b968fb	$pbkdf2-sha256$29000$35szRsgZo5SSUopRqhVibA$s5rjVkXdnOsZO3pzncTiVEo/BuyWk8SudAlKxaV8HJQ	t	t	user	2026-04-20 19:19:52.202948+05	2026-04-20 19:19:52.556148+05	2026-04-20 19:19:52.61148+05
d81bf2d5-bbcb-4d3a-a3fa-161eae3b27fe	e2e_dc3b9b6c@example.com	e2e_dc3b9b6c	$pbkdf2-sha256$29000$USoFYKzV.l.rNWasNSZkLA$40LzcjKsrwuBJ1ZmwnvKvC6DgO6jCfAH/2oAep9NMvk	t	t	user	2026-04-20 19:20:02.794151+05	2026-04-20 19:20:02.898629+05	2026-04-20 19:20:02.9419+05
\.


--
-- Name: ai_action_logs ai_action_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_action_logs
    ADD CONSTRAINT ai_action_logs_pkey PRIMARY KEY (id);


--
-- Name: ai_link_suggestions ai_link_suggestions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_link_suggestions
    ADD CONSTRAINT ai_link_suggestions_pkey PRIMARY KEY (id);


--
-- Name: audit_decision_links audit_decision_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_decision_links
    ADD CONSTRAINT audit_decision_links_pkey PRIMARY KEY (id);


--
-- Name: audit_findings audit_findings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_findings
    ADD CONSTRAINT audit_findings_pkey PRIMARY KEY (id);


--
-- Name: capa_audit_links capa_audit_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capa_audit_links
    ADD CONSTRAINT capa_audit_links_pkey PRIMARY KEY (id);


--
-- Name: capas capas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capas
    ADD CONSTRAINT capas_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: decision_sop_links decision_sop_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_pkey PRIMARY KEY (id);


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


--
-- Name: deviation_capa_links deviation_capa_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deviation_capa_links
    ADD CONSTRAINT deviation_capa_links_pkey PRIMARY KEY (id);


--
-- Name: deviations deviations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deviations
    ADD CONSTRAINT deviations_pkey PRIMARY KEY (id);


--
-- Name: document_versions document_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: embedding_jobs embedding_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.embedding_jobs
    ADD CONSTRAINT embedding_jobs_pkey PRIMARY KEY (id);


--
-- Name: knowledge_chunks knowledge_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT knowledge_chunks_pkey PRIMARY KEY (id);


--
-- Name: lifecycle_configs lifecycle_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lifecycle_configs
    ADD CONSTRAINT lifecycle_configs_pkey PRIMARY KEY (id);


--
-- Name: sop_deviation_links sop_deviation_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sop_deviation_links
    ADD CONSTRAINT sop_deviation_links_pkey PRIMARY KEY (id);


--
-- Name: sop_versions sop_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sop_versions
    ADD CONSTRAINT sop_versions_pkey PRIMARY KEY (id);


--
-- Name: sops sops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sops
    ADD CONSTRAINT sops_pkey PRIMARY KEY (id);


--
-- Name: source_references source_references_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_references
    ADD CONSTRAINT source_references_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_document_versions_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_versions_document_id ON public.document_versions USING btree (document_id);


--
-- Name: idx_document_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_versions_status ON public.document_versions USING btree (status);


--
-- Name: idx_documents_profile; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_profile ON public.documents USING btree (profile);


--
-- Name: ix_ai_action_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_action_logs_action ON public.ai_action_logs USING btree (action);


--
-- Name: ix_ai_action_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_action_logs_user_id ON public.ai_action_logs USING btree (user_id);


--
-- Name: ix_ai_link_suggestions_source_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_link_suggestions_source_entity_id ON public.ai_link_suggestions USING btree (source_entity_id);


--
-- Name: ix_ai_link_suggestions_source_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_link_suggestions_source_entity_type ON public.ai_link_suggestions USING btree (source_entity_type);


--
-- Name: ix_ai_link_suggestions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_link_suggestions_status ON public.ai_link_suggestions USING btree (status);


--
-- Name: ix_ai_link_suggestions_suggested_link_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_link_suggestions_suggested_link_type ON public.ai_link_suggestions USING btree (suggested_link_type);


--
-- Name: ix_ai_link_suggestions_target_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_link_suggestions_target_entity_id ON public.ai_link_suggestions USING btree (target_entity_id);


--
-- Name: ix_ai_link_suggestions_target_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_link_suggestions_target_entity_type ON public.ai_link_suggestions USING btree (target_entity_type);


--
-- Name: ix_chat_messages_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_messages_session_id ON public.chat_messages USING btree (session_id);


--
-- Name: ix_chat_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_sessions_user_id ON public.chat_sessions USING btree (user_id);


--
-- Name: ix_embedding_jobs_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_embedding_jobs_entity_id ON public.embedding_jobs USING btree (entity_id);


--
-- Name: ix_embedding_jobs_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_embedding_jobs_entity_type ON public.embedding_jobs USING btree (entity_type);


--
-- Name: ix_embedding_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_embedding_jobs_status ON public.embedding_jobs USING btree (status);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ai_action_logs ai_action_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_action_logs
    ADD CONSTRAINT ai_action_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: audit_decision_links audit_decision_links_audit_finding_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_decision_links
    ADD CONSTRAINT audit_decision_links_audit_finding_id_fkey FOREIGN KEY (audit_finding_id) REFERENCES public.audit_findings(id);


--
-- Name: audit_decision_links audit_decision_links_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_decision_links
    ADD CONSTRAINT audit_decision_links_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES public.decisions(id);


--
-- Name: capa_audit_links capa_audit_links_audit_finding_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capa_audit_links
    ADD CONSTRAINT capa_audit_links_audit_finding_id_fkey FOREIGN KEY (audit_finding_id) REFERENCES public.audit_findings(id);


--
-- Name: capa_audit_links capa_audit_links_capa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.capa_audit_links
    ADD CONSTRAINT capa_audit_links_capa_id_fkey FOREIGN KEY (capa_id) REFERENCES public.capas(id);


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: decision_sop_links decision_sop_links_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES public.decisions(id);


--
-- Name: decision_sop_links decision_sop_links_sop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_sop_id_fkey FOREIGN KEY (sop_id) REFERENCES public.sops(id);


--
-- Name: decision_sop_links decision_sop_links_sop_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.decision_sop_links
    ADD CONSTRAINT decision_sop_links_sop_version_id_fkey FOREIGN KEY (sop_version_id) REFERENCES public.sop_versions(id);


--
-- Name: deviation_capa_links deviation_capa_links_capa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deviation_capa_links
    ADD CONSTRAINT deviation_capa_links_capa_id_fkey FOREIGN KEY (capa_id) REFERENCES public.capas(id);


--
-- Name: deviation_capa_links deviation_capa_links_deviation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deviation_capa_links
    ADD CONSTRAINT deviation_capa_links_deviation_id_fkey FOREIGN KEY (deviation_id) REFERENCES public.deviations(id);


--
-- Name: document_versions document_versions_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: documents fk_current_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_current_version FOREIGN KEY (current_version_id) REFERENCES public.document_versions(id) ON DELETE SET NULL;


--
-- Name: sop_deviation_links sop_deviation_links_deviation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sop_deviation_links
    ADD CONSTRAINT sop_deviation_links_deviation_id_fkey FOREIGN KEY (deviation_id) REFERENCES public.deviations(id);


--
-- Name: sop_deviation_links sop_deviation_links_sop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sop_deviation_links
    ADD CONSTRAINT sop_deviation_links_sop_id_fkey FOREIGN KEY (sop_id) REFERENCES public.sops(id);


--
-- Name: sop_versions sop_versions_sop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sop_versions
    ADD CONSTRAINT sop_versions_sop_id_fkey FOREIGN KEY (sop_id) REFERENCES public.sops(id) ON DELETE CASCADE;


--
-- Name: sop_versions sop_versions_superseded_by_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sop_versions
    ADD CONSTRAINT sop_versions_superseded_by_version_id_fkey FOREIGN KEY (superseded_by_version_id) REFERENCES public.sop_versions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict idIosmj1EihkJpMb8aJHAKRwKj4G842AZ8cfuNxYEzRxAdI3gNQ4CdyzRYaNW2v

