from backend.models.user_model import UserManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from urllib.parse import urljoin
from backend.utils.jwt_utils import generate_token, token_required


class UserController:
    def __init__(self):
        self.user_manager = UserManager()
        self.token_required = token_required  # 添加token_required装饰器

    def send_verification_email(self, email, token):
        """发送验证邮件"""
        try:
            # 动态读取环境变量（每次调用时刷新）
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.qq.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SENDER_EMAIL', '')
            sender_password = os.getenv('SENDER_PASSWORD', '')
            app_base_url = os.getenv('APP_BASE_URL', 'http://localhost:5000')
            
            # 检查是否启用邮件功能
            email_enabled = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'
            if not email_enabled:
                print("邮件功能已禁用，跳过发送邮件")
                return True, "注册成功（邮件功能已禁用）"
            
            # 检查必要的配置是否存在
            if not sender_email or not sender_password:
                return False, "邮件服务器配置不完整，请检查SENDER_EMAIL和SENDER_PASSWORD环境变量"
            
            # 创建邮件内容
            verification_link = f"{app_base_url}/set_password.html?token={token}"
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Wefabricate系统注册验证"
            message["From"] = sender_email
            message["To"] = email

            # 创建HTML邮件内容
            html = f"""
            <html>
              <body>
                <p>您好!</p>
                <p>感谢您注册Wefabricate系统。</p>
                <p>请点击以下链接完成注册：</p>
                <p><a href="{verification_link}">点击这里验证您的邮箱并设置密码</a></p>
                <p>或者复制以下链接到浏览器地址栏：</p>
                <p>{verification_link}</p>
                <p>此链接将在24小时后过期。</p>
                <p>如果您没有注册我们的系统，请忽略此邮件。</p>
                <br>
                <p>谢谢!</p>
                <p>Wefabricate团队</p>
              </body>
            </html>
            """

            # 将HTML内容添加到邮件中
            html_part = MIMEText(html, "html")
            message.attach(html_part)

            # 尝试发送邮件 - 使用TLS (端口587)
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.set_debuglevel(1)  # 启用调试模式
                server.starttls()  # 启用TLS加密
                # 对于Outlook，需要使用OAuth2认证
                # 这里作为备用，实际上已经收集了OAuth2 token
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())
                server.quit()
                return True, "验证邮件已发送 (TLS连接)"
            except smtplib.SMTPAuthenticationError as tls_auth_error:
                # SMTP认证失败
                print(f"TLS认证失败: {tls_auth_error}")
                return False, f"SMTP认证失败，请检查邮箱和授权码：{str(tls_auth_error)}"
            except Exception as tls_error:
                # 如果TLS失败，尝试SSL (端口465)
                try:
                    import ssl
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(smtp_server, 465, context=context)
                    server.set_debuglevel(1)  # 启用调试模式
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, email, message.as_string())
                    server.quit()
                    return True, "验证邮件已发送 (SSL连接)"
                except Exception as ssl_error:
                    # 如果都失败，返回详细的错误信息
                    return False, f"SMTP连接失败: TLS错误: {str(tls_error)}, SSL错误: {str(ssl_error)}"

        except smtplib.SMTPAuthenticationError as e:
            return False, f"邮件认证失败，请检查邮箱和授权码是否正确: {str(e)}"
        except smtplib.SMTPException as e:
            return False, f"SMTP服务器错误: {str(e)}"
        except Exception as e:
            return False, f"发送验证邮件时出错: {str(e)}"

    def register_user(self, email, password):
        """用户注册"""
        # 注册用户
        success, result = self.user_manager.register_user(email)
        
        if not success:
            return False, result

        # result是一个字典，包含 user_id 和 verification_token
        user_id = result['user_id']
        
        # 注册成功，不发送邮件，直接返回用户ID
        return True, {"user_id": user_id, "email": email, "message": "注册成功，请设置密码"}

    def verify_user_token(self, token):
        """验证用户令牌"""
        success, result = self.user_manager.verify_user(token)
        
        if not success:
            return False, result

        return True, result

    def set_user_password(self, user_id, password):
        """设置用户密码"""
        success, message = self.user_manager.set_user_password(user_id, password)
        return success, message

    def login_user(self, email, password):
        """用户登录并生成token"""
        # 用户认证
        success, result = self.user_manager.authenticate_user(email, password)
        
        if not success:
            return False, result
        
        # 生成JWT token
        user_id = result['user_id']
        token = generate_token(user_id, email)
        
        return True, {
            'user': result,
            'token': token,
            'needs_password_change': result.get('needs_password_change', False)
        }

    def change_password(self, user_id, old_password, new_password):
        """修改用户密码"""
        success, message = self.user_manager.change_user_password(user_id, old_password, new_password)
        return success, message
