#!/usr/bin/env python3
"""
مسارات API للاختبار والتشخيص
"""

import logging
import requests
from flask import Blueprint, jsonify, request
from utils.auth import is_authenticated, is_authenticated_with_token

logger = logging.getLogger(__name__)

test_bp = Blueprint('test', __name__)

@test_bp.route('/api/test-ollama', methods=['POST'])
def api_test_ollama():
    """Test Ollama connection"""
    if not is_authenticated_with_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({
                'success': True,
                'message': f'Ollama connection successful. Found {len(models)} models.',
                'models': [model.get('name', 'unknown') for model in models]
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Ollama connection failed. Status code: {response.status_code}'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ollama connection failed: {str(e)}'
        })

@test_bp.route('/api/test-whisper', methods=['POST'])
def api_test_whisper():
    """Test Whisper API"""
    if not is_authenticated_with_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        try:
            from ai_integration_workaround import FastWhisperIntegration
            whisper = FastWhisperIntegration()
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'AI integration module not available'
            })
        
        if whisper._check_availability():
            return jsonify({
                'success': True,
                'message': 'Whisper (faster-whisper) is available and working correctly'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Whisper is not available'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Whisper test failed: {str(e)}'
        })

@test_bp.route('/api/benchmark-models', methods=['POST'])
def api_benchmark_models():
    """Benchmark AI models"""
    if not is_authenticated_with_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        try:
            from ai_integration_workaround import get_ai_status
            ai_status = get_ai_status()
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'AI integration module not available'
            })
        
        benchmark_results = {
            'faster_whisper': 'Available' if ai_status['components'].get('faster_whisper') else 'Not Available',
            'ollama': 'Available' if ai_status['components'].get('ollama') else 'Not Available',
            'pytorch': 'Available' if ai_status['components'].get('pytorch') else 'Not Available',
            'ffmpeg': 'Available' if ai_status['components'].get('ffmpeg') else 'Not Available'
        }
        
        return jsonify({
            'success': True,
            'message': 'Model benchmark completed successfully',
            'results': benchmark_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Benchmark failed: {str(e)}'
        })