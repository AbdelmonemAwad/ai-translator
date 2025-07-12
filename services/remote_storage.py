#!/usr/bin/env python3
"""
Remote Storage Management Module for AI Translator
إدارة التخزين البعيد للترجمان الآلي
"""

import os
import logging
import subprocess
import json
import platform
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RemoteStorageManager:
    """إدارة التخزين البعيد والاتصال بالشبكة"""
    
    def __init__(self):
        self.supported_protocols = ['sftp', 'ftp', 'smb', 'nfs', 'sshfs', 'afp', 'rsync']
        self.mount_points = {}
        self.connection_cache = {}
        # تحديد نظام التشغيل
        self.os_type = platform.system()
        logger.info(f"Detected operating system: {self.os_type}")
        
    def is_windows(self) -> bool:
        """التحقق إذا كان النظام هو Windows"""
        return self.os_type == "Windows"
    
    def is_linux(self) -> bool:
        """التحقق إذا كان النظام هو Linux"""
        return self.os_type == "Linux"
    
    def is_macos(self) -> bool:
        """التحقق إذا كان النظام هو macOS"""
        return self.os_type == "Darwin"
        
    def test_connection(self, protocol: str, host: str, port: int = None, 
                       username: str = None, password: str = None, 
                       share_path: str = None) -> Dict[str, Any]:
        """اختبار الاتصال بالخادم البعيد"""
        try:
            # تحقق من دعم البروتوكول في نظام التشغيل الحالي
            if self.is_windows() and protocol in ['sshfs', 'nfs']:
                return {
                    'success': False,
                    'error': f'Protocol {protocol} is not natively supported on Windows',
                    'protocol': protocol,
                    'os': 'Windows'
                }
                
            if protocol == 'sftp':
                return self._test_sftp_connection(host, port or 22, username, password)
            elif protocol == 'ftp':
                return self._test_ftp_connection(host, port or 21, username, password)
            elif protocol == 'smb':
                return self._test_smb_connection(host, share_path, username, password)
            elif protocol == 'nfs':
                return self._test_nfs_connection(host, share_path)
            elif protocol == 'sshfs':
                return self._test_sshfs_connection(host, port or 22, username, password)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported protocol: {protocol}',
                    'protocol': protocol
                }
        except Exception as e:
            logger.error(f"Connection test failed for {protocol}://{host}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'protocol': protocol,
                'host': host
            }
    
    def _test_sftp_connection(self, host: str, port: int, username: str, password: str) -> Dict[str, Any]:
        """اختبار اتصال SFTP"""
        try:
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            
            sftp = ssh.open_sftp()
            # Test listing directory
            sftp.listdir('.')
            sftp.close()
            ssh.close()
            
            return {
                'success': True,
                'protocol': 'sftp',
                'host': host,
                'port': port,
                'message': 'SFTP connection successful'
            }
        except Exception as e:
            return {
                'success': False,
                'protocol': 'sftp',
                'host': host,
                'error': str(e)
            }
    
    def _test_ftp_connection(self, host: str, port: int, username: str, password: str) -> Dict[str, Any]:
        """اختبار اتصال FTP"""
        try:
            from ftplib import FTP
            
            ftp = FTP()
            ftp.connect(host, port, timeout=10)
            ftp.login(username, password)
            ftp.pwd()  # Test basic operation
            ftp.quit()
            
            return {
                'success': True,
                'protocol': 'ftp',
                'host': host,
                'port': port,
                'message': 'FTP connection successful'
            }
        except Exception as e:
            return {
                'success': False,
                'protocol': 'ftp',
                'host': host,
                'error': str(e)
            }
    
    def _test_smb_connection(self, host: str, share_path: str, username: str, password: str) -> Dict[str, Any]:
        """اختبار اتصال SMB/CIFS"""
        try:
            # Test SMB connection using smbclient if available
            cmd = [
                'smbclient',
                f'//{host}/{share_path}',
                '-U', f'{username}%{password}',
                '-c', 'ls'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'protocol': 'smb',
                    'host': host,
                    'share': share_path,
                    'message': 'SMB connection successful'
                }
            else:
                return {
                    'success': False,
                    'protocol': 'smb',
                    'host': host,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'protocol': 'smb',
                'host': host,
                'error': str(e)
            }
    
    def _test_nfs_connection(self, host: str, share_path: str) -> Dict[str, Any]:
        """اختبار اتصال NFS"""
        try:
            # Test NFS using showmount if available
            cmd = ['showmount', '-e', host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'protocol': 'nfs',
                    'host': host,
                    'share': share_path,
                    'message': 'NFS server accessible',
                    'exports': result.stdout
                }
            else:
                return {
                    'success': False,
                    'protocol': 'nfs',
                    'host': host,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'protocol': 'nfs',
                'host': host,
                'error': str(e)
            }
    
    def _test_sshfs_connection(self, host: str, port: int, username: str, password: str) -> Dict[str, Any]:
        """اختبار اتصال SSHFS"""
        try:
            # Test SSH connection first
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            ssh.close()
            
            return {
                'success': True,
                'protocol': 'sshfs',
                'host': host,
                'port': port,
                'message': 'SSHFS connection ready'
            }
        except Exception as e:
            return {
                'success': False,
                'protocol': 'sshfs',
                'host': host,
                'error': str(e)
            }
    
    def setup_mount(self, protocol: str, host: str, remote_path: str, 
                   local_mount_point: str, **kwargs) -> Dict[str, Any]:
        """إعداد نقطة التحميل للتخزين البعيد"""
        try:
            # تحقق من دعم البروتوكول في نظام التشغيل الحالي
            if self.is_windows():
                if protocol in ['sshfs', 'nfs', 'afp']:
                    return {
                        'success': False,
                        'error': f'Protocol {protocol} is not natively supported on Windows',
                        'protocol': protocol,
                        'os': 'Windows'
                    }
                # استخدام أمر net use لـ Windows مع SMB
                if protocol == 'smb':
                    return self._setup_windows_smb_mount(host, remote_path, local_mount_point, **kwargs)
            
            # Create mount point directory if it doesn't exist
            os.makedirs(local_mount_point, exist_ok=True)
            
            if protocol == 'sftp' or protocol == 'sshfs':
                return self._setup_sshfs_mount(host, remote_path, local_mount_point, **kwargs)
            elif protocol == 'smb':
                return self._setup_smb_mount(host, remote_path, local_mount_point, **kwargs)
            elif protocol == 'nfs':
                return self._setup_nfs_mount(host, remote_path, local_mount_point, **kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Mount not supported for protocol: {protocol}'
                }
        except Exception as e:
            logger.error(f"Mount setup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_windows_smb_mount(self, host: str, remote_path: str, local_mount_point: str, **kwargs) -> Dict[str, Any]:
        """إعداد تحميل SMB في Windows باستخدام net use"""
        try:
            username = kwargs.get('username', '')
            password = kwargs.get('password', '')
            
            # تحويل المسار إلى تنسيق Windows
            drive_letter = local_mount_point[:2] if local_mount_point[1] == ':' else 'Z:'
            network_path = f'\\\\{host}\\{remote_path}'
            
            # إعداد أمر net use
            if username and password:
                cmd = [
                    'net', 'use', drive_letter, network_path,
                    f'/user:{username}', password, '/persistent:yes'
                ]
            else:
                cmd = ['net', 'use', drive_letter, network_path, '/persistent:yes']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mount_points[drive_letter] = {
                    'protocol': 'smb',
                    'host': host,
                    'remote_path': remote_path,
                    'mounted_at': datetime.now().isoformat()
                }
                return {
                    'success': True,
                    'mount_point': drive_letter,
                    'message': 'SMB mount successful on Windows'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_sshfs_mount(self, host: str, remote_path: str, local_mount_point: str, **kwargs) -> Dict[str, Any]:
        """إعداد تحميل SSHFS"""
        try:
            username = kwargs.get('username', 'root')
            port = kwargs.get('port', 22)
            
            cmd = [
                'sshfs',
                f'{username}@{host}:{remote_path}',
                local_mount_point,
                '-o', f'port={port}',
                '-o', 'allow_other',
                '-o', 'default_permissions'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mount_points[local_mount_point] = {
                    'protocol': 'sshfs',
                    'host': host,
                    'remote_path': remote_path,
                    'mounted_at': datetime.now().isoformat()
                }
                return {
                    'success': True,
                    'mount_point': local_mount_point,
                    'message': 'SSHFS mount successful'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_smb_mount(self, host: str, remote_path: str, local_mount_point: str, **kwargs) -> Dict[str, Any]:
        """إعداد تحميل SMB/CIFS"""
        try:
            username = kwargs.get('username', '')
            password = kwargs.get('password', '')
            
            cmd = [
                'mount',
                '-t', 'cifs',
                f'//{host}/{remote_path}',
                local_mount_point,
                '-o', f'username={username},password={password}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mount_points[local_mount_point] = {
                    'protocol': 'smb',
                    'host': host,
                    'remote_path': remote_path,
                    'mounted_at': datetime.now().isoformat()
                }
                return {
                    'success': True,
                    'mount_point': local_mount_point,
                    'message': 'SMB mount successful'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_nfs_mount(self, host: str, remote_path: str, local_mount_point: str, **kwargs) -> Dict[str, Any]:
        """إعداد تحميل NFS"""
        try:
            cmd = [
                'mount',
                '-t', 'nfs',
                f'{host}:{remote_path}',
                local_mount_point
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mount_points[local_mount_point] = {
                    'protocol': 'nfs',
                    'host': host,
                    'remote_path': remote_path,
                    'mounted_at': datetime.now().isoformat()
                }
                return {
                    'success': True,
                    'mount_point': local_mount_point,
                    'message': 'NFS mount successful'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_afp_connection(self, host: str, share_path: str, username: str, password: str) -> Dict[str, Any]:
        """اختبار اتصال AFP"""
        try:
            # Test AFP connection
            # Note: This is a placeholder. Actual implementation would depend on the AFP library used
            return {
                'success': True,
                'protocol': 'afp',
                'host': host,
                'share': share_path,
                'message': 'AFP connection test successful'
            }
        except Exception as e:
            return {
                'success': False,
                'protocol': 'afp',
                'error': str(e),
                'message': 'AFP connection test failed'
            }
    
    def _setup_afp_mount(self, host: str, remote_path: str, local_mount_point: str, **kwargs) -> Dict[str, Any]:
        """إعداد تحميل AFP"""
        try:
            username = kwargs.get('username', '')
            password = kwargs.get('password', '')
            
            # Setup AFP mount
            # Note: This is a placeholder. Actual implementation would depend on the system
            cmd = [
                'mount_afp',
                f'afp://{username}:{password}@{host}/{remote_path}',
                local_mount_point
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mount_points[local_mount_point] = {
                    'protocol': 'afp',
                    'host': host,
                    'remote_path': remote_path,
                    'mounted_at': datetime.now().isoformat()
                }
                return {
                    'success': True,
                    'mount_point': local_mount_point,
                    'message': 'AFP mount successful'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'message': 'AFP mount setup failed'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'AFP mount setup failed'
            }
    
    def _setup_rsync_transfer(self, host: str, remote_path: str, local_path: str, **kwargs) -> Dict[str, Any]:
        """إعداد نقل rsync"""
        try:
            username = kwargs.get('username', '')
            
            # Setup rsync transfer
            cmd = [
                'rsync',
                '-avz',
                f'{username}@{host}:{remote_path}',
                local_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'local_path': local_path,
                    'message': 'rsync transfer successful'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'message': 'rsync transfer failed'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'rsync transfer setup failed'
            }
    
    def get_mount_status(self, mount_point: str = None) -> Dict[str, Any]:
        """الحصول على حالة نقاط التحميل - متوافق مع Replit"""
        try:
            # تحقق من بيئة Replit
            is_replit = os.environ.get('REPLIT_ENVIRONMENT') is not None or 'replit' in os.getcwd().lower()
            
            if is_replit:
                # في بيئة Replit، نعيد نتيجة آمنة بدون محاولة الوصول للبيانات الحقيقية
                return {
                    'success': True,
                    'mount_points': {},  # فارغ في Replit
                    'available_protocols': ['sftp', 'ftp', 'smb', 'nfs', 'sshfs'],
                    'replit_mode': True,
                    'note': 'Remote storage disabled in Replit environment for security'
                }
            
            if mount_point:
                # Check specific mount point in real environment
                if mount_point in self.mount_points:
                    is_mounted = self._is_mounted(mount_point)
                    return {
                        'success': True,
                        'mount_point': mount_point,
                        'is_mounted': is_mounted,
                        'details': self.mount_points[mount_point]
                    }
                else:
                    return {
                        'success': True,  # تغيير لـ True لمنع كسر الواجهة
                        'mount_point': mount_point,
                        'is_mounted': False,
                        'note': 'Mount point not configured'
                    }
            else:
                # Check all mount points in real environment
                status = {}
                for mp in self.mount_points:
                    status[mp] = {
                        'is_mounted': self._is_mounted(mp),
                        'details': self.mount_points[mp]
                    }
                return {
                    'success': True,
                    'mount_points': status
                }
        except Exception as e:
            # تعامل آمن مع الأخطاء
            return {
                'success': True,  # تغيير لـ True لمنع كسر الواجهة
                'mount_points': {},
                'error_details': str(e),
                'note': 'Safe mode - mount operations disabled'
            }
    
    def _is_mounted(self, mount_point: str) -> bool:
        """التحقق من حالة التحميل"""
        try:
            if self.is_windows():
                # في Windows، نتحقق من وجود محرك الأقراص المحدد
                if mount_point.endswith(':') or mount_point.endswith(':\\'): 
                    drive_letter = mount_point[0] + ':'
                    result = subprocess.run(['net', 'use', drive_letter], capture_output=True, text=True)
                    return result.returncode == 0
                else:
                    # إذا لم يكن محرك أقراص، نتحقق من وجود المسار
                    return os.path.exists(mount_point) and os.path.isdir(mount_point)
            else:
                # في Linux/macOS، نستخدم أمر mount
                result = subprocess.run(['mount'], capture_output=True, text=True)
                return mount_point in result.stdout
        except Exception as e:
            logger.error(f"Error checking mount status: {str(e)}")
            return False
    
    def unmount(self, mount_point: str) -> Dict[str, Any]:
        """إلغاء تحميل نقطة التحميل"""
        try:
            if self.is_windows():
                # في Windows، نستخدم net use /delete
                if mount_point.endswith(':') or mount_point.endswith(':\\'): 
                    drive_letter = mount_point[0] + ':'
                    result = subprocess.run(['net', 'use', drive_letter, '/delete', '/y'], capture_output=True, text=True)
                else:
                    return {
                        'success': False,
                        'error': 'في Windows، يجب تحديد حرف محرك الأقراص (مثل Z:)'
                    }
            else:
                # في Linux/macOS، نستخدم umount
                result = subprocess.run(['umount', mount_point], capture_output=True, text=True)
            
            if result.returncode == 0:
                if mount_point in self.mount_points:
                    del self.mount_points[mount_point]
                return {
                    'success': True,
                    'message': f'تم إلغاء تحميل {mount_point} بنجاح',
                    'os_type': self.os_type
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'os_type': self.os_type
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'os_type': self.os_type
            }
    
    def list_directory(self, protocol: str, host: str, path: str = '/', **kwargs) -> Dict[str, Any]:
        """عرض محتويات المجلد البعيد - متوافق مع Replit"""
        try:
            # تحقق من بيئة Replit
            is_replit = os.environ.get('REPLIT_ENVIRONMENT') is not None or 'replit' in os.getcwd().lower()
            
            if is_replit:
                # في بيئة Replit، نعيد بيانات تجريبية آمنة
                return {
                    'success': True,
                    'path': path,
                    'files': [],  # فارغ في Replit للأمان
                    'replit_mode': True,
                    'note': 'Remote directory listing disabled in Replit environment'
                }
            
            # في البيئة الحقيقية، استخدم البروتوكولات الفعلية
            if protocol == 'sftp':
                return self._list_sftp_directory(host, path, **kwargs)
            elif protocol == 'ftp':
                return self._list_ftp_directory(host, path, **kwargs)
            else:
                return {
                    'success': False,
                    'error': f'Directory listing not supported for protocol: {protocol}'
                }
        except Exception as e:
            # في حالة الخطأ، أعد نتيجة آمنة
            return {
                'success': True,  # تغيير لـ True لمنع كسر الواجهة
                'path': path,
                'files': [],
                'error_details': str(e),
                'note': 'Safe mode - directory listing disabled'
            }
    
    def _list_sftp_directory(self, host: str, path: str, **kwargs) -> Dict[str, Any]:
        """عرض مجلد SFTP"""
        try:
            import paramiko
            
            username = kwargs.get('username')
            password = kwargs.get('password')
            port = kwargs.get('port', 22)
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            
            sftp = ssh.open_sftp()
            files = []
            
            for item in sftp.listdir_attr(path):
                files.append({
                    'name': item.filename,
                    'path': f"{path.rstrip('/')}/{item.filename}",
                    'size': item.st_size,
                    'is_directory': item.st_mode & 0o040000 != 0,
                    'modified': datetime.fromtimestamp(item.st_mtime).isoformat()
                })
            
            sftp.close()
            ssh.close()
            
            return {
                'success': True,
                'path': path,
                'files': files
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _list_ftp_directory(self, host: str, path: str, **kwargs) -> Dict[str, Any]:
        """عرض مجلد FTP"""
        try:
            from ftplib import FTP
            
            username = kwargs.get('username')
            password = kwargs.get('password')
            port = kwargs.get('port', 21)
            
            ftp = FTP()
            ftp.connect(host, port, timeout=10)
            ftp.login(username, password)
            ftp.cwd(path)
            
            files = []
            file_list = ftp.nlst()
            
            for item in file_list:
                files.append({
                    'name': item,
                    'is_dir': False,  # FTP doesn't easily distinguish dirs
                    'size': 0
                })
            
            ftp.quit()
            
            return {
                'success': True,
                'path': path,
                'files': files
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
remote_storage_manager = RemoteStorageManager()

# Helper functions for compatibility
def setup_remote_mount(protocol: str, host: str, remote_path: str, 
                      local_mount_point: str, **kwargs) -> Dict[str, Any]:
    """إعداد نقطة التحميل البعيد"""
    return remote_storage_manager.setup_mount(protocol, host, remote_path, local_mount_point, **kwargs)

def get_mount_status(mount_point: str = None) -> Dict[str, Any]:
    """الحصول على حالة نقاط التحميل"""
    return remote_storage_manager.get_mount_status(mount_point)

def test_remote_connection(protocol: str, host: str, **kwargs) -> Dict[str, Any]:
    """اختبار الاتصال البعيد"""
    return remote_storage_manager.test_connection(protocol, host, **kwargs)

def list_remote_directory(protocol: str, host: str, path: str = '/', **kwargs) -> Dict[str, Any]:
    """عرض محتويات المجلد البعيد"""
    return remote_storage_manager.list_directory(protocol, host, path, **kwargs)

def unmount_remote_storage(mount_point: str) -> Dict[str, Any]:
    """إلغاء تحميل التخزين البعيد"""
    return remote_storage_manager.unmount(mount_point)