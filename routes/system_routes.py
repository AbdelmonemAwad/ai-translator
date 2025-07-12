#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات مراقبة النظام - AI Translator
System Monitoring Routes - AI Translator
"""

import os
import psutil
import logging
import subprocess
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from utils.auth import login_required
from system_monitor import get_system_monitor

# إنشاء Blueprint لمسارات النظام
system_bp = Blueprint('system', __name__)


@system_bp.route('/api/system-health-check')
def api_system_health_check():
    """API للتحقق من صحة النظام الأساسية"""
    try:
        health = {
            'status': 'ok',
            'issues': [],
            'system_resources': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        }
        
        # Check for resource issues
        if health['system_resources']['memory_percent'] > 90:
            health['issues'].append('High memory usage')
            health['status'] = 'warning'
        
        if health['system_resources']['disk_percent'] > 95:
            health['issues'].append('Low disk space')
            health['status'] = 'warning'
        
        return jsonify(health)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@system_bp.route('/api/system-monitor')
def api_system_monitor_stats():
    """API للحصول على إحصائيات مراقبة النظام الأساسية"""
    try:
        # استخدام psutil مباشرة للحصول على الإحصائيات الأساسية
        cpu_percent = round(psutil.cpu_percent(interval=1))
        memory = psutil.virtual_memory()
        ram_percent = round(memory.percent)
        ram_used_gb = round(memory.used / (1024**3), 1)
        ram_total_gb = round(memory.total / (1024**3), 1)
        
        # Get basic disk info
        disk_usage = psutil.disk_usage('/')
        disk_percent = round(disk_usage.used / disk_usage.total * 100)
        disk_used_gb = round(disk_usage.used / (1024**3), 1)
        disk_total_gb = round(disk_usage.total / (1024**3), 1)
        
        # Get network info
        net_io = psutil.net_io_counters()
        network_stats = {
            'bytes_sent': net_io.bytes_sent if net_io else 0,
            'bytes_recv': net_io.bytes_recv if net_io else 0,
            'packets_sent': net_io.packets_sent if net_io else 0,
            'packets_recv': net_io.packets_recv if net_io else 0
        }
        
        # Auto-detect GPU information
        gpu_info = {'available': False, 'gpus': [], 'total_memory': 0}
        try:
            # Try nvidia-smi first
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                gpu_lines = result.stdout.strip().split('\n')
                gpu_info['available'] = True
                for i, line in enumerate(gpu_lines):
                    parts = line.split(', ')
                    if len(parts) >= 5:
                        name, total_mem, used_mem, util, temp = parts[:5]
                        gpu_info['gpus'].append({
                            'id': i,
                            'name': name.strip(),
                            'memory_total': int(total_mem),
                            'memory_used': int(used_mem),
                            'memory_free': int(total_mem) - int(used_mem),
                            'utilization': int(util),
                            'temperature': int(temp) if temp != '[Not Supported]' else 0
                        })
                        gpu_info['total_memory'] += int(total_mem)
        except:
            # Fallback to pynvml if available
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                if device_count > 0:
                    gpu_info['available'] = True
                    for i in range(device_count):
                        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                        name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        try:
                            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                            gpu_util = util.gpu
                        except:
                            gpu_util = 0
                        try:
                            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                        except:
                            temp = 0
                        
                        gpu_info['gpus'].append({
                            'id': i,
                            'name': name,
                            'memory_total': memory_info.total // (1024**2),  # MB
                            'memory_used': memory_info.used // (1024**2),
                            'memory_free': memory_info.free // (1024**2),
                            'utilization': gpu_util,
                            'temperature': temp
                        })
                        gpu_info['total_memory'] += memory_info.total // (1024**2)
            except:
                pass
        
        # Auto-detect storage devices
        disk_info = {}
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        'device': partition.device,
                        'filesystem': partition.fstype,
                        'total': round(partition_usage.total / (1024**3), 1),
                        'used': round(partition_usage.used / (1024**3), 1),
                        'free': round(partition_usage.free / (1024**3), 1),
                        'percent': round(partition_usage.used / partition_usage.total * 100),
                        'error': False
                    }
                except:
                    disk_info[partition.mountpoint] = {
                        'device': partition.device,
                        'error': True
                    }
        except:
            disk_info = {
                '/': {
                    'total': disk_total_gb,
                    'used': disk_used_gb,
                    'percent': disk_percent,
                    'error': False
                }
            }
        
        return jsonify({
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'ram_used_gb': ram_used_gb,
            'ram_total_gb': ram_total_gb,
            'disk': disk_info,
            'network': network_stats,
            'gpu': gpu_info
        })
        
    except Exception as e:
        logging.error(f"خطأ في مراقبة النظام: {e}")
        return jsonify({'error': f'خطأ في مراقبة النظام: {str(e)}'}), 500


@system_bp.route('/api/advanced-system-monitor')
def api_advanced_system_monitor():
    """API متطور لمراقبة النظام باستخدام نظام البايثون المتطور"""
    try:
        monitor = get_system_monitor()
        stats = monitor.get_real_time_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"خطأ في API مراقبة النظام المتطور: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/api/system-info-detailed')
def api_system_info_detailed():
    """API للحصول على معلومات النظام الأساسية المفصلة"""
    try:
        monitor = get_system_monitor()
        
        return jsonify({
            'success': True,
            'data': monitor.system_info
        })
        
    except Exception as e:
        logging.error(f"خطأ في API معلومات النظام: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/api/system-health')
def api_system_health():
    """API لتقييم صحة النظام"""
    try:
        monitor = get_system_monitor()
        health = monitor.get_system_health()
        
        return jsonify({
            'success': True,
            'data': health
        })
        
    except Exception as e:
        logging.error(f"خطأ في API صحة النظام: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/api/system-processes')
def api_system_processes():
    """API للحصول على قائمة العمليات"""
    try:
        monitor = get_system_monitor()
        limit = request.args.get('limit', 10, type=int)
        processes = monitor.get_process_list(limit)
        
        return jsonify({
            'success': True,
            'data': processes
        })
        
    except Exception as e:
        logging.error(f"خطأ في API العمليات: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/api/system-export')
def api_system_export():
    """API لتصدير إحصائيات النظام"""
    try:
        monitor = get_system_monitor()
        filepath = monitor.export_stats()
        
        if filepath and os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({
                'success': False,
                'error': 'فشل في تصدير الإحصائيات'
            }), 500
        
    except Exception as e:
        logging.error(f"خطأ في تصدير الإحصائيات: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500