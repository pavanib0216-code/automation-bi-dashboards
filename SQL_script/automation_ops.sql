-- CREATE DATABASE automation_ops;
-- USE automation_ops;

-- GRANT ALL PRIVILEGES ON automation_ops.* TO 'pavani'@'localhost';
-- FLUSH PRIVILEGES;

USE automation_ops;

SELECT 'machine_health' AS table_name, COUNT(*) AS row_count FROM machine_health
UNION ALL
SELECT 'production_output', COUNT(*) FROM production_output
UNION ALL
SELECT 'maintenance_workorders', COUNT(*) FROM maintenance_workorders
UNION ALL
SELECT 'quality_defects', COUNT(*) FROM quality_defects;