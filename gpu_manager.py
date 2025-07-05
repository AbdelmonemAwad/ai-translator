#!/usr/bin/env python3
"""
GPU Manager - Advanced GPU Detection and Management System
Handles NVIDIA GPU detection, monitoring, and allocation for AI services
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Optional, Tuple

class GPUManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gpus = []
        self.nvidia_available = False
        self.refresh_gpu_info()
    
    def run_command(self, command: List[str]) -> Tuple[bool, str]:
        """Run a system command and return success status and output"""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0, result.stdout.strip()
        except FileNotFoundError:
            # Silently handle missing commands in cloud environments
            return False, f"Command not found: {command[0]}"
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Command timeout: {' '.join(command)}")
            return False, "Command timeout"
        except Exception as e:
            # Handle permission and other errors gracefully
            return False, str(e)
    
    def detect_nvidia_gpus(self) -> List[Dict]:
        """Detect NVIDIA GPUs using nvidia-smi"""
        gpus = []
        
        # Check if nvidia-smi is available
        success, output = self.run_command(['nvidia-smi', '--version'])
        if not success:
            self.logger.info("NVIDIA drivers not detected")
            return gpus
        
        # Query GPU information
        command = [
            'nvidia-smi',
            '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,power.limit',
            '--format=csv,noheader,nounits'
        ]
        
        success, output = self.run_command(command)
        if not success:
            self.logger.error(f"Failed to query GPU info: {output}")
            return gpus
        
        for line in output.split('\n'):
            if line.strip():
                try:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 9:
                        gpu_info = {
                            'id': int(parts[0]),
                            'name': parts[1],
                            'memory_total': int(parts[2]) if parts[2] != '[Not Supported]' else 0,
                            'memory_used': int(parts[3]) if parts[3] != '[Not Supported]' else 0,
                            'memory_free': int(parts[4]) if parts[4] != '[Not Supported]' else 0,
                            'utilization': int(parts[5]) if parts[5] != '[Not Supported]' else 0,
                            'temperature': int(parts[6]) if parts[6] != '[Not Supported]' else 0,
                            'power_draw': float(parts[7]) if parts[7] != '[Not Supported]' else 0.0,
                            'power_limit': float(parts[8]) if parts[8] != '[Not Supported]' else 0.0,
                            'type': 'NVIDIA',
                            'driver_version': self.get_nvidia_driver_version(),
                            'cuda_version': self.get_cuda_version()
                        }
                        
                        # Calculate memory usage percentage
                        if gpu_info['memory_total'] > 0:
                            gpu_info['memory_usage_percent'] = (gpu_info['memory_used'] / gpu_info['memory_total']) * 100
                        else:
                            gpu_info['memory_usage_percent'] = 0
                        
                        # Performance scoring (0-100)
                        gpu_info['performance_score'] = self.calculate_performance_score(gpu_info)
                        
                        gpus.append(gpu_info)
                except Exception as e:
                    self.logger.error(f"Failed to parse GPU info line: {line} - {e}")
        
        return gpus
    
    def get_nvidia_driver_version(self) -> str:
        """Get NVIDIA driver version"""
        success, output = self.run_command(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'])
        if success and output:
            return output.split('\n')[0].strip()
        return "Unknown"
    
    def get_cuda_version(self) -> str:
        """Get CUDA version"""
        success, output = self.run_command(['nvcc', '--version'])
        if success and 'release' in output:
            for line in output.split('\n'):
                if 'release' in line:
                    parts = line.split('release')
                    if len(parts) > 1:
                        version = parts[1].split(',')[0].strip()
                        return f"CUDA {version}"
        return "Unknown"
    
    def detect_system_gpus(self) -> List[Dict]:
        """Detect GPUs using lspci (fallback method)"""
        gpus = []
        
        success, output = self.run_command(['lspci', '-nn'])
        if not success:
            return gpus
        
        gpu_id = 0
        for line in output.split('\n'):
            if 'VGA compatible controller' in line or 'Display controller' in line:
                # Extract GPU name
                parts = line.split(': ')
                if len(parts) > 1:
                    name = parts[1].split('[')[0].strip()
                    
                    gpu_info = {
                        'id': gpu_id,
                        'name': name,
                        'memory_total': 0,  # Not available via lspci
                        'memory_used': 0,
                        'memory_free': 0,
                        'utilization': 0,
                        'temperature': 0,
                        'power_draw': 0.0,
                        'power_limit': 0.0,
                        'memory_usage_percent': 0,
                        'performance_score': 50,  # Default score
                        'type': 'Generic',
                        'driver_version': 'Unknown',
                        'cuda_version': 'Not Available'
                    }
                    
                    gpus.append(gpu_info)
                    gpu_id += 1
        
        return gpus
    
    def calculate_performance_score(self, gpu_info: Dict) -> int:
        """Calculate GPU performance score (0-100)"""
        score = 50  # Base score
        
        # Memory-based scoring
        if gpu_info['memory_total'] > 0:
            if gpu_info['memory_total'] >= 24000:  # 24GB+
                score += 25
            elif gpu_info['memory_total'] >= 16000:  # 16GB+
                score += 20
            elif gpu_info['memory_total'] >= 12000:  # 12GB+
                score += 15
            elif gpu_info['memory_total'] >= 8000:   # 8GB+
                score += 10
            elif gpu_info['memory_total'] >= 6000:   # 6GB+
                score += 5
        
        # Name-based scoring (common GPU models)
        name_lower = gpu_info['name'].lower()
        if 'rtx 4090' in name_lower or 'a100' in name_lower:
            score += 20
        elif 'rtx 4080' in name_lower or 'rtx 3090' in name_lower:
            score += 15
        elif 'rtx 4070' in name_lower or 'rtx 3080' in name_lower:
            score += 10
        elif 'rtx 3070' in name_lower or 'rtx 3060' in name_lower:
            score += 5
        
        # Utilization penalty
        if gpu_info['utilization'] > 80:
            score -= 10
        elif gpu_info['utilization'] > 60:
            score -= 5
        
        # Temperature penalty
        if gpu_info['temperature'] > 85:
            score -= 15
        elif gpu_info['temperature'] > 75:
            score -= 10
        elif gpu_info['temperature'] > 65:
            score -= 5
        
        return max(0, min(100, score))
    
    def refresh_gpu_info(self):
        """Refresh GPU information - Real system detection only"""
        self.gpus = []
        self.nvidia_available = False
        
        # Try NVIDIA detection first
        nvidia_gpus = self.detect_nvidia_gpus()
        if nvidia_gpus:
            self.nvidia_available = True
            self.gpus.extend(nvidia_gpus)
            self.logger.info(f"Detected {len(nvidia_gpus)} NVIDIA GPU(s)")
        else:
            # Try system GPU detection as fallback
            system_gpus = self.detect_system_gpus()
            if system_gpus:
                self.gpus.extend(system_gpus)
                self.logger.info(f"Detected {len(system_gpus)} system GPU(s) via lspci")
            else:
                self.logger.info("No GPU hardware detected on this system")
        
        self.logger.info(f"Total GPU count: {len(self.gpus)}")
    
    def get_gpu_status(self) -> Dict:
        """Get comprehensive GPU status"""
        return {
            'nvidia_available': self.nvidia_available,
            'gpu_count': len(self.gpus),
            'gpus': self.gpus,
            'recommended_allocation': self.get_recommended_allocation()
        }
    
    def get_recommended_allocation(self) -> Dict:
        """Get recommended GPU allocation for AI services"""
        if not self.gpus:
            return {
                'whisper': 'cpu',
                'ollama': 'cpu',
                'strategy': 'cpu_only',
                'recommendation': 'لا توجد كروت شاشة متاحة، سيتم استخدام المعالج لجميع الخدمات',
                'suggestion': 'يُنصح بتثبيت تعريفات كروت الشاشة NVIDIA'
            }
        
        if len(self.gpus) == 1:
            gpu = self.gpus[0]
            memory_gb = gpu.get('memory_total_gb', 0)
            
            if memory_gb >= 12:
                return {
                    'whisper': str(gpu['id']),
                    'ollama': str(gpu['id']),
                    'strategy': 'single_shared',
                    'recommendation': f"كارت واحد بذاكرة كبيرة ({memory_gb}GB) - مشاركة مثلى بين الخدمات",
                    'suggestion': 'توزيع مثالي للذاكرة بين Whisper و Ollama'
                }
            elif memory_gb >= 6:
                return {
                    'whisper': str(gpu['id']),
                    'ollama': 'cpu',
                    'strategy': 'single_whisper',
                    'recommendation': f"كارت بذاكرة متوسطة ({memory_gb}GB) - Whisper على GPU، Ollama على CPU",
                    'suggestion': 'Whisper يحتاج ذاكرة أقل من Ollama'
                }
            else:
                return {
                    'whisper': 'cpu',
                    'ollama': str(gpu['id']),
                    'strategy': 'single_ollama',
                    'recommendation': f"كارت بذاكرة محدودة ({memory_gb}GB) - Ollama على GPU، Whisper على CPU",
                    'suggestion': 'Ollama يستفيد أكثر من تسريع GPU'
                }
        
        elif len(self.gpus) >= 2:
            # Multiple GPUs - intelligent dedicated allocation
            sorted_gpus = sorted(self.gpus, key=lambda x: x.get('performance_score', 0), reverse=True)
            
            best_gpu = sorted_gpus[0]
            second_gpu = sorted_gpus[1]
            
            best_memory = best_gpu.get('memory_total_gb', 0)
            second_memory = second_gpu.get('memory_total_gb', 0)
            
            # Strategy: Best GPU for Ollama (more demanding), Second for Whisper
            return {
                'whisper': str(second_gpu['id']),  # Second best for Whisper
                'ollama': str(best_gpu['id']),     # Best for Ollama (more demanding)
                'strategy': 'dual_optimized',
                'recommendation': f"توزيع مثالي - أقوى كارت ({best_memory}GB) لـ Ollama، ثاني أقوى ({second_memory}GB) لـ Whisper",
                'suggestion': 'كل خدمة على كارت منفصل لأداء أقصى'
            }
        
        # Fallback
        return {
            'whisper': 'auto',
            'ollama': 'auto',
            'strategy': 'auto',
            'recommendation': 'تحديد تلقائي حسب النظام',
            'suggestion': 'سيتم اختيار أفضل إعداد متاح'
        }
    
    def allocate_gpus(self, whisper_gpu: str, ollama_gpu: str) -> Dict:
        """Allocate GPUs to services"""
        allocation = {
            'whisper': whisper_gpu,
            'ollama': ollama_gpu,
            'environment_vars': {}
        }
        
        # Set CUDA_VISIBLE_DEVICES for each service
        if whisper_gpu != 'cpu' and whisper_gpu != 'auto':
            allocation['environment_vars']['WHISPER_CUDA_VISIBLE_DEVICES'] = whisper_gpu
        
        if ollama_gpu != 'cpu' and ollama_gpu != 'auto':
            allocation['environment_vars']['OLLAMA_CUDA_VISIBLE_DEVICES'] = ollama_gpu
        
        return allocation
    
    def get_gpu_options(self) -> List[Dict]:
        """Get GPU options for dropdowns with detailed GPU information"""
        options = [
            {'value': 'auto', 'label': 'تلقائي / Auto'},
            {'value': 'cpu', 'label': 'معالج فقط / CPU Only'}
        ]
        
        # Refresh GPU info to ensure we have latest data
        self.refresh_gpu_info()
        
        for gpu in self.gpus:
            gpu_name = gpu.get('name', f"GPU {gpu['id']}")
            memory_gb = gpu.get('memory_total_gb', 0)
            
            # Calculate memory from bytes if GB not available
            if memory_gb == 0 and gpu.get('memory_total'):
                memory_gb = round(gpu['memory_total'] / (1024**3), 1)
            
            # Get performance indicator
            performance = gpu.get('performance_score', 0)
            if performance >= 80:
                performance_icon = "⚡"  # High performance
            elif performance >= 60:
                performance_icon = "🔶"  # Medium performance
            else:
                performance_icon = "🔸"  # Basic performance
            
            # Create comprehensive label
            memory_info = f" ({memory_gb}GB)" if memory_gb > 0 else ""
            short_name = gpu_name[:25] + "..." if len(gpu_name) > 25 else gpu_name
            
            label = f"{performance_icon} كارت الشاشة {gpu['id']} / {short_name}{memory_info}"
            
            options.append({
                'value': str(gpu['id']),
                'label': label.strip()
            })
        
        return options
    
    def diagnose_gpu_setup(self) -> Dict:
        """Diagnose GPU setup and provide installation recommendations"""
        diagnosis = {
            'nvidia_driver_installed': False,
            'cuda_installed': False,
            'gpu_detected': False,
            'recommendations': [],
            'installation_commands': []
        }
        
        # Check NVIDIA driver
        success, output = self.run_command(['nvidia-smi', '--version'])
        if success:
            diagnosis['nvidia_driver_installed'] = True
            diagnosis['driver_version'] = output.split('\n')[0] if output else 'Unknown'
        else:
            diagnosis['recommendations'].append('تثبيت تعريفات NVIDIA GPU')
            diagnosis['installation_commands'].append('sudo apt update && sudo apt install nvidia-driver-535 nvidia-utils-535')
        
        # Check CUDA
        success, output = self.run_command(['nvcc', '--version'])
        if success:
            diagnosis['cuda_installed'] = True
            diagnosis['cuda_version'] = output.split('release')[1].split(',')[0].strip() if 'release' in output else 'Unknown'
        else:
            diagnosis['recommendations'].append('تثبيت CUDA Toolkit')
            diagnosis['installation_commands'].append('sudo apt install nvidia-cuda-toolkit')
        
        # Check GPU detection
        if self.gpus:
            diagnosis['gpu_detected'] = True
            diagnosis['gpu_count'] = len(self.gpus)
        else:
            diagnosis['recommendations'].append('إعادة تشغيل النظام بعد تثبيت التعريفات')
            diagnosis['installation_commands'].append('sudo reboot')
        
        # Check Docker NVIDIA runtime (for containerized environments)
        success, output = self.run_command(['docker', 'info'])
        if success and 'nvidia' in output.lower():
            diagnosis['docker_nvidia_runtime'] = True
        else:
            diagnosis['recommendations'].append('تثبيت NVIDIA Container Runtime للـ Docker')
            diagnosis['installation_commands'].append('sudo apt install nvidia-container-runtime')
        
        return diagnosis
    
    def get_installation_script(self) -> str:
        """Generate complete GPU setup installation script"""
        script = """#!/bin/bash
