#!/usr/bin/env python3
"""
مسارات API للملفات الثابتة
"""

import os
import re
from flask import Blueprint, send_file

static_bp = Blueprint('static', __name__)

@static_bp.route('/static/OLLAMA_MODELS_README.md')
def serve_ollama_models_readme():
    """Serve the Ollama models README markdown file as HTML"""
    try:
        readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'OLLAMA_MODELS_README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple markdown to HTML conversion
            # Convert headers
            content = content.replace('# ', '<h1>').replace(' #', '</h1>')
            content = content.replace('## ', '<h2>').replace(' ##', '</h2>')
            content = content.replace('### ', '<h3>').replace(' ###', '</h3>')
            
            # Convert line breaks
            content = content.replace('\n', '<br>')
            
            # Convert links
            content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', content)
            
            # Convert code blocks
            content = content.replace('```', '<pre>')
            content = content.replace('```', '</pre>')
            
            # Wrap in HTML
            html = f'''
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>دليل تثبيت نماذج Ollama</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        color: #333;
                    }}
                    h1, h2, h3 {{
                        color: #2c3e50;
                    }}
                    pre {{
                        background-color: #f5f5f5;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    a {{
                        color: #3498db;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                {content}
            </body>
            </html>
            '''
            
            return html
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

@static_bp.route('/static/ollama_models_guide.html')
def serve_ollama_models_guide():
    """Serve the Ollama models guide HTML file"""
    try:
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'ollama_models_guide.html')
        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500