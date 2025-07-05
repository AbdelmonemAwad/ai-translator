#!/usr/bin/env python3
"""
Remote Storage Management Module for AI Translator
إدارة التخزين البعيد للترجمان الآلي
"""

import os
import logging
import subprocess
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RemoteStorageManager:
    """إدارة التخزين البعيد والاتصال بالشبكة"""
    
    def __init__(self):
        self.supported_protocols = ['sftp', 'ftp', 'smb', 'nfs', 'sshfs']
        self.mount_points = {}
        self.connection_cache = {}
    
    def test_connection(self, protocol: str, host: str, port: int = None, 
                       username: str = None, password: str = None, 
                       share_path: str = None) -> Dict[str, Any]:
        """اختبار الاتصال بالخادم البعيد"""
        try:
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
    
    def get_mount_status(self, mount_point: str = None) -> Dict[str, Any]:
        """الحصول على حالة نقاط التحميل"""
        try:
            if mount_point:
                # Check specific mount point
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
                        'success': False,
                        'error': 'Mount point not found'
                    }
            else:
                # Check all mount points
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
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_mounted(self, mount_point: str) -> bool:
        """التحقق من حالة التحميل"""
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            return mount_point in result.stdout
        except Exception:
            return False
    
    def unmount(self, mount_point: str) -> Dict[str, Any]:
        """إلغاء تحميل نقطة التحميل"""
        try:
            result = subprocess.run(['umount', mount_point], capture_output=True, text=True)
            
            if result.returncode == 0:
                if mount_point in self.mount_points:
                    del self.mount_points[mount_point]
                return {
                    'success': True,
                    'message': f'Successfully unmounted {mount_point}'
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
    
    def list_directory(self, protocol: str, host: str, path: str = '/', **kwargs) -> Dict[str, Any]:
        """عرض محتويات المجلد البعيد"""
        try:
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
            return {
                'success': False,
                'error': str(e)
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
                    'size': item.st_size,
                    'is_dir': item.st_mode & 0o040000 != 0,
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