"""
发货处理路由
处理从open表到closed表的货物发送
"""

from flask import Blueprint, jsonify, request
from backend.controllers.shipment_controller import ShipmentController

# 创建蓝图
shipment_bp = Blueprint('shipment', __name__, url_prefix='/api/shipment')

# 创建控制器实例
shipment_controller = ShipmentController()

@shipment_bp.route('/process', methods=['POST'])
def process_shipment():
    """处理发货"""
    try:
        # 获取请求数据
        data = request.json
        
        # 从请求头获取用户邮箱
        user_email = request.headers.get('X-User-Email', 'unknown@example.com')
        
        # 调用控制器处理发货
        result = shipment_controller.process_shipment(
            source_table=data.get('source_table'),
            po=data.get('po'),
            pn=data.get('pn'),
            shipment_qty=data.get('shipment_qty'),
            max_qty=data.get('max_qty'),
            user_email=user_email,
            po_line=data.get('po_line'),
            tracking_no=data.get('tracking_no'),
            shipping_mode=data.get('shipping_mode'),
            shipping_cost=data.get('shipping_cost'),
            is_shared=data.get('is_shared', False),
            shipment_batch_no=data.get('shipment_batch_no')  # 新增：支持接收前端传来的批次号
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@shipment_bp.route('/return', methods=['POST'])
def return_shipment():
    """处理退货"""
    try:
        data = request.json
        user_email = request.headers.get('X-User-Email', 'unknown@example.com')
        
        result = shipment_controller.return_shipment(
            closed_table=data.get('closed_table'),
            record_id=data.get('record_id'),
            return_qty=data.get('return_qty'),
            user_email=user_email,
            new_shipping_cost=data.get('new_shipping_cost'),
            shipment_batch_no=data.get('shipment_batch_no')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