# GPU Setup Installation Script - مساعد تثبيت كروت الشاشة
# Generated by AI Translator v2.2.4

echo "🚀 بدء تثبيت تعريفات وأدوات كروت الشاشة NVIDIA..."

# Update system
echo "📦 تحديث النظام..."
sudo apt update && sudo apt upgrade -y

# Install NVIDIA drivers
echo "🎮 تثبيت تعريفات NVIDIA..."
sudo apt install -y nvidia-driver-535 nvidia-utils-535

# Install CUDA Toolkit
echo "⚡ تثبيت CUDA Toolkit..."
sudo apt install -y nvidia-cuda-toolkit

# Install development tools
echo "🛠️ تثبيت أدوات التطوير..."
sudo apt install -y build-essential nvidia-cuda-dev

# Install NVIDIA Container Runtime (for Docker)
echo "🐳 تثبيت NVIDIA Container Runtime..."
sudo apt install -y nvidia-container-runtime

# Install monitoring tools
echo "📊 تثبيت أدوات المراقبة..."
sudo apt install -y nvidia-smi htop

# Install Python GPU libraries
echo "🐍 تثبيت مكتبات Python للـ GPU..."
pip install pynvml gpustat

echo "✅ تم الانتهاء من التثبيت!"
echo "🔄 يُنصح بإعادة تشغيل النظام الآن: sudo reboot"
echo "🧪 للتحقق من التثبيت: nvidia-smi"
"""
        return script
    
    def get_available_gpus(self) -> List[Dict]:
        """Get list of available GPUs - alias for self.gpus"""
        return self.gpus
    
    def get_optimal_allocation(self) -> Dict:
        """Get optimal GPU allocation - alias for get_recommended_allocation"""
        return self.get_recommended_allocation()
    
    def is_nvidia_available(self) -> bool:
        """Check if NVIDIA drivers are available"""
        return self.nvidia_available

# Global GPU manager instance
gpu_manager = GPUManager()

def get_gpu_status():
    """Get GPU status (for API endpoints)"""
    return gpu_manager.get_gpu_status()

def refresh_gpu_info():
    """Refresh GPU information (for API endpoints)"""
    gpu_manager.refresh_gpu_info()
    return gpu_manager.get_gpu_status()

def get_gpu_options():
    """Get GPU options for dropdowns"""
    return gpu_manager.get_gpu_options()

def get_gpu_environment_variables(service: str, gpu_id: int = None) -> dict:
    """Get environment variables for GPU allocation"""
    if gpu_id is not None:
        return {
            "CUDA_VISIBLE_DEVICES": str(gpu_id),
            "NVIDIA_VISIBLE_DEVICES": str(gpu_id)
        }
    else:
        return {
            "CUDA_VISIBLE_DEVICES": "",
            "NVIDIA_VISIBLE_DEVICES": ""
        }
