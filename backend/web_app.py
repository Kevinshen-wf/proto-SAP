from flask import Flask, render_template, jsonify, request, g
import psycopg2
from psycopg2 import sql
from config.env_db_config import get_db_config
import hashlib
import json
import os
from functools import wraps
from backend.utils.jwt_utils import verify_token

# 导入路由蓝图
from backend.routes.table_routes import table_bp
from backend.routes.user_routes import user_bp
from backend.routes.shipment_routes import shipment_bp

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'frontend')
static_dir = os.path.join(project_root, 'frontend')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='')

# 注册路由蓝图
app.register_blueprint(table_bp)
app.register_blueprint(user_bp)
app.register_blueprint(shipment_bp)

# 数据库连接配置
db_config = get_db_config()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头中获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # 期望格式: Bearer <token>
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'success': False, 'error': 'Token格式错误'}), 401
        
        if not token:
            return jsonify({'success': False, 'error': '缺少Token'}), 401
        
        success, result = verify_token(token)
        if not success:
            return jsonify({'success': False, 'error': result}), 401
        
        # 将用户信息存储在全局变量中
        g.current_user = result
        return f(*args, **kwargs)
    
    return decorated

# 在所有请求之前检查认证（除了特定的公开路由）
@app.before_request
def check_authentication():
    # 添加调试信息
    print(f"请求路径: {request.path}")
    print(f"请求方法: {request.method}")
    print(f"请求端点: {request.endpoint}")
    
    # 公开路由不需要认证
    public_routes = [
        '/api/user/register',
        '/api/user/login',
        '/api/user/verify-email',
        '/api/user/set-password',
        '/register.html',
        '/login.html',
        '/set_password.html'
    ]
    
    # 静态文件不需要认证
    if request.path.startswith('/static/') or request.path.startswith('/css/') or request.path.startswith('/js/') or request.path.startswith('/assets/'):
        return
    
    # 检查是否是公开路由
    if request.path in public_routes or request.endpoint in ['static']:
        return
    
    # 主页和PDF导入页面需要特殊处理，因为它们是HTML页面
    if request.path == '/' or request.path == '/pdf_import.html':
        # 对于HTML页面，我们不在此处拦截，而是在前端处理
        return
    
    # 对于其他API路由，需要认证
    if request.path.startswith('/api/'):
        print(f"API路由需要认证: {request.path}")
        token = None
        
        # 从请求头中获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # 期望格式: Bearer <token>
                token = auth_header.split(" ")[1]
            except IndexError:
                print("Token格式错误")
                return jsonify({'success': False, 'error': 'Token格式错误'}), 401
        
        if not token:
            print("缺少Token")
            return jsonify({'success': False, 'error': '缺少Token'}), 401
        
        success, result = verify_token(token)
        if not success:
            print(f"Token验证失败: {result}")
            return jsonify({'success': False, 'error': result}), 401
        
        # 将用户信息存储在全局变量中
        g.current_user = result
        print(f"认证成功，用户: {result}")

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = psycopg2.connect(**db_config)
        return connection
    except Exception as error:
        print(f"数据库连接失败: {error}")
        return None

def generate_row_hash(row_data):
    """为行数据生成哈希值用于版本控制"""
    # 将行数据转换为字符串并生成哈希
    row_str = str(sorted(row_data.items()))
    return hashlib.md5(row_str.encode()).hexdigest()

@app.route('/')
def index():
    """主页"""
    return render_template('database_management.html')

@app.route('/pdf_import.html')
def pdf_import():
    """PDF导入页面"""
    return render_template('pdf_import.html')

@app.route('/register.html')
def register():
    """注册页面"""
    return render_template('register.html')

@app.route('/login.html')
def login():
    """登录页面"""
    return render_template('login.html')

@app.route('/set_password.html')
def set_password():
    """设置密码页面"""
    return render_template('set_password.html')

# 所有 /api/tables 相关的路由由蓝图处理，不在此处定义
# 避免路由冲突

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)