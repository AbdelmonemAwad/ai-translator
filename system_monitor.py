#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام مراقبة النظام المتطور - AI Translator
Advanced System Monitoring System - AI Translator
"""

import psutil
import platform
import json
import time
import os
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedSystemMonitor:
    """
    نظام مراقبة النظام المتطور
    Advanced System Monitoring System with real-time data collection
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.cpu_history = []
        self.memory_history = []
        self.disk_io_history = []
        self.network_io_history = []
        self.gpu_history = []
        self.history_limit = 60  # آخر 60 قراءة
        
        # معلومات النظام الأساسية
        self.system_info = self._get_system_info()
        
        # بدء مؤشر المراقبة المستمرة
        self.monitoring = False
        self.monitor_thread = None
        
    def _get_system_info(self) -> Dict[str, Any]:
        """الحصول على معلومات النظام الأساسية"""
        try:
            # معلومات المعالج
            cpu_info = self._get_cpu_info()
            
            # معلومات الذاكرة
            memory_info = self._get_memory_info()
            
            # معلومات التخزين
            storage_info = self._get_storage_info()
            
            # معلومات الشبكة
            network_info = self._get_network_info()
            
            # معلومات نظام التشغيل
            os_info = {
                'name': platform.system(),
                'version': platform.version(),
                'release': platform.release(),
                'architecture': platform.architecture()[0],
                'hostname': platform.node(),
                'uptime': self._get_uptime()
            }
            
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'storage': storage_info,
                'network': network_info,
                'os': os_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات النظام: {e}")
            return {}
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """الحصول على معلومات المعالج المفصلة"""
        try:
            # اسم المعالج
            cpu_name = "Unknown CPU"
            if platform.system() == "Linux":
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'model name' in line:
                                cpu_name = line.split(':')[1].strip()
                                break
                except:
                    pass
            
            # تفاصيل المعالج
            cpu_freq = psutil.cpu_freq()
            cpu_times = psutil.cpu_times()
            cpu_stats = psutil.cpu_stats()
            
            return {
                'name': cpu_name,
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'current_freq': cpu_freq.current if cpu_freq else 0,
                'min_freq': cpu_freq.min if cpu_freq else 0,
                'max_freq': cpu_freq.max if cpu_freq else 0,
                'usage_percent': psutil.cpu_percent(interval=1),
                'usage_per_core': psutil.cpu_percent(interval=1, percpu=True),
                'times': {
                    'user': cpu_times.user,
                    'system': cpu_times.system,
                    'idle': cpu_times.idle,
                    'iowait': getattr(cpu_times, 'iowait', 0)
                },
                'stats': {
                    'ctx_switches': cpu_stats.ctx_switches,
                    'interrupts': cpu_stats.interrupts,
                    'soft_interrupts': cpu_stats.soft_interrupts,
                    'syscalls': cpu_stats.syscalls
                },
                'temperature': self._get_cpu_temperature()
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات المعالج: {e}")
            return {}
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الذاكرة المفصلة"""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            # معلومات إضافية عن الذاكرة
            memory_type = "Unknown"
            memory_speed = 0
            
            if platform.system() == "Linux":
                try:
                    # محاولة الحصول على نوع الذاكرة من dmidecode
                    result = subprocess.run(['dmidecode', '-t', 'memory'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for i, line in enumerate(lines):
                            if 'Type:' in line and 'DDR' in line:
                                memory_type = line.split(':')[1].strip()
                            if 'Speed:' in line and 'MHz' in line:
                                try:
                                    memory_speed = int(line.split(':')[1].strip().split()[0])
                                except:
                                    pass
                except:
                    pass
            
            return {
                'total': virtual_mem.total,
                'available': virtual_mem.available,
                'used': virtual_mem.used,
                'free': virtual_mem.free,
                'percent': virtual_mem.percent,
                'buffers': getattr(virtual_mem, 'buffers', 0),
                'cached': getattr(virtual_mem, 'cached', 0),
                'shared': getattr(virtual_mem, 'shared', 0),
                'type': memory_type,
                'speed_mhz': memory_speed,
                'swap': {
                    'total': swap_mem.total,
                    'used': swap_mem.used,
                    'free': swap_mem.free,
                    'percent': swap_mem.percent,
                    'sin': swap_mem.sin,
                    'sout': swap_mem.sout
                }
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات الذاكرة: {e}")
            return {}
    
    def _get_storage_info(self) -> List[Dict[str, Any]]:
        """الحصول على معلومات التخزين المفصلة"""
        try:
            storage_devices = []
            
            # الحصول على جميع نقاط التركيب
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # تحديد نوع القرص
                    device_type = "Unknown"
                    is_ssd = False
                    
                    if platform.system() == "Linux":
                        device_name = partition.device.split('/')[-1]
                        # إزالة الأرقام من اسم الجهاز
                        base_device = ''.join([c for c in device_name if not c.isdigit()])
                        
                        try:
                            # فحص إذا كان SSD
                            rotational_path = f"/sys/block/{base_device}/queue/rotational"
                            if os.path.exists(rotational_path):
                                with open(rotational_path, 'r') as f:
                                    is_ssd = f.read().strip() == '0'
                                    device_type = "SSD" if is_ssd else "HDD"
                        except:
                            pass
                        
                        # إضافة فحص NVMe
                        if 'nvme' in device_name.lower():
                            device_type = "NVMe SSD"
                            is_ssd = True
                    
                    # الحصول على إحصائيات I/O
                    io_stats = {}
                    try:
                        disk_io = psutil.disk_io_counters(perdisk=True)
                        device_key = partition.device.split('/')[-1]
                        if device_key in disk_io:
                            io_stats = {
                                'read_count': disk_io[device_key].read_count,
                                'write_count': disk_io[device_key].write_count,
                                'read_bytes': disk_io[device_key].read_bytes,
                                'write_bytes': disk_io[device_key].write_bytes,
                                'read_time': disk_io[device_key].read_time,
                                'write_time': disk_io[device_key].write_time
                            }
                    except:
                        pass
                    
                    storage_devices.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0,
                        'type': device_type,
                        'is_ssd': is_ssd,
                        'io_stats': io_stats
                    })
                    
                except PermissionError:
                    continue
                except Exception as e:
                    logger.warning(f"خطأ في قراءة معلومات القرص {partition.device}: {e}")
                    continue
            
            return storage_devices
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات التخزين: {e}")
            return []
    
    def _get_network_info(self) -> List[Dict[str, Any]]:
        """الحصول على معلومات الشبكة المفصلة"""
        try:
            network_interfaces = []
            
            # الحصول على إحصائيات الشبكة
            net_io = psutil.net_io_counters(pernic=True)
            net_addrs = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            
            for interface_name, stats in net_stats.items():
                # تجاهل الواجهات الافتراضية
                if interface_name.startswith(('lo', 'docker', 'br-', 'veth')):
                    continue
                
                interface_info = {
                    'name': interface_name,
                    'is_up': stats.isup,
                    'duplex': str(stats.duplex),
                    'speed': stats.speed,
                    'mtu': stats.mtu,
                    'addresses': [],
                    'io_stats': {}
                }
                
                # الحصول على العناوين
                if interface_name in net_addrs:
                    for addr in net_addrs[interface_name]:
                        addr_info = {
                            'family': str(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask if addr.netmask else "",
                            'broadcast': addr.broadcast if addr.broadcast else ""
                        }
                        interface_info['addresses'].append(addr_info)
                
                # الحصول على إحصائيات I/O
                if interface_name in net_io:
                    io = net_io[interface_name]
                    interface_info['io_stats'] = {
                        'bytes_sent': io.bytes_sent,
                        'bytes_recv': io.bytes_recv,
                        'packets_sent': io.packets_sent,
                        'packets_recv': io.packets_recv,
                        'errin': io.errin,
                        'errout': io.errout,
                        'dropin': io.dropin,
                        'dropout': io.dropout
                    }
                
                network_interfaces.append(interface_info)
            
            return network_interfaces
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات الشبكة: {e}")
            return []
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """الحصول على حرارة المعالج"""
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                
                # البحث عن حرارة المعالج
                for name, entries in temps.items():
                    if 'coretemp' in name.lower() or 'cpu' in name.lower():
                        for entry in entries:
                            if entry.current:
                                return entry.current
                
                # إذا لم نجد حرارة المعالج، نأخذ أول حرارة متاحة
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            return entry.current
            
            return None
            
        except Exception as e:
            logger.warning(f"لا يمكن قراءة حرارة المعالج: {e}")
            return None
    
    def _get_uptime(self) -> str:
        """الحصول على مدة تشغيل النظام"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception as e:
            logger.error(f"خطأ في حساب مدة التشغيل: {e}")
            return "Unknown"
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النظام في الوقت الفعلي"""
        try:
            current_time = datetime.now()
            
            # إحصائيات المعالج
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # إحصائيات الذاكرة
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # إحصائيات القرص
            disk_io = psutil.disk_io_counters()
            
            # إحصائيات الشبكة
            net_io = psutil.net_io_counters()
            
            # إحصائيات العمليات
            processes = len(psutil.pids())
            
            # معلومات التحميل (Linux only)
            load_avg = [0, 0, 0]
            if hasattr(os, 'getloadavg'):
                try:
                    load_avg = list(os.getloadavg())
                except:
                    pass
            
            stats = {
                'timestamp': current_time.isoformat(),
                'uptime': self._get_uptime(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'usage_per_core': cpu_per_core,
                    'temperature': self._get_cpu_temperature(),
                    'load_average': load_avg
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent,
                    'swap_percent': swap.percent
                },
                'disk': {
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent if net_io else 0,
                    'bytes_recv': net_io.bytes_recv if net_io else 0,
                    'packets_sent': net_io.packets_sent if net_io else 0,
                    'packets_recv': net_io.packets_recv if net_io else 0
                },
                'processes': {
                    'total': processes,
                    'running': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running']),
                    'sleeping': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'sleeping'])
                }
            }
            
            # إضافة الإحصائيات إلى التاريخ
            self._add_to_history(stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الإحصائيات: {e}")
            return {}
    
    def _add_to_history(self, stats: Dict[str, Any]):
        """إضافة الإحصائيات إلى التاريخ"""
        try:
            # إضافة إحصائيات المعالج
            if 'cpu' in stats:
                self.cpu_history.append({
                    'timestamp': stats['timestamp'],
                    'usage': stats['cpu']['usage_percent'],
                    'temperature': stats['cpu']['temperature']
                })
            
            # إضافة إحصائيات الذاكرة
            if 'memory' in stats:
                self.memory_history.append({
                    'timestamp': stats['timestamp'],
                    'percent': stats['memory']['percent'],
                    'used': stats['memory']['used'],
                    'available': stats['memory']['available']
                })
            
            # إضافة إحصائيات القرص
            if 'disk' in stats:
                self.disk_io_history.append({
                    'timestamp': stats['timestamp'],
                    'read_bytes': stats['disk']['read_bytes'],
                    'write_bytes': stats['disk']['write_bytes']
                })
            
            # إضافة إحصائيات الشبكة
            if 'network' in stats:
                self.network_io_history.append({
                    'timestamp': stats['timestamp'],
                    'bytes_sent': stats['network']['bytes_sent'],
                    'bytes_recv': stats['network']['bytes_recv']
                })
            
            # تنظيف التاريخ القديم
            for history in [self.cpu_history, self.memory_history, 
                          self.disk_io_history, self.network_io_history]:
                if len(history) > self.history_limit:
                    history.pop(0)
                    
        except Exception as e:
            logger.error(f"خطأ في إضافة الإحصائيات إلى التاريخ: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """تقييم صحة النظام العامة"""
        try:
            stats = self.get_real_time_stats()
            health = {
                'overall_status': 'healthy',
                'warnings': [],
                'critical_issues': [],
                'score': 100
            }
            
            # فحص استخدام المعالج
            cpu_usage = stats.get('cpu', {}).get('usage_percent', 0)
            if cpu_usage > 90:
                health['critical_issues'].append('استخدام المعالج مرتفع جداً')
                health['score'] -= 30
            elif cpu_usage > 75:
                health['warnings'].append('استخدام المعالج مرتفع')
                health['score'] -= 15
            
            # فحص استخدام الذاكرة
            memory_usage = stats.get('memory', {}).get('percent', 0)
            if memory_usage > 90:
                health['critical_issues'].append('استخدام الذاكرة مرتفع جداً')
                health['score'] -= 25
            elif memory_usage > 80:
                health['warnings'].append('استخدام الذاكرة مرتفع')
                health['score'] -= 10
            
            # فحص حرارة المعالج
            cpu_temp = stats.get('cpu', {}).get('temperature')
            if cpu_temp:
                if cpu_temp > 85:
                    health['critical_issues'].append('حرارة المعالج مرتفعة جداً')
                    health['score'] -= 20
                elif cpu_temp > 75:
                    health['warnings'].append('حرارة المعالج مرتفعة')
                    health['score'] -= 10
            
            # فحص مساحة القرص
            for device in self._get_storage_info():
                if device['percent'] > 95:
                    health['critical_issues'].append(f'مساحة القرص {device["mountpoint"]} ممتلئة')
                    health['score'] -= 20
                elif device['percent'] > 85:
                    health['warnings'].append(f'مساحة القرص {device["mountpoint"]} قليلة')
                    health['score'] -= 10
            
            # تحديد الحالة العامة
            if health['score'] < 50:
                health['overall_status'] = 'critical'
            elif health['score'] < 75:
                health['overall_status'] = 'warning'
            elif health['score'] < 90:
                health['overall_status'] = 'good'
            
            return health
            
        except Exception as e:
            logger.error(f"خطأ في تقييم صحة النظام: {e}")
            return {'overall_status': 'unknown', 'score': 0}
    
    def get_process_list(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على قائمة العمليات المرتبة حسب استخدام المعالج"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 
                                           'memory_percent', 'status', 'create_time']):
                try:
                    proc_info = proc.info
                    proc_info['create_time'] = datetime.fromtimestamp(
                        proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # ترتيب حسب استخدام المعالج
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على قائمة العمليات: {e}")
            return []
    
    def start_monitoring(self, interval: int = 5):
        """بدء المراقبة المستمرة"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self.get_real_time_stats()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"خطأ في حلقة المراقبة: {e}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("تم بدء مراقبة النظام")
    
    def stop_monitoring(self):
        """إيقاف المراقبة المستمرة"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("تم إيقاف مراقبة النظام")
    
    def export_stats(self, filepath: Optional[str] = None) -> str:
        """تصدير الإحصائيات إلى ملف JSON"""
        try:
            stats_data = {
                'system_info': self.system_info,
                'current_stats': self.get_real_time_stats(),
                'system_health': self.get_system_health(),
                'cpu_history': self.cpu_history[-20:],  # آخر 20 قراءة
                'memory_history': self.memory_history[-20:],
                'processes': self.get_process_list(20),
                'export_time': datetime.now().isoformat()
            }
            
            if not filepath:
                filepath = f"system_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"تم تصدير الإحصائيات إلى: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"خطأ في تصدير الإحصائيات: {e}")
            return ""

# إنشاء مثيل مراقب النظام
system_monitor = AdvancedSystemMonitor()

def get_system_monitor():
    """الحصول على مثيل مراقب النظام"""
    return system_monitor

if __name__ == "__main__":
    # اختبار النظام
    monitor = AdvancedSystemMonitor()
    
    print("=== معلومات النظام ===")
    print(json.dumps(monitor.system_info, ensure_ascii=False, indent=2))
    
    print("\n=== الإحصائيات الحالية ===")
    print(json.dumps(monitor.get_real_time_stats(), ensure_ascii=False, indent=2))
    
    print("\n=== صحة النظام ===")
    print(json.dumps(monitor.get_system_health(), ensure_ascii=False, indent=2))
    
    print("\n=== العمليات ===")
    for proc in monitor.get_process_list(5):
        print(f"{proc['name']} - CPU: {proc['cpu_percent']}% - الذاكرة: {proc['memory_percent']:.1f}%")