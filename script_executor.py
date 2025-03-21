import os
import tempfile
import subprocess
import traceback
import re
import json
from typing import Tuple, Dict, Any, Union

class ScriptExecutor:
    @staticmethod
    def _clean_code(code: str) -> str:
        """清理代码块标记和说明文本"""
        # 移除代码块标记
        code = re.sub(r'```python[^\n]*\n', '', code)
        code = re.sub(r'```\n?', '', code)
        
        # 移除代码后的说明部分
        code = code.split('\n\n这段代码实现了')[0]
        code = code.split('\n\n功能说明：')[0]
        code = code.split('\n\n代码说明：')[0]
        
        # 确保代码以换行符结束
        if not code.endswith('\n'):
            code += '\n'
            
        return code.strip()

    @staticmethod
    def execute(script: str, excel_path: str) -> Tuple[Union[Dict[str, Any], str], bool]:
        """执行生成的脚本并返回结果和执行状态"""
        try:
            # 创建一个临时文件来存储脚本
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                full_script = f"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import sys
import traceback
import json
import os

class AnalysisOutput:
    def __init__(self):
        self.sections = []
        self.current_section = None
    
    def start_section(self, title: str):
        if self.current_section:
            self.sections.append(self.current_section)
        self.current_section = {{"title": title, "content": [], "data": {{}}, "charts": []}}
    
    def add_text(self, text: str):
        if self.current_section:
            self.current_section["content"].append({{"type": "text", "text": text}})
    
    def add_table(self, df: pd.DataFrame, description: str = ""):
        if self.current_section:
            self.current_section["content"].append({{
                "type": "table",
                "data": df.to_dict(orient="records"),
                "description": description
            }})
    
    def add_stat(self, name: str, value: Any):
        if self.current_section:
            self.current_section["data"][name] = str(value)
    
    def end_section(self):
        if self.current_section:
            self.sections.append(self.current_section)
            self.current_section = None
    
    def get_output(self) -> dict:
        if self.current_section:
            self.end_section()
        return {{"sections": self.sections}}

# 创建全局输出对象
output = AnalysisOutput()
orig_print = print

def print(*args, **kwargs):
    text = " ".join(str(arg) for arg in args)
    output.add_text(text)
    orig_print(*args, **kwargs)

{script}

def main():
    try:
        # 根据文件扩展名选择读取方式
        file_ext = os.path.splitext(r'{excel_path}')[1].lower()
        if file_ext == '.csv':
            df = pd.read_csv(r'{excel_path}')
        else:
            df = pd.read_excel(r'{excel_path}')
        df.columns = df.columns.astype(str)
        
        # 执行分析
        analyze_data(df)
        
        # 输出结构化结果
        result = output.get_output()
        print("\\n=== ANALYSIS_RESULT_JSON_START ===")
        print(json.dumps(result))
        print("=== ANALYSIS_RESULT_JSON_END ===")
        
    except Exception as e:
        print(f"执行出错: {{str(e)}}", file=sys.stderr)
        print("\\n详细错误信息:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
"""
                f.write(full_script)
                temp_path = f.name
            
            # 执行脚本并捕获输出
            result = subprocess.run(['python', temp_path], 
                                 capture_output=True, 
                                 text=True)
            
            # 删除临时文件
            os.unlink(temp_path)
            
            if result.returncode != 0:
                return f"执行脚本时出错:\n{result.stderr}", False
            
            # 尝试从输出中提取JSON结果
            try:
                output = result.stdout
                json_start = output.find("=== ANALYSIS_RESULT_JSON_START ===")
                json_end = output.find("=== ANALYSIS_RESULT_JSON_END ===")
                
                if json_start != -1 and json_end != -1:
                    json_str = output[json_start + len("=== ANALYSIS_RESULT_JSON_START ==="):json_end].strip()
                    structured_result = json.loads(json_str)
                    return structured_result, True
            except:
                pass
            
            # 如果无法提取结构化结果，返回原始输出
            output = result.stdout if result.stdout.strip() else "执行成功但没有输出"
            return output, True
            
        except Exception as e:
            return f"执行脚本时发生错误:\n{traceback.format_exc()}", False
