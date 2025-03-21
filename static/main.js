let currentFilename = null;
let apiConfig = {};
let isAnalyzing = false;

function togglePreview(element) {
    const container = element.previousElementSibling;
    const previewShort = container.querySelector('.preview-short');
    const previewFull = container.querySelector('.preview-full');
    const isExpanded = container.classList.toggle('expanded');
    
    if (isExpanded) {
        previewShort.style.display = 'none';
        previewFull.style.display = 'block';
        element.textContent = '点击收起';
    } else {
        previewFull.style.display = 'none';
        previewShort.style.display = 'block';
        element.textContent = '点击展开';
        container.scrollTop = 0;
    }
}

// API配置相关
document.getElementById('apiType').addEventListener('change', function() {
    const apiBaseGroup = document.getElementById('apiBaseGroup');
    apiBaseGroup.style.display = this.value !== 'openai' ? 'block' : 'none';
    
    const apiBase = document.getElementById('apiBase');
    if (this.value === 'custom') {
        apiBase.placeholder = "例如: https://api.example.com";
    } else if (this.value === 'azure') {
        apiBase.placeholder = "例如: https://your-resource.openai.azure.com";
    }
});

// 页面加载时初始化
window.onload = async () => {
    // 初始化代码高亮
    hljs.configure({
        languages: ['python'],
        tabReplace: '    '
    });
    hljs.highlightAll();
    
    // 获取保存的配置
    try {
        // 加载保存的配置
        const configResponse = await fetch('/save_api_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_config: {} })  // 空配置触发加载
        });
        const configData = await configResponse.json();
        
        if (!configData.error && configData.api_config) {
            // 填充表单
            const apiTypeSelect = document.getElementById('apiType');
            apiTypeSelect.value = configData.api_config.type || 'openai';
            document.getElementById('apiKey').value = configData.api_config.key || '';
            document.getElementById('apiBase').value = configData.api_config.base || '';
            document.getElementById('maxRetries').value = configData.api_config.max_retries || 3;
            
            // 触发apiType的change事件来更新UI状态
            apiTypeSelect.dispatchEvent(new Event('change'));
            
            // 更新全局配置
            apiConfig = configData.api_config;
            
            // 更新UI状态
            if (apiConfig.key) {
                const apiStatus = document.getElementById('apiStatus');
                apiStatus.textContent = '已连接';
                apiStatus.className = 'api-status connected';
                document.getElementById('queryCard').style.display = 'block';

                // 获取可用模型列表
                const modelsResponse = await fetch('/models', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ api_config: apiConfig })
                });
                const modelsData = await modelsResponse.json();

                if (!modelsData.error) {
                    const modelSelect = document.getElementById('modelSelect');
                    modelSelect.innerHTML = modelsData.models.map(model => 
                        `<option value="${model}">${model}</option>`
                    ).join('');
                    document.getElementById('modelsCard').style.display = 'block';
                } else {
                    console.error('获取模型列表失败:', modelsData.error);
                }
            }
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
};

document.getElementById('apiConfig').onsubmit = async (e) => {
    e.preventDefault();
    apiConfig = {
        type: document.getElementById('apiType').value,
        key: document.getElementById('apiKey').value,
        base: document.getElementById('apiBase').value,
        max_retries: parseInt(document.getElementById('maxRetries').value) || 3
    };
    
    try {
        const response = await fetch('/save_api_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_config: apiConfig })
        });
        const data = await response.json();
        
        if (data.error) {
            alert('保存配置失败: ' + data.error);
            return;
        }
        
        const apiStatus = document.getElementById('apiStatus');
        apiStatus.textContent = '已连接';
        apiStatus.className = 'api-status connected';
        
        document.getElementById('queryCard').style.display = 'block';
        alert('API配置已保存');
    } catch (error) {
        alert('保存配置时发生错误');
        console.error(error);
    }
};

