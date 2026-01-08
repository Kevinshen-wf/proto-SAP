from flask import Blueprint, jsonify, request, render_template
from backend.controllers.user_controller import UserController
import hashlib

# 创建用户蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# 创建控制器实例
user_controller = UserController()


@user_bp.route('/register', methods=['POST'])
def register():
    """用户注册 - 已禁用，仅支持数据库直接添加用户"""
    return jsonify({'success': False, 'error': '注册功能已禁用，请联系管理员在数据库中添加用户'}), 403


@user_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """验证邮箱页面"""
    try:
        token = request.args.get('token')
        
        print(f"收到验证令牌请求: token={token}")
        
        if not token:
            return jsonify({'success': False, 'error': '缺少验证令牌'}), 400
        
        # 验证令牌
        success, result = user_controller.verify_user_token(token)
        
        print(f"验证令牌结果: success={success}, result={result}")
        
        if success:
            # 返回用户信息
            return jsonify({
                'success': True, 
                'user': result
            }), 200
        else:
            return jsonify({'success': False, 'error': result}), 400
    except Exception as e:
        print(f"验证令牌时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/set-password', methods=['POST'])
def set_password():
    """设置密码"""
    try:
        # 获取请求数据
        data = request.json
        user_id = data.get('user_id')
        password = data.get('password')
        
        print(f"收到设置密码请求: user_id={user_id}, password={'*' * len(password) if password else None}")
        
        if not user_id or not password:
            return jsonify({'success': False, 'error': '用户ID和密码不能为空'}), 400
        
        # 设置密码
        success, message = user_controller.set_user_password(user_id, password)
        
        print(f"设置密码结果: success={success}, message={message}")
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        print(f"设置密码时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/profile', methods=['GET'])
@user_controller.token_required
def get_user_profile():
    """获取用户资料"""
    try:
        # 获取当前用户信息
        current_user = request.current_user
        return jsonify({
            'success': True,
            'user': {
                'user_id': current_user['user_id'],
                'email': current_user['email']
            }
        }), 200
    except Exception as e:
        print(f"获取用户资料时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/change-password', methods=['POST'])
@user_controller.token_required
def change_password():
    """修改密码"""
    try:
        # 获取当前用户信息
        current_user = request.current_user
        user_id = current_user['user_id']
        
        # 获取请求数据
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        print(f"收到修改密码请求: user_id={user_id}")
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'error': '旧密码和新密码不能为空'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': '新密码长度至少为6位'}), 400
        
        # 修改密码
        success, message = user_controller.change_password(user_id, old_password, new_password)
        
        print(f"修改密码结果: success={success}, message={message}")
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        print(f"修改密码时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/protected', methods=['GET'])
@user_controller.token_required
def protected_route():
    """受保护的路由示例"""
    try:
        # 获取当前用户信息
        current_user = request.current_user
        return jsonify({
            'success': True,
            'message': '访问受保护资源成功',
            'user': {
                'user_id': current_user['user_id'],
                'email': current_user['email']
            }
        }), 200
    except Exception as e:
        print(f"访问受保护资源时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        # 获取请求数据
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        print(f"收到登录请求: email={email}")
        
        if not email or not password:
            return jsonify({'success': False, 'error': '邮箱和密码不能为空'}), 400
        
        # 用户登录并生成token
        success, result = user_controller.login_user(email, password)
        
        print(f"登录结果: success={success}, result={result}")
        
        if success:
            return jsonify({
                'success': True, 
                'message': '登录成功',
                'user': result['user'],
                'token': result['token'],
                'needs_password_change': result.get('needs_password_change', False)
            }), 200
        else:
            return jsonify({'success': False, 'error': result}), 401
    except Exception as e:
        print(f"登录时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500