#!/usr/bin/env python3
"""
مسارات API لإدارة وحدات معالجة الرسومات (GPU)
"""

import logging
from flask import Blueprint, jsonify, request
from utils.auth import is_authenticated, is_authenticated_with_token
from utils.settings import get_setting, update_setting

logger = logging.getLogger(__name__)

gpu_bp = Blueprint('gpu', __name__)

@gpu_bp.route('/api/gpu/status')
def api_gpu_status():
    """Get GPU status and information"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from gpu_manager import gpu_manager
        gpus = gpu_manager.get_available_gpus()
        allocation = gpu_manager.get_optimal_allocation()
        
        return jsonify({
            'nvidia_available': gpu_manager.is_nvidia_available(),
            'gpus': gpus,
            'optimal_allocation': allocation,
            'total_gpus': len(gpus)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gpu_bp.route('/api/gpu/allocate', methods=['POST'])
def api_gpu_allocate():
    """Allocate GPUs to services"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        whisper_gpu = data.get('whisper_gpu')
        ollama_gpu = data.get('ollama_gpu')
        
        # Update settings
        if whisper_gpu is not None:
            update_setting('whisper_gpu_id', str(whisper_gpu))
        
        if ollama_gpu is not None:
            update_setting('ollama_gpu_id', str(ollama_gpu))
        
        return jsonify({
            'success': True,
            'allocation': {
                'whisper_gpu': whisper_gpu,
                'ollama_gpu': ollama_gpu
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gpu_bp.route('/api/gpu/auto-allocate', methods=['POST'])
def api_gpu_auto_allocate():
    """Automatically allocate GPUs based on optimal configuration"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from gpu_manager import gpu_manager
        allocation = gpu_manager.get_optimal_allocation()
        
        # Update settings with optimal allocation
        if allocation['whisper'] is not None:
            update_setting('whisper_gpu_id', str(allocation['whisper']))
        else:
            update_setting('whisper_gpu_id', 'cpu')
            
        if allocation['ollama'] is not None:
            update_setting('ollama_gpu_id', str(allocation['ollama']))
        else:
            update_setting('ollama_gpu_id', 'cpu')
        
        # Update auto allocation setting
        update_setting('auto_gpu_allocation', 'true')
        
        return jsonify({
            'success': True,
            'allocation': allocation,
            'message': 'GPUs allocated automatically based on optimal configuration'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gpu_bp.route('/api/gpu-refresh', methods=['POST'])
def api_gpu_refresh():
    """Refresh GPU information"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from gpu_manager import GPUManager
        gpu_manager = GPUManager()
        gpu_status = gpu_manager.get_gpu_status()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث معلومات كروت الشاشة بنجاح',
            'gpu_status': gpu_status
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': f'تم إكمال تحديث كروت الشاشة. حالة النظام: لا توجد كروت شاشة مكتشفة'
        })

@gpu_bp.route('/api/gpu-optimize', methods=['POST'])
def api_gpu_optimize():
    """Optimize GPU allocation"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from gpu_manager import GPUManager
        gpu_manager = GPUManager()
        
        # تحسين توزيع GPU
        gpu_status = gpu_manager.get_gpu_status()
        if gpu_status.get('total_gpus', 0) > 0:
            # تحديث إعدادات GPU
            update_setting('whisper_model_gpu', '0')
            update_setting('ollama_model_gpu', '0' if gpu_status.get('total_gpus', 0) == 1 else '1')
            
            return jsonify({
                'success': True,
                'message': 'GPU allocation optimized successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No GPUs detected. System configured for CPU-only processing.'
            })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': f'GPU optimization completed with status: {str(e)}'
        })

@gpu_bp.route('/api/gpu-diagnostics', methods=['POST'])
def api_gpu_diagnostics():
    """Run GPU diagnostics"""
    if not is_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from gpu_manager import GPUManager
        gpu_manager = GPUManager()
        
        gpu_status = gpu_manager.get_gpu_status()
        diagnostics = {
            'gpu_status': gpu_status,
            'system_status': 'تم إكمال تشخيص كروت الشاشة',
            'recommendations': []
        }
        
        if gpu_status.get('total_gpus', 0) == 0:
            diagnostics['recommendations'].append(
                'No GPUs detected. Install NVIDIA drivers if you have NVIDIA hardware.'
            )
        
        return jsonify({
            'success': True,
            'message': 'GPU diagnostics completed successfully',
            'diagnostics': diagnostics
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': f'GPU diagnostics completed. Status: {str(e)}'
        })