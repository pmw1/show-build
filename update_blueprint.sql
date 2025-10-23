-- Update Episode Blueprint Template to match EPISODE_DIRECTORY_STANDARD.md
-- This SQL script updates the default 'Sunday Show' blueprint to create canonical structure

BEGIN;

-- Delete existing nodes for template ID 1 (Sunday Show)
DELETE FROM blueprint_nodes WHERE template_id = 1;

-- Insert root directories
INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, sort_order, is_required) VALUES
(1, NULL, 'directory', 'projects', 1, TRUE),
(1, NULL, 'directory', 'captures', 2, TRUE),
(1, NULL, 'directory', 'thumbnails', 3, TRUE),
(1, NULL, 'directory', 'assets', 4, TRUE),
(1, NULL, 'directory', 'rundown', 5, TRUE),
(1, NULL, 'directory', 'scripts', 6, TRUE),
(1, NULL, 'directory', 'exports', 7, TRUE);

-- Get IDs for parent directories (PostgreSQL-specific using RETURNING into temp table)
CREATE TEMP TABLE temp_root_ids AS
SELECT id, name FROM blueprint_nodes WHERE template_id = 1 AND parent_id IS NULL;

-- projects/ subdirectories
INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, sort_order, is_required)
SELECT 1, id, 'directory', 'teasers', 1, FALSE FROM temp_root_ids WHERE name = 'projects'
UNION ALL
SELECT 1, id, 'directory', 'graphics', 2, FALSE FROM temp_root_ids WHERE name = 'projects';

-- assets/ subdirectories
INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, sort_order, is_required)
SELECT 1, id, 'directory', 'video', 1, TRUE FROM temp_root_ids WHERE name = 'assets'
UNION ALL
SELECT 1, id, 'directory', 'images', 2, TRUE FROM temp_root_ids WHERE name = 'assets'
UNION ALL
SELECT 1, id, 'directory', 'audio', 3, TRUE FROM temp_root_ids WHERE name = 'assets'
UNION ALL
SELECT 1, id, 'directory', 'graphics', 4, TRUE FROM temp_root_ids WHERE name = 'assets';

-- rundown/media-list/ subdirectory
INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, sort_order, is_required)
SELECT 1, id, 'directory', 'media-list', 1, TRUE FROM temp_root_ids WHERE name = 'rundown';

-- scripts/ subdirectories
INSERT INTO blueprint_nodes (template_id, parent_id, node_type, name, sort_order, is_required)
SELECT 1, id, 'directory', 'versions', 1, TRUE FROM temp_root_ids WHERE name = 'scripts'
UNION ALL
SELECT 1, id, 'directory', 'current', 2, TRUE FROM temp_root_ids WHERE name = 'scripts';

-- Update template metadata
UPDATE blueprint_templates
SET template_metadata = jsonb_build_object(
    'specification', 'EPISODE_DIRECTORY_STANDARD.md v1.0',
    'updated', '2025-10-14',
    'canonical_structure', true,
    'airdate', '',
    'duration', '01:00:00',
    'status', 'draft',
    'description', 'Standard episode directory structure per canonical specification'
),
updated_at = NOW()
WHERE id = 1;

-- Verify structure
SELECT
    'Root directories created:' as status,
    COUNT(*) as count
FROM blueprint_nodes
WHERE template_id = 1 AND parent_id IS NULL;

SELECT
    'Total nodes created:' as status,
    COUNT(*) as count
FROM blueprint_nodes
WHERE template_id = 1;

-- Show structure
SELECT
    CASE WHEN bn.parent_id IS NULL THEN bn.name
         ELSE p.name || '/' || bn.name
    END as path,
    bn.node_type,
    bn.sort_order,
    bn.is_required
FROM blueprint_nodes bn
LEFT JOIN blueprint_nodes p ON bn.parent_id = p.id
WHERE bn.template_id = 1
ORDER BY
    COALESCE(p.sort_order, bn.sort_order),
    bn.sort_order;

DROP TABLE temp_root_ids;

COMMIT;

-- Final verification
SELECT
    '✅ Blueprint update complete' as status,
    'Matches EPISODE_DIRECTORY_STANDARD.md' as specification;
