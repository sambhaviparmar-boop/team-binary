-- FreightIQ Sprint 1: research-stage berth seed
-- Safe to rerun: inserts only missing (port, berth, source) combinations.
-- IMPORTANT:
--   * This is not an operational navigation database.
--   * Values are from cited public port documents/pages and require current marine confirmation.
--   * Haldia design draft/present depth are intentionally NOT loaded into max_draft_m because
--     design draft/current depth are not the same as currently allowable vessel draft.
--   * Do not run this file until the target database has the matching schema and port rows.

BEGIN;

INSERT INTO data_sources
    (source_name, publisher, source_url, dataset_type, units, frequency, license_notes, provenance_notes)
VALUES
    ('Paradip Port Authority berth specifications', 'Paradip Port Authority',
     'https://paradipport.gov.in/berth-specifications/',
     'observed', 'metres; tonnes where stated', 'reference document',
     'Public official website; follow publisher terms',
     'Public berth specifications. Draft limits may depend on tide and berth arrangement; verify current marine circulars before operational use.'),
    ('Syama Prasad Mookerjee Port Authority Haldia Dock Complex Administrative Report 2024-25',
     'Syama Prasad Mookerjee Port Authority',
     'https://smportkolkata.shipping.gov.in/smpk/wp-content/uploads/2026/04/Administrative-Report-2024-2025-Soft-Copy_compressed.pdf',
     'observed', 'metres; tonnes where stated', 'annual report',
     'Public official report; follow publisher terms',
     'Berth particulars from FY 2024-25 report. Design draft and present depth are not treated as current allowable vessel draft.'),
    ('Visakhapatnam Port Authority berth particulars and allowable drafts',
     'Visakhapatnam Port Authority',
     'https://vpt.shipping.gov.in/Template/navigateTemplate/gnt/QmVydGhz',
     'observed', 'metres; tonnes where stated', 'reference webpage and PDF',
     'Public official website; follow publisher terms',
     'Published berth particulars and allowable-draft reference. Current tide/operational restrictions must be checked before operational use.')
ON CONFLICT (source_name, dataset_type) DO UPDATE
SET publisher = EXCLUDED.publisher,
    source_url = EXCLUDED.source_url,
    units = EXCLUDED.units,
    frequency = EXCLUDED.frequency,
    license_notes = EXCLUDED.license_notes,
    provenance_notes = EXCLUDED.provenance_notes;

