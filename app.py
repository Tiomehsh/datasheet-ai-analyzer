from flask import Flask, request, jsonify, render_template, session
import os
import pandas as pd
from werkzeug.utils import secure_filename
from config import Config
from analyzer import Analyzer, create_excel_info

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 添加session支持

# 配置上传文件夹
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_api_config', methods=['POST'])
def save_api_config():
    try:
        data = request.get_json()
        api_config = data.get('api_config', {})
        
        config = Config.get_instance()
        
        # 如果是空配置，则只返回当前配置
        if not api_config:
            return jsonify({
                'api_config': {
                    'type': Config.API_TYPE,
                    'key': Config.API_KEY,
                    'base': Config.API_BASE,
                    'max_retries': Config.MAX_RETRIES
                }
            })
        
        # 否则更新配置
        success = config.update_config(
            API_KEY=api_config.get('key'),
            API_BASE=api_config.get('base'),
            API_TYPE=api_config.get('type', 'openai'),
            MAX_RETRIES=api_config.get('max_retries', 3)
        )
        
        if success:
            return jsonify({
                'message': 'API配置已保存',
                'api_config': {
                    'type': Config.API_TYPE,
                    'key': Config.API_KEY,
                    'base': Config.API_BASE,
                    'max_retries': Config.MAX_RETRIES
                }
            })
        else:
            return jsonify({'error': '保存配置失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['POST'])
def get_models():
    try:
        data = request.get_json()
        api_config = data.get('api_config', {})
        
        # 保存API配置
        config = Config.get_instance()
        config.update_config(
            API_KEY=api_config.get('key'),
            API_BASE=api_config.get('base'),
            API_TYPE=api_config.get('type', 'openai'),
            MAX_RETRIES=api_config.get('max_retries', 3)
        )
        
        analyzer = Analyzer(
            api_key=api_config.get('key'),
            api_base=api_config.get('base'),
            api_type=api_config.get('type', 'openai')
        )
        
        models = analyzer.get_models()
        return jsonify({'models': models})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # 根据文件扩展名选择读取方式
            file_ext = os.path.splitext(filepath)[1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            
            # 创建文件分析信息
            analysis = create_excel_info(df)
            
            # 创建两个预览：一个简短（10行）一个完整（最多100行）
            preview_short = df.head(10).to_html(classes='table table-striped table-bordered', index=False)
            preview_full = df.head(100).to_html(classes='table table-striped table-bordered', index=False)
            
            analysis['preview'] = f"""
                <div class="preview-short">{preview_short}</div>
                <div class="preview-full" style="display: none;">{preview_full}</div>
            """
            
            return jsonify({
                'filename': filename,
                'analysis': analysis
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def perform_analysis(data):
    """执行分析并返回结果"""
    filename = data.get('filename')
    query = data.get('query')
    model = data.get('model')
    api_config = data.get('api_config', {})
    retry_count = data.get('retry_count', 0)
    
    # 保存API配置
    config = Config.get_instance()
    config.update_config(
        API_KEY=api_config.get('key'),
        API_BASE=api_config.get('base'),
        API_TYPE=api_config.get('type', 'openai'),
        MAX_RETRIES=api_config.get('max_retries', 3)
    )
    
    if not filename or not query:
        return jsonify({'error': '缺少必要参数'}), 400
        
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
        
    # 根据文件扩展名读取文件
    file_ext = os.path.splitext(filepath)[1].lower()
    if file_ext == '.csv':
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
    excel_info = create_excel_info(df)
    
    # 创建分析器实例
    analyzer = Analyzer(
        api_key=api_config.get('key'),
        api_base=api_config.get('base'),
        api_type=api_config.get('type', 'openai')
    )
    
    # 分析数据
    script, result, status = analyzer.analyze(query, excel_info, filepath, model)
    
    response_data = {
        'script': script,
        'retry_count': retry_count,
        'can_retry': retry_count < Config.MAX_RETRIES - 1,
        'attempt': retry_count + 1,
        'max_attempts': Config.MAX_RETRIES
    }
    
    if status.startswith("成功"):
        response_data.update({
            'result': result,
            'status': status,
            'success': True
        })
    else:
        response_data.update({
            'error': f"第{retry_count + 1}次尝试失败 - {status}",
            'details': result or '无执行结果',
            'success': False
        })
    
    # 如果返回的是结构化结果，直接使用它
    if isinstance(result, dict) and 'sections' in result:
        response_data['result'] = result
    else:
        # 如果是普通文本结果，包装成结构化格式
        response_data['result'] = {
            'sections': [{
                'title': '分析结果',
                'content': [{'type': 'text', 'text': result}],
                'data': {}
            }]
        }
    
    return jsonify(response_data)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        
        # 保存当前请求信息到session
        session['last_analysis'] = data
        
        return perform_analysis(data)
        
    except Exception as e:
        retry_count = request.get_json().get('retry_count', 0)
        return jsonify({
            'error': str(e),
            'script': '生成或执行脚本时发生错误',
            'success': False,
            'retry_count': retry_count,
            'can_retry': retry_count < Config.MAX_RETRIES - 1,
            'attempt': retry_count + 1,
            'max_attempts': Config.MAX_RETRIES
        }), 500

@app.route('/retry', methods=['POST'])
def retry_analysis():
    """重试上一次的分析请求"""
    try:
        last_analysis = session.get('last_analysis')
        if not last_analysis:
            return jsonify({'error': '没有找到上一次的分析请求'}), 404
            
        # 增加重试次数
        last_analysis['retry_count'] = last_analysis.get('retry_count', 0) + 1
        
        # 重新保存更新后的请求信息
        session['last_analysis'] = last_analysis
        
        # 重新发送分析请求
        return perform_analysis(last_analysis)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1832, debug=True)
