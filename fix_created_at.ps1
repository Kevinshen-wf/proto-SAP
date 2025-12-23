# 修复 created_at 字段的 PowerShell 脚本

Write-Host "正在更新 wf_open 表..."
docker exec proto-sap-db psql -U postgres -d purchase_orders -c "UPDATE purchase_orders.wf_open SET created_at = po_placed_date WHERE po_placed_date IS NOT NULL;"

Write-Host "正在更新 wf_closed 表..."
docker exec proto-sap-db psql -U postgres -d purchase_orders -c "UPDATE purchase_orders.wf_closed SET created_at = po_placed_date WHERE po_placed_date IS NOT NULL;"

Write-Host "正在更新 non_wf_open 表..."
docker exec proto-sap-db psql -U postgres -d purchase_orders -c "UPDATE purchase_orders.non_wf_open SET created_at = po_placed_date WHERE po_placed_date IS NOT NULL;"

Write-Host "正在更新 non_wf_closed 表..."
docker exec proto-sap-db psql -U postgres -d purchase_orders -c "UPDATE purchase_orders.non_wf_closed SET created_at = po_placed_date WHERE po_placed_date IS NOT NULL;"

Write-Host "`n验证更新结果..."
docker exec proto-sap-db psql -U postgres -d purchase_orders -c "SELECT po_line, comment, created_at, update_at FROM purchase_orders.wf_open WHERE po_line IN ('4500009853/30', '4500008993/30', '4500008993/20') ORDER BY created_at DESC;"

Write-Host "`n完成！"
