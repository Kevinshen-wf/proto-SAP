-- 修复 created_at 字段，使用 po_placed_date 作为真正的创建时间
-- 这个脚本会更新所有4个表，将 created_at 设置为 po_placed_date

-- 更新 wf_open 表
UPDATE purchase_orders.wf_open
SET created_at = po_placed_date
WHERE po_placed_date IS NOT NULL;

-- 更新 wf_closed 表
UPDATE purchase_orders.wf_closed
SET created_at = po_placed_date
WHERE po_placed_date IS NOT NULL;

-- 更新 non_wf_open 表
UPDATE purchase_orders.non_wf_open
SET created_at = po_placed_date
WHERE po_placed_date IS NOT NULL;

-- 更新 non_wf_closed 表
UPDATE purchase_orders.non_wf_closed
SET created_at = po_placed_date
WHERE po_placed_date IS NOT NULL;

-- 验证更新结果
SELECT 'wf_open' as table_name, COUNT(*) as total_records, 
       COUNT(DISTINCT created_at) as unique_created_at_values
FROM purchase_orders.wf_open
UNION ALL
SELECT 'wf_closed', COUNT(*), COUNT(DISTINCT created_at)
FROM purchase_orders.wf_closed
UNION ALL
SELECT 'non_wf_open', COUNT(*), COUNT(DISTINCT created_at)
FROM purchase_orders.non_wf_open
UNION ALL
SELECT 'non_wf_closed', COUNT(*), COUNT(DISTINCT created_at)
FROM purchase_orders.non_wf_closed;
