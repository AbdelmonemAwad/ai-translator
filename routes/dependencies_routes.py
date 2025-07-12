#!/usr/bin/env python3
"""
مسارات API للتبعيات
"""

import logging
import subprocess
from flask import Blueprint, jsonify, request
from utils.dependencies import get_dependencies_status, get_ai_status
from utils.auth import is_authenticated

logger = logging.getLogger(__name__)

dependencies_bp = Blueprint('dependencies', __name__)

@dependencies_bp.route('/api/dependencies-status')
def api_dependencies_status():
    """Get status of all dependencies"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        status_result = get_dependencies_status()
        ai_status = status_result.pop('ai_system', get_ai_status())
        
        return jsonify({
            'success': True,
            'dependencies': status_result,
            'ai_system': ai_status,
            'summary': status_result.get('summary', {
                'total_packages': 0,
                'installed_count': 0,
                'system_ready': False
            })
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dependencies_bp.route('/api/install-dependency', methods=['POST'])
def api_install_dependency():
    """Install a specific dependency"""
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        package = data.get('package')
        package_type = data.get('type', 'python')
        
        # ... باقي الكود من الدالة الأصلية
        
        return jsonify({'success': True, 'message': f'Package {package} installed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ... باقي مسارات API التبعيات