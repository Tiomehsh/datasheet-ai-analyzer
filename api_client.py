import requests
from typing import Dict, List, Any
from config import Config

class APIClient:
    def __init__(self, api_key: str, api_type: str = "openai", api_base: str = None):
        self.api_key = api_key
        self.api_type = api_type
        self.api_config = Config.get_api_config(api_type, api_base)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_type == "azure":
            headers["api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            response = requests.get(
                self.api_config['models_url'],
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            
            if self.api_type == "azure":
                return ["gpt-35-turbo"]
            elif "data" in result:
                return [model["id"] for model in result["data"]]
            else:
                return ["gpt-3.5-turbo"]
                
        except Exception as e:
            print(f"获取模型列表失败: {str(e)}")
            return ["gpt-3.5-turbo"]

    def generate_completion(self, prompt: str, model: str = None, temperature: float = 0.5) -> str:
        """生成完成响应"""
        try:
            if not model:
                models = self.get_models()
                model = models[0] if models else "gpt-3.5-turbo"

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个Python数据分析专家，精通代码规范和pandas数据分析。请只返回代码，不要包含任何注释或说明。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 2000
            }

            response = requests.post(
                self.api_config['chat_url'],
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception("API返回的响应格式不正确")
                
        except Exception as e:
            return f"生成脚本时出错: {str(e)}"
