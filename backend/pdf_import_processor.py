import json
import os
from backend.db_pdf_processor import extract_wefaricate_data, extract_centurion_data, extract_magic_fx_data
from backend.models.database import insert_table_data

class PDFImportProcessor:
    def __init__(self, config_path="config/column_mapping.json", upload_folder="uploads"):
        self.config_path = config_path
        self.upload_folder = upload_folder
        self.mapping_config = self.load_mapping_config()
        
        # 确保上传文件夹存在
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def load_mapping_config(self):
        """加载映射配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def save_mapping_config(self):
        """保存映射配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.mapping_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_available_companies(self):
        """获取可用的公司列表"""
        # 返回固定的公司列表
        companies = ['wefabricate', 'centurion', 'magic_fx']
        return companies
    
    def add_company_mapping(self, company_name, pdf_patterns, table_columns, database_mapping):
        """添加新的公司映射配置"""
        self.mapping_config[company_name] = {
            "pdf_patterns": pdf_patterns,
            "table_columns": table_columns,
            "database_mapping": database_mapping
        }
        return self.save_mapping_config()
    
    def save_uploaded_file(self, file_data, filename):
        """保存上传的文件"""
        try:
            file_path = os.path.join(self.upload_folder, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            return file_path
        except Exception as e:
            print(f"保存上传文件失败: {e}")
            return None
    
    def process_pdf_by_company(self, pdf_path, company_name):
        """根据公司名称处理PDF文件"""
        # 根据公司类型调用相应的处理函数
        if company_name == 'wefabricate':
            data = extract_wefaricate_data(pdf_path)
            return data
        elif company_name == 'centurion':
            data = extract_centurion_data(pdf_path)
            return data
        elif company_name == 'magic_fx':
            data = extract_magic_fx_data(pdf_path)
            return data
        elif company_name.startswith('generic_wf'):
            # 通用WF处理方式
            data = extract_wefaricate_data(pdf_path)
            return data
        elif company_name.startswith('generic_non_wf'):
            # 通用Non-WF处理方式
            data = extract_centurion_data(pdf_path)
            return data
        else:
            # 对于其他公司，使用默认处理方式
            data = extract_wefaricate_data(pdf_path)
            return data
    
    def process_pdf_with_duplicate_check(self, pdf_path, company_name):
        """处理PDF文件并检查重复数据"""
        try:
            print(f"正在处理: {pdf_path}")
            data = self.process_pdf_by_company(pdf_path, company_name)
            
            if not data:
                return {
                    "success": False,
                    "error": "未从PDF中提取到有效数据"
                }
            
            # 为每条数据添加公司字段
            for item in data:
                item['company'] = company_name
            
            # 确定目标表名
            table_name = 'wf_open'
            if company_name == 'centurion' or company_name == 'magic_fx' or 'non_wf' in company_name:
                table_name = 'non_wf_open'
            
            # 检查重复数据
            duplicates = self.check_duplicates(table_name, data)
            
            return {
                "success": True,
                "data": data,
                "duplicates": duplicates,
                "table_name": table_name
            }
        except Exception as e:
            print(f"处理 {pdf_path} 时出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_duplicates(self, table_name, data_list):
        """检查数据列表中是否存在主键冲突"""
        from backend.models.database import DatabaseManager
        db_manager = DatabaseManager()
        
        try:
            duplicates = db_manager.check_duplicates(table_name, data_list)
            return duplicates
        except Exception as e:
            print(f"检查重复数据时出错: {e}")
            return []
    
    def insert_data_with_check(self, table_name, data_list, user_email=None):
        """插入数据，如果有重复则覆盖，并记录操作日志"""
        try:
            success_count = 0
            
            # 如果没有提供用户邮箱，使用默认值
            if user_email is None:
                user_email = "pdf_importer@example.com"
            
            # 逐条插入数据并记录操作日志
            for data in data_list:
                # 使用数据库管理器的插入方法，它会处理重复数据的情况
                from backend.models.database import insert_table_data
                success, message = insert_table_data(table_name, data, user_email)
                if success:
                    success_count += 1
                else:
                    print(f"插入数据时出错: {message}")
            
            return {
                "success": True,
                "count": success_count
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_multiple_pdfs(self, pdf_files, company_name):
        """处理多个PDF文件"""
        all_data = []
        success_count = 0
        error_count = 0
        
        for pdf_path in pdf_files:
            try:
                print(f"正在处理: {pdf_path}")
                data = self.process_pdf_by_company(pdf_path, company_name)
                if data:
                    # 为每条数据添加公司字段
                    for item in data:
                        item['company'] = company_name
                    all_data.extend(data)
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"处理 {pdf_path} 时出错: {e}")
                error_count += 1
        
        return {
            "data": all_data,
            "success_count": success_count,
            "error_count": error_count
        }