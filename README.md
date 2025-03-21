# DataSheet AI Analyzer

An intelligent Flask-based web application for analyzing Excel and CSV files using AI, supporting natural language queries and data analysis.

English | [简体中文](README_CN.md)

## Features

- 🤖 AI-powered data analysis
- 📊 Support for Excel (.xlsx, .xls) and CSV files
- 💬 Natural language query interface
- 📈 Data visualization
- 🔄 Automatic retry mechanism
- 🌐 Multiple API support (OpenAI, etc.)

## System Requirements

- Python 3.7+
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, etc.)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd datasheet-ai-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the application:
```bash
python app.py
```

The application will be running at http://localhost:1832

## Usage Guide

### 1. API Configuration

First-time users need to configure API settings:
- API Type: Choose your API service (e.g., OpenAI)
- API Key: Enter your API key
- API Base URL: (Optional) For custom API endpoints
- Max Retries: Set the number of retry attempts for failed analyses

### 2. File Upload

- Supported formats: Excel (.xlsx, .xls) and CSV (.csv)
- Click "Upload File" button or drag and drop files
- Preview uploaded files (default 10 rows, expandable for more)

### 3. Data Analysis

1. After upload, the system automatically analyzes file information:
   - Row and column counts
   - Data types
   - Basic statistical information

2. Enter natural language queries, such as:
   - "Count items by category"
   - "Calculate total sales"
   - "Generate data visualization"

3. Select appropriate model (if multiple models are available)

4. Click "Analyze" to start processing

### 4. View Results

- Results are displayed in a structured format
- Supports text explanations and data visualizations
- Retry functionality available for failed analyses

## Configuration

Key settings in config.py include:
- UPLOAD_FOLDER: File upload directory
- API settings (API_KEY, API_BASE, etc.)
- MAX_RETRIES: Maximum retry attempts

## Important Notes

1. Uploaded files are temporarily stored in the uploads directory
2. Ensure correct API configuration to avoid analysis failures
3. Larger files may require longer processing times
