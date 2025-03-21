import json
import os
from typing import Dict, Any

class Config:
    _instance = None
    _config_file = 'config.json'
    
    # 类属性定义
    MAX_RETRIES = 3
    UPLOAD_FOLDER = 'uploads'
    API_TYPE = 'openai'
    API_BASE = None
    API_KEY = None
    
    def __init__(self):
        self.load_config()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance
    
    def load_config(self):
        """从配置文件加载配置"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # 更新类属性
                    for key, value in config_data.items():
                        if hasattr(Config, key):
                            setattr(Config, key, value)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                'MAX_RETRIES': Config.MAX_RETRIES,
                'UPLOAD_FOLDER': Config.UPLOAD_FOLDER,
                'API_TYPE': Config.API_TYPE,
                'API_BASE': Config.API_BASE,
                'API_KEY': Config.API_KEY
            }
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(Config, key):
                setattr(Config, key, value)
        return self.save_config()
    
    @classmethod
    def get_api_config(cls, api_type: str = None, api_base: str = None) -> Dict[str, str]:
        """获取API配置"""
        # 优先使用传入的参数，否则使用保存的配置
        actual_type = api_type or cls.API_TYPE
        actual_base = api_base or cls.API_BASE or "https://api.openai.com"
        
        base_url = actual_base.rstrip('/')
        
        if actual_type == 'custom':
            return {
                'models_url': f"{base_url}/v1/models",
                'chat_url': f"{base_url}/v1/chat/completions"
            }
        elif actual_type == 'azure':
            return {
                'models_url': f"{base_url}/openai/models?api-version=2024-02-15-preview",
                'chat_url': f"{base_url}/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-02-15-preview"
            }
        else:  # openai
            return {
                'models_url': f"{base_url}/v1/models",
                'chat_url': f"{base_url}/v1/chat/completions"
            }
