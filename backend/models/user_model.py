import psycopg2
from psycopg2 import sql
import hashlib
import secrets
import datetime
from backend.utils.config import get_db_config


class UserManager:
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

    def create_users_table(self):
        """创建用户表"""
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"

        try:
            cursor = conn.cursor()
            
            # 创建Schema（如果不存在）
            cursor.execute("CREATE SCHEMA IF NOT EXISTS purchase_orders")
            
            # 使用Schema
            cursor.execute("SET search_path TO purchase_orders")
            
            # 创建用户表
            create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(255),
                token_expires TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token)")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True, "用户表创建成功"
        except Exception as error:
            if conn:
                conn.rollback()
                conn.close()
            return False, f"创建用户表时出错: {error}"

    def is_valid_email(self, email):
        """检查邮箱是否为@wefabricate.com后缀"""
        return email.endswith('@wefabricate.com')

    def generate_verification_token(self):
        """生成验证令牌"""
        return secrets.token_urlsafe(32)

    def register_user(self, email):
        """用户注册"""
        # 检查邮箱格式
        if not self.is_valid_email(email):
            return False, "只允许使用@wefabricate.com后缀的邮箱"

        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"

        try:
            cursor = conn.cursor()
            
            # 邮箱转换为小写（不区分大小写）
            email_lower = email.lower()
            
            # 检查用户是否已存在
            check_query = "SELECT id FROM purchase_orders.users WHERE LOWER(email) = %s"
            cursor.execute(check_query, (email_lower,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, "该邮箱已被注册"

            # 生成验证令牌
            verification_token = self.generate_verification_token()
            token_expires = datetime.datetime.now() + datetime.timedelta(seconds=30)  # 30秒过期
            
            # 插入新用户（未验证状态）
            insert_query = """
            INSERT INTO purchase_orders.users (email, verification_token, token_expires)
            VALUES (%s, %s, %s)
            RETURNING id
            """
            cursor.execute(insert_query, (email_lower, verification_token, token_expires))
            user_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True, {"user_id": user_id, "verification_token": verification_token}
        except Exception as error:
            if conn:
                conn.rollback()
                conn.close()
            return False, f"注册用户时出错: {error}"

    def verify_user(self, token):
        """验证用户令牌"""
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"

        try:
            cursor = conn.cursor()
            
            # 查找令牌对应的用户
            check_query = """
            SELECT id, email, token_expires FROM purchase_orders.users 
            WHERE verification_token = %s AND is_verified = FALSE
            """
            cursor.execute(check_query, (token,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return False, "无效的验证令牌"

            user_id, email, token_expires = user
            
            # 检查令牌是否过期
            if datetime.datetime.now() > token_expires:
                cursor.close()
                conn.close()
                return False, "验证令牌已过期"

            cursor.close()
            conn.close()
            
            return True, {"user_id": user_id, "email": email}
        except Exception as error:
            if conn:
                conn.close()
            return False, f"验证用户时出错: {error}"

    def set_user_password(self, user_id, password):
        """设置用户密码"""
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"

        try:
            cursor = conn.cursor()
            
            # 生成密码哈希
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # 更新用户密码和验证状态
            update_query = """
            UPDATE purchase_orders.users 
            SET password_hash = %s, is_verified = TRUE, verification_token = NULL, token_expires = NULL
            WHERE id = %s
            """
            cursor.execute(update_query, (password_hash, user_id))
            
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                return False, "用户不存在"

            conn.commit()
            cursor.close()
            conn.close()
            
            return True, "密码设置成功"
        except Exception as error:
            if conn:
                conn.rollback()
                conn.close()
            return False, f"设置密码时出错: {error}"

    def change_user_password(self, user_id, old_password, new_password, skip_old_password_check=False):
        """修改用户密码（需要提供旧密码，除非skip_old_password_check为True）"""
        DEFAULT_PASSWORD = "Wefabricate123"
        DEFAULT_PASSWORD_HASH = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest()
        
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"

        try:
            cursor = conn.cursor()
            
            # 获取用户当前密码哈希
            select_query = """
            SELECT password_hash, is_verified FROM purchase_orders.users 
            WHERE id = %s
            """
            cursor.execute(select_query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return False, "用户不存在"
            
            current_password_hash, is_verified = user
            
            # 如果跳过旧密码检查（用于非verified用户首次设置密码）
            if not skip_old_password_check:
                # 验证旧密码
                old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
                
                # 对于非verified用户，允许使用默认密码作为旧密码
                if not is_verified:
                    if old_password_hash != DEFAULT_PASSWORD_HASH and old_password_hash != current_password_hash:
                        cursor.close()
                        conn.close()
                        return False, "旧密码错误，未验证用户请使用默认密码"
                else:
                    # 已验证用户必须提供正确的旧密码
                    if old_password_hash != current_password_hash:
                        cursor.close()
                        conn.close()
                        return False, "旧密码错误"
            
            # 生成新密码哈希
            new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            # 更新用户密码，如果是非verified用户，同时设置为verified
            if not is_verified:
                update_query = """
                UPDATE purchase_orders.users 
                SET password_hash = %s, is_verified = TRUE, verification_token = NULL, token_expires = NULL
                WHERE id = %s
                """
            else:
                update_query = """
                UPDATE purchase_orders.users 
                SET password_hash = %s
                WHERE id = %s
                """
            cursor.execute(update_query, (new_password_hash, user_id))
            
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                return False, "更新密码失败"

            conn.commit()
            cursor.close()
            conn.close()
            
            return True, "密码修改成功"
        except Exception as error:
            if conn:
                conn.rollback()
                conn.close()
            return False, f"修改密码时出错: {error}"

    def authenticate_user(self, email, password):
        """用户认证"""
        DEFAULT_PASSWORD = "Wefabricate123"
        DEFAULT_PASSWORD_HASH = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest()
        
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"

        try:
            cursor = conn.cursor()
            
            # 邮箱转换为小写进行查询（不区分大小写）
            email_lower = email.lower()
            
            # 获取用户信息
            select_query = """
            SELECT id, password_hash, is_verified FROM purchase_orders.users 
            WHERE LOWER(email) = %s
            """
            cursor.execute(select_query, (email_lower,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return False, "用户不存在"

            user_id, password_hash, is_verified = user
            
            # 对于未验证用户，允许使用默认密码登录
            if not is_verified:
                # 验证是否为默认密码
                if hashlib.sha256(password.encode()).hexdigest() != DEFAULT_PASSWORD_HASH:
                    cursor.close()
                    conn.close()
                    return False, "密码错误，未验证用户请使用默认密码"
                # 默认密码验证成功，返回用户信息（包含is_verified状态）
                cursor.close()
                conn.close()
                return True, {"user_id": user_id, "email": email, "is_verified": False, "needs_password_change": True}

            # 对于已验证用户，验证密码
            if hashlib.sha256(password.encode()).hexdigest() != password_hash:
                cursor.close()
                conn.close()
                return False, "密码错误"

            cursor.close()
            conn.close()
            
            return True, {"user_id": user_id, "email": email, "is_verified": True, "needs_password_change": False}
        except Exception as error:
            if conn:
                conn.close()
            return False, f"用户认证时出错: {error}"