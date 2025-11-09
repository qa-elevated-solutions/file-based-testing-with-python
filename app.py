"""
Web-based Test Runner Application
A Flask web app to upload and run test files
"""

from flask import Flask, render_template_string, request, jsonify
import os
import tempfile
from datetime import datetime
from test_framework import TestParser, TestRunner, TestResult

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Runner - Python Testing Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 40px;
        }
        .upload-section {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            border: 2px dashed #dee2e6;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }
        input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            background: white;
            cursor: pointer;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 32px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .results {
            margin-top: 30px;
        }
        .summary {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            flex: 1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card.total {
            background: #e7f3ff;
            border: 2px solid #2196F3;
        }
        .stat-card.passed {
            background: #e8f5e9;
            border: 2px solid #4caf50;
        }
        .stat-card.failed {
            background: #ffebee;
            border: 2px solid #f44336;
        }
        .stat-card h3 {
            font-size: 2em;
            margin-bottom: 5px;
        }
        .test-result {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .test-result:hover {
            transform: translateX(5px);
        }
        .test-result.passed {
            border-left: 5px solid #4caf50;
        }
        .test-result.failed {
            border-left: 5px solid #f44336;
        }
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .test-name {
            font-size: 1.2em;
            font-weight: 600;
        }
        .test-status {
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        .test-status.passed {
            background: #4caf50;
            color: white;
        }
        .test-status.failed {
            background: #f44336;
            color: white;
        }
        .test-details {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
        }
        .detail-row {
            margin-bottom: 10px;
            font-size: 0.95em;
        }
        .detail-label {
            font-weight: 600;
            color: #495057;
        }
        .code-block {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            margin-top: 5px;
            overflow-x: auto;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Runner Platform</h1>
            <p>Upload your .test files and run automated tests</p>
        </div>
        
        <div class="content">
            <div class="upload-section">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="testfile">Select Test File (.test)</label>
                        <input type="file" id="testfile" name="testfile" accept=".test" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="command">Command Template (use {input} as placeholder)</label>
                        <input type="text" id="command" name="command" 
                               value="python run_test.py {input}"
                               placeholder="echo {input}">
                    </div>
                    
                    <button type="submit" id="runBtn">Run Tests</button>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Running tests...</p>
            </div>
            
            <div class="results" id="results" style="display:none;">
                <!-- Results will be inserted here -->
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const runBtn = document.getElementById('runBtn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            runBtn.disabled = true;
            loading.style.display = 'block';
            results.style.display = 'none';
            
            try {
                const response = await fetch('/run-tests', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                alert('Error running tests: ' + error.message);
            } finally {
                runBtn.disabled = false;
                loading.style.display = 'none';
            }
        });
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            const { summary, tests } = data;
            
            let html = `
                <div class="summary">
                    <div class="stat-card total">
                        <h3>${summary.total}</h3>
                        <p>Total Tests</p>
                    </div>
                    <div class="stat-card passed">
                        <h3>${summary.passed}</h3>
                        <p>Passed</p>
                    </div>
                    <div class="stat-card failed">
                        <h3>${summary.failed}</h3>
                        <p>Failed</p>
                    </div>
                </div>
            `;
            
            tests.forEach(test => {
                const status = test.passed ? 'passed' : 'failed';
                const statusText = test.passed ? '✓ PASSED' : '✗ FAILED';
                
                html += `
                    <div class="test-result ${status}">
                        <div class="test-header">
                            <div class="test-name">${test.name}</div>
                            <div class="test-status ${status}">${statusText}</div>
                        </div>
                        ${test.description ? `<div class="detail-row">${test.description}</div>` : ''}
                        <div class="test-details">
                            <div class="detail-row">
                                <span class="detail-label">Execution Time:</span> ${test.time}s
                            </div>
                            ${!test.passed ? `
                                <div class="detail-row">
                                    <span class="detail-label">Expected:</span>
                                    <div class="code-block">${escapeHtml(test.expected)}</div>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Actual:</span>
                                    <div class="code-block">${escapeHtml(test.actual)}</div>
                                </div>
                                ${test.error ? `
                                    <div class="detail-row">
                                        <span class="detail-label">Error:</span>
                                        <div class="code-block">${escapeHtml(test.error)}</div>
                                    </div>
                                ` : ''}
                            ` : ''}
                        </div>
                    </div>
                `;
            });
            
            resultsDiv.innerHTML = html;
            resultsDiv.style.display = 'block';
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/run-tests', methods=['POST'])
def run_tests():
    """Handle test file upload and execution"""
    try:
        # Get uploaded file
        if 'testfile' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['testfile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get command template
        command = request.form.get('command', 'echo {input}')
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(mode='w', suffix='.test', delete=False) as tmp:
            content = file.read().decode('utf-8')
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Parse and run tests
            parser = TestParser()
            test_cases = parser.parse_file(tmp_path)
            
            runner = TestRunner(command)
            results = []
            
            for test_case in test_cases:
                result = runner.run_test(test_case)
                results.append({
                    'name': result.test_case.name,
                    'description': result.test_case.description,
                    'passed': result.passed,
                    'expected': result.test_case.expected_output,
                    'actual': result.actual_output,
                    'error': result.error_message,
                    'time': f"{result.execution_time:.3f}"
                })
            
            # Calculate summary
            passed = sum(1 for r in results if r['passed'])
            failed = len(results) - passed
            
            return jsonify({
                'summary': {
                    'total': len(results),
                    'passed': passed,
                    'failed': failed
                },
                'tests': results
            })
        
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*70)
    print("Test Runner Web Application")
    print("="*70)
    print("Starting server at http://localhost:5000")
    print("Open your browser and navigate to the URL above")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5000)