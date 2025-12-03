#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库表列"""

import psycopg2
from backend.utils.config import get_db_config

conn = psycopg2.connect(**get_db_config())
cursor = conn.cursor()

# Check wf_closed table columns
cursor.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'purchase_orders' 
AND table_name = 'wf_closed' 
ORDER BY ordinal_position
""")

print('[INFO] wf_closed table columns:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check if shipment_batch_no exists
cursor.execute("""
SELECT COUNT(*) FROM information_schema.columns 
WHERE table_schema = 'purchase_orders' 
AND table_name = 'wf_closed' 
AND column_name = 'shipment_batch_no'
""")

count = cursor.fetchone()[0]
print(f'\n[INFO] shipment_batch_no column exists: {count == 1}')

# Check actual data in wf_closed
cursor.execute("SELECT id, po_line, shipment_batch_no FROM purchase_orders.wf_closed LIMIT 5")
print(f'\n[INFO] Sample data from wf_closed:')
for row in cursor.fetchall():
    print(f'  id={row[0]}, po_line={row[1]}, shipment_batch_no={row[2]}')

cursor.close()
conn.close()