WITH berth_seed(port_name, berth_name, cargo_type, max_draft_m, max_loa_m, max_dwt_tonnes, source_name, restriction_notes) AS (
    VALUES
    ('Paradip', 'Berth No. 03 (New Coal Import Berth)', 'Coking coal', 16.00::numeric, 300.00::numeric, NULL::integer,
     'Paradip Port Authority berth specifications',
     'Published draft up to 16 m is tide/arrangement-conditioned. Verify current admissible draft and operating conditions; research-stage record.'),
    ('Paradip', 'Berth No. 05 (Coal Berth - 01)', 'Thermal coal', 14.50::numeric, 300.00::numeric, NULL::integer,
     'Paradip Port Authority berth specifications',
     'Published baseline draft 14.5 m; higher draft may be allowed under specified high-tide/arrangement conditions. Verify current restrictions.'),
    ('Paradip', 'Berth No. 06 (Coal Berth - 02)', 'Thermal coal', 14.50::numeric, 300.00::numeric, NULL::integer,
     'Paradip Port Authority berth specifications',
     'Published admissible draft; verify current operational restrictions before use.'),
    ('Paradip', 'Berth No. 07 (East Quay - 03)', 'Thermal coal', 14.50::numeric, 300.00::numeric, NULL::integer,
     'Paradip Port Authority berth specifications',
     'Published admissible draft; source notes arrangement-specific total LOA for multiple vessels. Verify current restrictions.'),
    ('Paradip', 'Berth No. 08 (East Quay - 02)', 'Thermal coal', 14.50::numeric, 300.00::numeric, NULL::integer,
     'Paradip Port Authority berth specifications',
     'Published admissible draft; verify current operational restrictions before use.'),
    ('Haldia', 'New Berth No. 1', 'Dry bulk: coke, coal, ore, limestone', NULL::numeric, 238.00::numeric, 75000,
     'Syama Prasad Mookerjee Port Authority Haldia Dock Complex Administrative Report 2024-25',
     'Official FY2024-25 report lists design draft 10.0 m and present depth 7.1 m; neither is loaded as current allowable draft. Confirm current draft forecast and vessel restrictions.'),
    ('Haldia', 'New Berth No. 2', 'Dry bulk: coke, coal, ore, limestone; also POL/chemicals', NULL::numeric, 239.00::numeric, 75000,
     'Syama Prasad Mookerjee Port Authority Haldia Dock Complex Administrative Report 2024-25',
     'Official FY2024-25 report lists design draft 12.2 m and present depth 8.1 m; neither is loaded as current allowable draft. Confirm current draft forecast and vessel restrictions.'),
    ('Haldia', 'New Berth No. 3', 'Mechanized berth for thermal coal', NULL::numeric, 239.00::numeric, 75000,
     'Syama Prasad Mookerjee Port Authority Haldia Dock Complex Administrative Report 2024-25',
     'Official FY2024-25 report lists design draft 12.2 m and present depth 9.1 m; neither is loaded as current allowable draft. Confirm current draft forecast and vessel restrictions.'),
    ('Visakhapatnam', 'EQ1', 'Steam coal', 14.50::numeric, 240.00::numeric, NULL::integer,
     'Visakhapatnam Port Authority berth particulars and allowable drafts',
     'Published permissible draft/LOA; beam not supplied in this seed. Verify current allowable-draft schedule.'),
    ('Visakhapatnam', 'EQ7 (PPP)', 'Includes thermal coal', 14.50::numeric, 240.00::numeric, NULL::integer,
     'Visakhapatnam Port Authority berth particulars and allowable drafts',
     'Published permissible draft/LOA; beam not supplied in this seed. Verify current allowable-draft schedule.'),
    ('Visakhapatnam', 'WQ2', 'Thermal coal, coking coal, multi-cargo', 13.50::numeric, 240.00::numeric, NULL::integer,
     'Visakhapatnam Port Authority berth particulars and allowable drafts',
     'Published permissible draft/LOA; beam not supplied in this seed. Verify current allowable-draft schedule.'),
    ('Visakhapatnam', 'WQ3', 'Coal', 13.50::numeric, 240.00::numeric, NULL::integer,
     'Visakhapatnam Port Authority berth particulars and allowable drafts',
     'Published permissible draft/LOA; beam not supplied in this seed. Verify current allowable-draft schedule.'),
    ('Visakhapatnam', 'VGCB', 'Coal; fully mechanized coal terminal', 18.10::numeric, 300.00::numeric, 200000,
     'Visakhapatnam Port Authority berth particulars and allowable drafts',
     'Published 18.1 m draft is subject to tide/operational conditions. Verify current restriction schedule; do not use as unconditional draft limit.')
)
INSERT INTO berths
    (port_id, berth_name, cargo_type, max_draft_m, max_loa_m, max_dwt_tonnes,
     restriction_notes, source_id, effective_from, effective_to, verification_status)
SELECT p.port_id, s.berth_name, s.cargo_type, s.max_draft_m, s.max_loa_m, s.max_dwt_tonnes,
       s.restriction_notes, ds.source_id, NULL, NULL, 'partially_verified'
FROM berth_seed s
JOIN ports p ON p.port_name = s.port_name AND p.country = 'India'
JOIN data_sources ds ON ds.source_name = s.source_name AND ds.dataset_type = 'observed'
WHERE NOT EXISTS (
    SELECT 1
    FROM berths b
    WHERE b.port_id = p.port_id
      AND b.berth_name = s.berth_name
      AND b.source_id = ds.source_id
);

COMMIT;

-- Verification after running:
-- SELECT p.port_name, b.berth_name, b.cargo_type, b.max_draft_m, b.max_loa_m,
--        b.max_dwt_tonnes, b.verification_status, ds.source_name
-- FROM berths b
-- JOIN ports p USING (port_id)
-- LEFT JOIN data_sources ds USING (source_id)
-- ORDER BY p.port_name, b.berth_name;