document.getElementById('fileInput').onchange = async (e) => {
    if (!apiConfig.key) {
        alert('请先配置API');
        return;
    }

    if (!e.target.files || !e.target.files[0]) return;
    
    const formData = new FormData();
    formData.append('file', e.target.files[0]);
    formData.append('api_config', JSON.stringify(apiConfig));

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        currentFilename = data.filename;
        document.getElementById('fileOverview').style.display = 'block';
        document.getElementById('rowCount').textContent = data.analysis.row_count;
        document.getElementById('columnsList').innerHTML = data.analysis.columns.join(', ');
        document.getElementById('previewData').innerHTML = data.analysis.preview;
        
        // 初始化预览状态
        const previewContainer = document.querySelector('.preview-container');
        const previewToggle = document.querySelector('.preview-toggle');
        const previewShort = previewContainer.querySelector('.preview-short');
        const previewFull = previewContainer.querySelector('.preview-full');
        
        // 重置预览状态
        previewContainer.classList.remove('expanded');
        previewShort.style.display = 'block';
        previewFull.style.display = 'none';
        previewToggle.textContent = '点击展开';
        
        document.getElementById('analysisResults').style.display = 'block';
    } catch (error) {
        alert('上传文件时发生错误');
        console.error(error);
    }
};

document.getElementById('analyzeBtn').onclick = async () => {
    if (!apiConfig.key) {
        alert('请先配置API');
        return;
    }

    const query = document.getElementById('queryInput').value.trim();
    if (!query) {
        alert('请输入分析需求');
        return;
    }

    await performAnalysis(0);
};

document.getElementById('retryBtn').onclick = async () => {
    if (isAnalyzing) return;
    
    const currentRetries = parseInt(document.getElementById('retryCount').textContent) || 0;
    await performAnalysis(currentRetries + 1);
};

async function performAnalysis(retryCount = 0) {
    if (isAnalyzing) return;
    isAnalyzing = true;

    try {
        const modelSelect = document.getElementById('modelSelect');
        const selectedModel = modelSelect.value;

        // 禁用按钮
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('retryBtn').disabled = true;
        document.getElementById('regenerateBtn').disabled = true;

        // 重置显示状态
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('statusMessage').style.display = 'none';
        document.getElementById('retrySection').style.display = 'none';
        
        // 显示进度信息
        document.getElementById('currentAttempt').textContent = retryCount + 1;
        document.getElementById('progressSection').style.display = 'block';

        document.getElementById('generatedScript').textContent = '正在生成分析脚本...';
        document.getElementById('analysisOutput').textContent = '';

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFilename,
                query: document.getElementById('queryInput').value.trim(),
                model: selectedModel,
                api_config: apiConfig,
                retry_count: retryCount
            })
        });
        
        const data = await response.json();
        handleAnalysisResponse(data);
    } catch (error) {
        handleAnalysisError(error);
    } finally {
        document.getElementById('analyzeBtn').disabled = false;
        document.getElementById('retryBtn').disabled = false;
        document.getElementById('regenerateBtn').disabled = false;
        document.getElementById('progressSection').style.display = 'none';
        isAnalyzing = false;
    }
}

// 初始化复制按钮功能
document.querySelectorAll('.copy-btn').forEach(button => {
    button.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const targetElement = document.getElementById(targetId);
        const textToCopy = targetElement.textContent;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="bi bi-check"></i> 已复制';
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        }).catch(err => {
            console.error('复制失败:', err);
        });
    });
});

