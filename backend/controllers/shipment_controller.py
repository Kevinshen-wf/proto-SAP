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

class ShipmentController:
    def __init__(self):
        self.db_config = get_db_config()
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = psycopg2.connect(**self.db_config)
            return connection
        except Exception as error:
            print(f"数据库连接失败: {error}")
            return None
    
    def process_shipment(self, source_table, po, pn, shipment_qty, max_qty, user_email, po_line=None, tracking_no=None, shipping_mode=None, shipping_cost=None, is_shared=False):
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
            
            # 过滤closed_record，只保留closed表中存在的列
            filtered_closed_record = {}
            for key, value in closed_record.items():
                if key in closed_columns:
                    filtered_closed_record[key] = value
            
            # 插入数据到closed表
            columns = list(filtered_closed_record.keys())
            values = list(filtered_closed_record.values())
            
            placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
            
            insert_closed_query = sql.SQL("INSERT INTO purchase_orders.{} ({}) VALUES ({})").format(
                sql.Identifier(target_table),
                sql.SQL(", ").join(sql.Identifier(col) for col in columns),
                placeholders
            )
            
            cursor.execute(insert_closed_query, values)
            
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
                new_qty = max_qty - shipment_qty
                net_price = float(open_record.get('net_price') or 0)
                new_total_price = round(new_qty * net_price, 2) if net_price > 0 else 0
                
                if po_line:
                    update_open_query = sql.SQL("UPDATE purchase_orders.{} SET qty = %s, total_price = %s WHERE po_line = %s").format(
                        sql.Identifier(source_table)
                    )
                    cursor.execute(update_open_query, (new_qty, new_total_price, po_line))
                else:
                    update_open_query = sql.SQL("UPDATE purchase_orders.{} SET qty = %s, total_price = %s WHERE po = %s AND pn = %s").format(
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
                'remaining_qty': max_qty - shipment_qty if not is_full_shipment else 0
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
