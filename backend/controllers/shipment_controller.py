"""
发货控制器
处理发货逻辑：
1. 全部发货：删除open表记录，插入closed表
2. 部分发货：更新open表qty，插入closed表
3. 记录操作日志到po_records表
"""

import psycopg2
from psycopg2 import sql
from backend.utils.config import get_db_config
from backend.operation_logger import operation_logger
import json
import uuid
from datetime import datetime

class ShipmentController:
    def __init__(self):
        self.db_config = get_db_config()
        # 自动检查并修复数据库表结构
        self._ensure_closed_tables_structure()
    
    def _ensure_closed_tables_structure(self):
        """
        确保closed表存在必要的列，如果不存在则自动添加
        """
        try:
            conn = self.get_connection()
            if not conn:
                print(f"[WARNING] Cannot connect to DB for structure check")
                return
            
            cursor = conn.cursor()
            
            for table_name in ['wf_closed', 'non_wf_closed']:
                # 检查shipment_batch_no列是否存在
                check_query = """
                    SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_schema = 'purchase_orders' 
                    AND table_name = %s 
                    AND column_name = 'shipment_batch_no'
                """
                cursor.execute(check_query, (table_name,))
                
                if cursor.fetchone()[0] == 0:
                    # 列不存在，添加它
                    print(f"[INFO] Missing shipment_batch_no in {table_name}, adding...")
                    add_column_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN shipment_batch_no VARCHAR(50)"
                    cursor.execute(add_column_query)
                    conn.commit()
                    print(f"[SUCCESS] Added shipment_batch_no to {table_name}")
                else:
                    print(f"[INFO] shipment_batch_no already exists in {table_name}")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Failed to ensure closed tables structure: {e}")
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = psycopg2.connect(**self.db_config)
            return connection
        except Exception as error:
            print(f"数据库连接失败: {error}")
            return None
    
    def process_shipment(self, source_table, po, pn, shipment_qty, max_qty, user_email, po_line=None, tracking_no=None, shipping_mode=None, shipping_cost=None, is_shared=False, shipment_batch_no=None):
        """
        处理发货
        
        Args:
            source_table: 源表 (wf_open 或 non_wf_open)
            po: PO号
            pn: PN号
            shipment_qty: 发货数量
            max_qty: 最大可发货数量
            user_email: 用户邮箱
            po_line: PO/行号
            tracking_no: 追踪号
            shipping_mode: 运输方式
            shipping_cost: 运费
            is_shared: 是否是整发货（不是整发货需添加shared:前缀）
            shipment_batch_no: 发货批次号 (可选，如果不提供则自动生成)
            
        Returns:
            dict: 处理结果
        """
        conn = self.get_connection()
        if not conn:
            return {'success': False, 'message': '数据库连接失败'}
        
        try:
            cursor = conn.cursor()
            
            # 验证参数
            if not source_table or source_table not in ['wf_open', 'non_wf_open']:
                return {'success': False, 'message': '无效的源表'}
            
            if shipment_qty <= 0 or shipment_qty > max_qty:
                return {'success': False, 'message': f'发货数量必须在1到{max_qty}之间'}
            
            # 确定源表和目标表
            target_table = 'wf_closed' if source_table == 'wf_open' else 'non_wf_closed'
            primary_key_field = 'po_line'
            
            # 不流量霉 po_line 是否传递
            # 获取open表中的完整记录
            if po_line:
                get_record_query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE po_line = %s").format(
                    sql.Identifier(source_table)
                )
                cursor.execute(get_record_query, (po_line,))
            else:
                get_record_query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE po = %s AND pn = %s").format(
                    sql.Identifier(source_table)
                )
                cursor.execute(get_record_query, (po, pn))
            record = cursor.fetchone()
            
            if not record:
                conn.close()
                return {'success': False, 'message': '未找到指定的记录'}
            
            # 获取列名
            colnames = [desc[0] for desc in cursor.description]
            open_record = dict(zip(colnames, record))
            
            # 检查是否是全部发货
            is_full_shipment = (shipment_qty >= max_qty)
            
            # 准备closed表的数据（复制open表数据，修改qty、total_price以及新字段）
            closed_record = open_record.copy()
            closed_record['qty'] = shipment_qty
            
            # 设置发货相关字段
            if tracking_no:
                closed_record['tracking_no'] = tracking_no
            if shipping_mode:
                closed_record['shipping_mode'] = shipping_mode if source_table == 'non_wf_open' else shipping_mode
                if source_table == 'wf_open':
                    closed_record['wfsz_shipping_mode'] = shipping_mode
            if shipping_cost is not None:
                # 运费处理：永远只存储数值，不在数据库中存储shared:前缀
                # shared:前缀只作为UI显示标记，后端只需存储数字值
                closed_record['shipping_cost'] = shipping_cost
            
            # 计算total_price（qty * net_price）
            net_price = float(closed_record.get('net_price') or 0)
            if net_price > 0:
                closed_record['total_price'] = round(shipment_qty * net_price, 2)
            
            # 生成或使用传入的shipment_batch_no (格式: SHIP-YYYYMMDD-UUID缩写)
            # 优先使用前端传来的批次号，实现批量发货的一致性
            if not shipment_batch_no:
                # 如果没有提供则自动生成
                shipment_batch_no = f"SHIP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            closed_record['shipment_batch_no'] = shipment_batch_no
            
            print(f"[DEBUG] ===== SHIPMENT PROCESS START =====")
            print(f"[DEBUG] Generated shipment_batch_no: {shipment_batch_no}")
            print(f"[DEBUG] Inserting closed record with shipment_batch_no for PO={po}, PN={pn}")
            print(f"[DEBUG] closed_record keys: {list(closed_record.keys())}")
            print(f"[DEBUG] closed_record['shipment_batch_no']: {closed_record.get('shipment_batch_no')}")
            
            # 处理po_line字段（避免主键冲突）
            if 'po_line' in closed_record and closed_record['po_line']:
                # closed表的po_line不作为主键，可以保持相同值
                pass
            
            # 获取closed表的列
            get_closed_columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'purchase_orders' 
                AND table_name = %s
                ORDER BY ordinal_position
            """
            cursor.execute(get_closed_columns_query, (target_table,))
            closed_columns = set(row[0] for row in cursor.fetchall())
            
            print(f"[DEBUG] {target_table} columns: {sorted(closed_columns)}")
            print(f"[DEBUG] 'shipment_batch_no' in closed_columns: {'shipment_batch_no' in closed_columns}")
            
            # 过滤closed_record，只保留closed表中存在的列
            # 且排除 update_at 字段，让 PostgreSQL 使用 DEFAULT CURRENT_TIMESTAMP
            filtered_closed_record = {}
            for key, value in closed_record.items():
                if key in closed_columns and key != 'update_at':  # 排除 update_at
                    filtered_closed_record[key] = value
            
            print(f"[DEBUG] filtered_closed_record keys: {list(filtered_closed_record.keys())}")
            print(f"[DEBUG] filtered_closed_record['shipment_batch_no']: {filtered_closed_record.get('shipment_batch_no')}")
            
            # 插入数据到closed表
            columns = list(filtered_closed_record.keys())
            values = list(filtered_closed_record.values())
            
            placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
            
            insert_closed_query = sql.SQL("INSERT INTO purchase_orders.{} ({}) VALUES ({})").format(
                sql.Identifier(target_table),
                sql.SQL(", ").join(sql.Identifier(col) for col in columns),
                placeholders
            )
            
            print(f"[DEBUG] Inserting into {target_table}")
            print(f"[DEBUG] Columns: {columns}")
            print(f"[DEBUG] Values: {values}")
            print(f"[DEBUG] shipment_batch_no in columns: {'shipment_batch_no' in columns}")
            print(f"[DEBUG] shipment_batch_no value in values: {values[columns.index('shipment_batch_no')] if 'shipment_batch_no' in columns else 'NOT FOUND'}")
            
            cursor.execute(insert_closed_query, values)
            
            # 验证插入是否成功
            inserted_rows = cursor.rowcount
            print(f"[DEBUG] Rows inserted: {inserted_rows}")
            
            if inserted_rows == 0:
                print(f"[ERROR] Failed to insert record into {target_table}")
                return {'success': False, 'message': f'失败：无法插入{target_table}表'}
            
            print(f"[DEBUG] ===== SHIPMENT PROCESS END =====")
            
            # 处理open表的记录
            if is_full_shipment:
                # 全部发货：删除open表记录
                if po_line:
                    delete_open_query = sql.SQL("DELETE FROM purchase_orders.{} WHERE po_line = %s").format(
                        sql.Identifier(source_table)
                    )
                    cursor.execute(delete_open_query, (po_line,))
                else:
                    delete_open_query = sql.SQL("DELETE FROM purchase_orders.{} WHERE po = %s AND pn = %s").format(
                        sql.Identifier(source_table)
                    )
                    cursor.execute(delete_open_query, (po, pn))
                operation_type = 'full_shipment'
            else:
                # 部分发货：更新open表qty和total_price
                # 同时更新 update_at 时间戳
                new_qty = max_qty - shipment_qty
                net_price = float(open_record.get('net_price') or 0)
                new_total_price = round(new_qty * net_price, 2) if net_price > 0 else 0
                
                if po_line:
                    update_open_query = sql.SQL(
                        "UPDATE purchase_orders.{} SET qty = %s, total_price = %s, update_at = CURRENT_TIMESTAMP WHERE po_line = %s"
                    ).format(
                        sql.Identifier(source_table)
                    )
                    cursor.execute(update_open_query, (new_qty, new_total_price, po_line))
                else:
                    update_open_query = sql.SQL(
                        "UPDATE purchase_orders.{} SET qty = %s, total_price = %s, update_at = CURRENT_TIMESTAMP WHERE po = %s AND pn = %s"
                    ).format(
                        sql.Identifier(source_table)
                    )
                    cursor.execute(update_open_query, (new_qty, new_total_price, po, pn))
                operation_type = 'partial_shipment'
            
            conn.commit()
            
            # 记录操作日志
            try:
                shipment_record = {
                    'operation': operation_type,
                    'source_table': source_table,
                    'target_table': target_table,
                    'po': po,
                    'pn': pn,
                    'shipment_qty': shipment_qty,
                    'max_qty': max_qty,
                    'remaining_qty': max_qty - shipment_qty if not is_full_shipment else 0,
                    'record_data': filtered_closed_record
                }
                
                operation_logger.log_operation(
                    user_email=user_email,
                    table_name=source_table,
                    operation=f'shipment_{operation_type}',
                    record_data=shipment_record
                )
            except Exception as log_error:
                print(f"记录发货操作日志时出错: {log_error}")
            
            cursor.close()
            conn.close()
            
            # 返回成功结果
            result_message = f"{'全部' if is_full_shipment else '部分'}发货成功，发货数量: {shipment_qty}"
            return {
                'success': True,
                'message': result_message,
                'shipment_type': '全部发货' if is_full_shipment else '部分发货',
                'shipment_qty': shipment_qty,
                'remaining_qty': max_qty - shipment_qty if not is_full_shipment else 0,
                'shipment_batch_no': shipment_batch_no
            }
            
        except Exception as error:
            if conn:
                try:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                except:
                    pass
            return {'success': False, 'message': f'发货处理失败: {error}'}
    
    def return_shipment(self, closed_table, record_id, return_qty, user_email, new_shipping_cost=None, shipment_batch_no=None):
        """
        处理退货
        
        Args:
            closed_table: closed表名 (例如 wf_closed 或 non_wf_closed)
            record_id: closed表的ID (为了正确标識单一记录)
            return_qty: 退货数量
            user_email: 用户邮箱
            new_shipping_cost: 新的运费 (可选，用于更新同一批发货不的运费)
        
        Returns:
            dict: 处理结果
        """
        conn = self.get_connection()
        if not conn:
            return {'success': False, 'message': '数据库连接失败'}
        
        try:
            cursor = conn.cursor()
            
            # 验证参数
            if not closed_table or closed_table not in ['wf_closed', 'non_wf_closed']:
                return {'success': False, 'message': '无效的closed表'}
            
            if return_qty <= 0:
                return {'success': False, 'message': '退货数量必须大于0'}
            
            # 确定源表和目标表
            source_table = 'wf_open' if closed_table == 'wf_closed' else 'non_wf_open'
            
            # 从有效表获取带回须的完整记录 (using id as primary key)
            get_closed_query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE id = %s").format(
                sql.Identifier(closed_table)
            )
            cursor.execute(get_closed_query, (record_id,))
            closed_record = cursor.fetchone()
            
            if not closed_record:
                conn.close()
                return {'success': False, 'message': '未找到指定的closed记录'}
            
            # 获取列名
            colnames = [desc[0] for desc in cursor.description]
            closed_record_dict = dict(zip(colnames, closed_record))
            
            # 得到po_line（用于在open表中查找）
            po_line = closed_record_dict.get('po_line')
            
            # 处理有效表中是否存在该记录
            get_open_query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE po_line = %s").format(
                sql.Identifier(source_table)
            )
            cursor.execute(get_open_query, (po_line,))
            open_record = cursor.fetchone()
            
            if open_record:
                # 有效表中存在该记录，更新qty和total_price
                # 同时更新 update_at 时间戳
                colnames_open = [desc[0] for desc in cursor.description]
                open_record_dict = dict(zip(colnames_open, open_record))
                
                # 更新有效表的qty和total_price
                new_open_qty = float(open_record_dict.get('qty') or 0) + return_qty
                net_price = float(open_record_dict.get('net_price') or 0)
                new_total_price = round(new_open_qty * net_price, 2) if net_price > 0 else 0
                
                update_open_query = sql.SQL(
                    "UPDATE purchase_orders.{} SET qty = %s, total_price = %s, update_at = CURRENT_TIMESTAMP WHERE po_line = %s"
                ).format(
                    sql.Identifier(source_table)
                )
                cursor.execute(update_open_query, (new_open_qty, new_total_price, po_line))
            else:
                # 有效表中不存在该记录，需要从有效表中恢复
                # 填充表的列
                get_open_columns_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'purchase_orders' 
                    AND table_name = %s
                    ORDER BY ordinal_position
                """
                cursor.execute(get_open_columns_query, (source_table,))
                open_columns = set(row[0] for row in cursor.fetchall())
                
                # 从有效表记录增到有效表中，但下流数量为退货数量
                open_insert_record = {}
                for key, value in closed_record_dict.items():
                    if key in open_columns and key != 'shipment_batch_no' and key != 'update_at':
                        if key == 'qty':
                            open_insert_record[key] = return_qty
                        elif key == 'total_price':
                            net_price = float(closed_record_dict.get('net_price') or 0)
                            open_insert_record[key] = round(return_qty * net_price, 2) if net_price > 0 else 0
                        else:
                            open_insert_record[key] = value
                
                # 插入有效表
                columns = list(open_insert_record.keys())
                values = list(open_insert_record.values())
                
                placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
                
                insert_open_query = sql.SQL("INSERT INTO purchase_orders.{} ({}) VALUES ({})").format(
                    sql.Identifier(source_table),
                    sql.SQL(", ").join(sql.Identifier(col) for col in columns),
                    placeholders
                )
                
                cursor.execute(insert_open_query, values)
            
            # 处理运费更新 - 必须在删除/更新closed表之前执行
            # 先获取closed_qty，用于后续的部分/全部退货判断
            closed_qty = float(closed_record_dict.get('qty') or 0)
            
            if new_shipping_cost is not None:
                # 获取shipment_batch_no（优先使用前端传进来的批号，其次是数据库中的）
                batch_no = shipment_batch_no or closed_record_dict.get('shipment_batch_no')
                print(f"[DEBUG] Attempting to update shipping cost:")
                print(f"  - Batch No (from frontend): {shipment_batch_no}")
                print(f"  - Batch No (from database): {closed_record_dict.get('shipment_batch_no')}")
                print(f"  - Final Batch No to use: {batch_no}")
                print(f"  - New Shipping Cost: {new_shipping_cost}")
                
                if batch_no:
                    # 更新所有相同batch的记录（除了要删除的当前记录）
                    # 同时更新 update_at 时间戳
                    update_shipping_cost_query = sql.SQL(
                        "UPDATE purchase_orders.{} SET shipping_cost = %s, update_at = CURRENT_TIMESTAMP WHERE shipment_batch_no = %s AND id != %s"
                    ).format(sql.Identifier(closed_table))
                    cursor.execute(update_shipping_cost_query, (new_shipping_cost, batch_no, record_id))
                    rows_affected = cursor.rowcount
                    print(f"  - Query executed. Rows affected (excluding current): {rows_affected}")
                    
                    # 如果是部分退货，也应该更新当前记录的运费
                    if return_qty < closed_qty:
                        update_current_cost_query = sql.SQL(
                            "UPDATE purchase_orders.{} SET shipping_cost = %s, update_at = CURRENT_TIMESTAMP WHERE id = %s"
                        ).format(sql.Identifier(closed_table))
                        cursor.execute(update_current_cost_query, (new_shipping_cost, record_id))
                        print(f"  - Current record shipping cost also updated (partial return)")
                else:
                    print(f"[DEBUG] No shipment_batch_no found, cannot update shipping cost")
            else:
                print(f"[DEBUG] new_shipping_cost is None, skipping shipping cost update")
            
            # 处理closed表的数据：根据退货数量是否为全部发货来删除或更新
            if return_qty >= closed_qty:
                # 全部退货：删除closed表的记录 (using id as primary key)
                delete_closed_query = sql.SQL("DELETE FROM purchase_orders.{} WHERE id = %s").format(
                    sql.Identifier(closed_table)
                )
                cursor.execute(delete_closed_query, (record_id,))
            else:
                # 部分退货：更新closed表的qty和total_price (using id as primary key)
                # 同时更新 update_at 时间戳
                new_closed_qty = closed_qty - return_qty
                net_price = float(closed_record_dict.get('net_price') or 0)
                new_closed_total_price = round(new_closed_qty * net_price, 2) if net_price > 0 else 0
                
                update_closed_query = sql.SQL(
                    "UPDATE purchase_orders.{} SET qty = %s, total_price = %s, update_at = CURRENT_TIMESTAMP WHERE id = %s"
                ).format(
                    sql.Identifier(closed_table)
                )
                cursor.execute(update_closed_query, (new_closed_qty, new_closed_total_price, record_id))
            
            conn.commit()
            
            # 记录退货操作日志
            try:
                return_record = {
                    'operation': 'return_shipment',
                    'closed_table': closed_table,
                    'source_table': source_table,
                    'po_line': po_line,
                    'return_qty': return_qty,
                    'new_shipping_cost': new_shipping_cost
                }
                
                operation_logger.log_operation(
                    user_email=user_email,
                    table_name=closed_table,
                    operation='return_shipment',
                    record_data=return_record
                )
            except Exception as log_error:
                print(f"记录退货操作日志时出错: {log_error}")
            
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'message': f'退货成功，退货数量: {return_qty}'
            }
            
        except Exception as error:
            if conn:
                try:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                except:
                    pass
            return {'success': False, 'message': f'退货处理失败: {error}'}