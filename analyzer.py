import pandas as pd
from typing import Dict, Any, Tuple, List, Union
from config import Config
from api_client import APIClient
from script_executor import ScriptExecutor
import json

def create_excel_info(df: pd.DataFrame) -> Dict[str, Any]:
    """创建Excel文件信息字典，确保所有数据都是JSON可序列化的"""
    dtypes_dict = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
    columns = [str(col) for col in df.columns]
    preview_str = df.head().to_string(index=False)
    
    return {
        'columns': columns,
        'preview': preview_str,
        'row_count': len(df),
        'dtypes': dtypes_dict
    }

class Analyzer:
    def __init__(self, api_key: str, api_base: str = None, api_type: str = "openai"):
        self.api_client = APIClient(api_key, api_type, api_base)
        self.script_executor = ScriptExecutor()

    def get_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.api_client.get_models()

    def _build_prompt(self, user_query: str, excel_info: Dict[str, Any], error_context: str = None) -> str:
        """构建分析提示"""
        type_info = "\n".join([f"{col}: {dtype}" for col, dtype in excel_info['dtypes'].items()])
        
        base_prompt = f"""
分析任务：
根据以下要求编写一个完整、规范的Python数据分析脚本。使用提供的结构化输出工具记录分析结果。

用户需求：
{user_query}

Excel文件信息：
列名及数据类型：
{type_info}

数据预览：
{excel_info['preview']}

分析要求：
1. 关注核心需求
   根据用户的实际查询需求进行分析，如果用户没有要求基础统计分析，
   则无需输出这些信息。

2. 数据处理步骤
   - 针对性地处理与查询相关的数据
   - 必要时进行类型转换和清洗
   - 按需进行分组和聚合

3. 统计输出建议
   - 只输出与用户查询直接相关的统计数据
   - 必要时才进行空值统计
   - 避免冗余的基础统计信息

4. 结果展示
   使用结构化输出工具记录结果：
   ```python
   # 开始一个新的分析部分
   output.start_section("基础统计")
   
   # 添加统计数据
   output.add_stat("总行数", len(df))
   output.add_stat("平均值", mean_value)
   
   # 添加描述性文本
   output.add_text("该数据集质量良好，完整性高")
   
   # 添加表格数据
   output.add_table(summary_df, "数据概览")
   
   # 结束当前部分
   output.end_section()
   ```

4. 异常处理
   - 空值处理
   - 类型转换异常处理
   - 边界条件检查
"""
        
        if error_context:
            base_prompt += f"""
修正说明：
前次代码存在以下问题：
{error_context}

请特别注意：
1. 正确的代码缩进
2. 完整的代码块结构
3. 异常处理的完整性
4. 数据类型的安全转换
"""

        base_prompt += """
技术规范：
1. 函数定义：
   ```python
   def analyze_data(df):
    try:
        df = df.copy()
        
        output.start_section("分析结果")
        
        # 数据处理
        df['成绩'] = pd.to_numeric(df['成绩'], errors='coerce')
        result_df = df[df['成绩'] < 60].copy()
        
        # 统计和输出
        output.add_stat("筛选结果数量", len(result_df))
        
        if len(result_df) > 0:
            result_df = result_df[['班级', '学号', '姓名', '成绩']].sort_values('成绩')
            output.add_table(result_df, "详细名单")
        
        output.end_section()
        return df
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
   ```

2. 代码结构规范：
   - 所有代码块使用4空格缩进
   - if/for/while等语句后必须缩进
   - try-except块完整包裹主要逻辑
   - 不要包含main函数或__main__检查
   - 不要包含任何注释或功能说明

3. 数据处理规范：
   - 使用 df = df.copy() 创建数据副本
   - 数值比较前使用 pd.to_numeric(series, errors='coerce')
   - 使用 fillna() 或 dropna() 处理空值
   - 字符串处理使用 str 访问器

4. 输出规范：
   - 使用结构化输出工具记录所有结果
   - 合理划分分析部分
   - 关键数据使用 add_stat 记录
   - 表格数据使用 add_table 展示

请直接返回analyze_data函数的完整实现，不要包含任何注释、说明或其他代码。确保代码格式规范、结构完整、异常处理充分。
"""
        return base_prompt

    def analyze(self, user_query: str, excel_info: Dict[str, Any], excel_path: str, model: str = None) -> Tuple[str, Union[Dict[str, Any], str], str]:
        """
        分析数据并返回结果。
        返回元组: (生成的代码, 执行结果, 错误/状态信息)
        """
        script = None
        error_context = None
        attempts = 0
        
        while attempts < Config.MAX_RETRIES:
            attempts += 1
            try:
                # 生成脚本
                prompt = self._build_prompt(user_query, excel_info, error_context)
                script = self.api_client.generate_completion(prompt, model)
                
                if script.startswith("生成脚本时出错"):
                    error_context = f"生成脚本失败: {script}"
                    continue
                    
                # 清理和格式化代码
                script = self.script_executor._clean_code(script)
                
                # 执行脚本
                result, success = self.script_executor.execute(script, excel_path)
                
                if not success:
                    error_context = result
                    if attempts < Config.MAX_RETRIES:
                        continue
                    else:
                        return script, "", f"尝试{Config.MAX_RETRIES}次后失败。最后的错误：{error_context}"
                else:
                    # 检查是否返回了结构化结果
                    is_structured = isinstance(result, dict) and 'sections' in result
                    
                    # 确保结构化结果中的所有数据都是可序列化的
                    if is_structured:
                        try:
                            # 尝试序列化结果，确保它可以被JSON化
                            json.dumps(result)
                        except Exception as e:
                            print(f"结果序列化失败: {str(e)}")
                            # 如果序列化失败，返回错误信息
                            return script, str(result), f"成功（尝试次数：{attempts}）- 但结果无法序列化为JSON"
                            
                    status = f"成功（尝试次数：{attempts}）" + (" - 结构化输出" if is_structured else "")
                    return script, result, status
                    
            except Exception as e:
                error_context = str(e)
                if attempts < Config.MAX_RETRIES:
                    continue
                else:
                    return script or "生成失败", "", f"重试{Config.MAX_RETRIES}次后失败。最后的错误：{error_context}"
        
        return script or "生成失败", "", f"重试次数过多（{Config.MAX_RETRIES}次），停止重试。最后的错误：{error_context}"