function renderAnalysisResult(result) {
    const outputElement = document.getElementById('analysisOutput');
    outputElement.innerHTML = '';
    
    if (!result || !result.sections) {
        outputElement.textContent = '无分析结果';
        return;
    }
    
    const container = document.createElement('div');
    
    result.sections.forEach(section => {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'mb-4';
        
        // 添加标题
        const title = document.createElement('h5');
        title.className = 'mb-3';
        title.textContent = section.title;
        sectionDiv.appendChild(title);
        
        // 添加统计数据
        if (Object.keys(section.data).length > 0) {
            const statsDiv = document.createElement('div');
            statsDiv.className = 'stats-grid mb-3';
            
            Object.entries(section.data).forEach(([key, value]) => {
                const statBox = document.createElement('div');
                statBox.className = 'stat-box';
                
                // 检查值是否为对象（字典）
                if (value && typeof value === 'object' && value.constructor === Object) {
                    // 对于字典类型，创建一个格式化的列表
                    let formattedList = '<ul class="list-unstyled mb-0">';
                    Object.entries(value).forEach(([k, v]) => {
                        formattedList += `<li><span class="fw-bold">${k}</span>: ${v}</li>`;
                    });
                    formattedList += '</ul>';
                    
                    statBox.innerHTML = `
                        <div class="stat-label">${key}</div>
                        <div class="stat-value-list">${formattedList}</div>
                    `;
                } else {
                    // 对于普通值，使用原来的展示方式
                    statBox.innerHTML = `
                        <div class="stat-label">${key}</div>
                        <div class="stat-value">${value}</div>
                    `;
                }
                
                statsDiv.appendChild(statBox);
            });
            
            sectionDiv.appendChild(statsDiv);
        }
        
        // 添加内容
        section.content.forEach(item => {
            switch (item.type) {
                case 'text':
                    const textDiv = document.createElement('div');
                    textDiv.className = 'mb-3';
                    textDiv.textContent = item.text;
                    sectionDiv.appendChild(textDiv);
                    break;
                    
                case 'table':
                    const tableContainer = document.createElement('div');
                    tableContainer.className = 'table-responsive mb-3';
                    
                    if (item.description) {
                        const desc = document.createElement('div');
                        desc.className = 'mb-2';
                        desc.textContent = item.description;
                        tableContainer.appendChild(desc);
                    }
                    
                    const table = document.createElement('table');
                    table.className = 'table table-sm table-bordered table-hover';
                    
                    // 创建表头
                    if (item.data && item.data.length > 0) {
                        const thead = document.createElement('thead');
                        const headerRow = document.createElement('tr');
                        Object.keys(item.data[0]).forEach(key => {
                            const th = document.createElement('th');
                            th.textContent = key;
                            headerRow.appendChild(th);
                        });
                        thead.appendChild(headerRow);
                        table.appendChild(thead);
                        
                        // 创建表体
                        const tbody = document.createElement('tbody');
                        item.data.forEach(row => {
                            const tr = document.createElement('tr');
                            Object.values(row).forEach(value => {
                                const td = document.createElement('td');
                                td.textContent = value;
                                tr.appendChild(td);
                            });
                            tbody.appendChild(tr);
                        });
                        table.appendChild(tbody);
                    }
                    
                    tableContainer.appendChild(table);
                    sectionDiv.appendChild(tableContainer);
                    break;
            }
        });
        
        container.appendChild(sectionDiv);
    });
    
    outputElement.appendChild(container);
}

document.getElementById('regenerateBtn').onclick = async () => {
    if (isAnalyzing) return;
    await performAnalysis(0);  // 从零开始重新生成
};

function handleAnalysisResponse(data) {
    // 显示重新生成按钮（仅在分析成功时）
    const regenerateBtn = document.getElementById('regenerateBtn');
    regenerateBtn.style.display = data.success ? 'block' : 'none';
    // 更新脚本显示
    const scriptElement = document.getElementById('generatedScript');
    scriptElement.textContent = data.script || '生成脚本失败';
    hljs.highlightElement(scriptElement);
    
    // 渲染结构化结果
    renderAnalysisResult(data.result);
    
    // 更新重试信息
    document.getElementById('retryCount').textContent = data.retry_count || 0;
    document.getElementById('currentAttempt').textContent = data.attempt || 1;
    document.getElementById('maxAttempts').textContent = data.max_attempts || 3;

    const retrySection = document.getElementById('retrySection');
    if (!data.success && data.can_retry) {
        retrySection.style.display = 'block';
        document.getElementById('retryBtn').disabled = false;
    } else {
        retrySection.style.display = 'none';
    }

    if (data.error) {
        // 显示错误信息和详细信息
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.style.display = 'block';
        errorMessage.innerHTML = `
            <strong>错误信息：</strong><br>
            ${data.error}<br>
            ${data.details ? `<strong>详细信息：</strong><br><pre class="mt-2">${data.details}</pre>` : ''}
        `;
        document.getElementById('analysisOutput').textContent = '';
    } else {
    // 显示分析结果和状态
    document.getElementById('errorMessage').style.display = 'none';
    if (data.status) {
        document.getElementById('statusText').textContent = data.status;
        document.getElementById('statusMessage').style.display = 'block';
    }
    }
}

function handleAnalysisError(error) {
    document.getElementById('errorMessage').textContent = '分析过程中发生错误';
    document.getElementById('errorMessage').style.display = 'block';
    console.error(error);
}
