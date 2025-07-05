#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import tempfile
import json
import requests
from datetime import datetime
from pathlib import Path

def log_message(message):
    """Log message to console and process log file"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    try:
        process_log = os.path.join(os.path.dirname(__file__), "process.log")
        with open(process_log, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

# استيراد النظام الجديد للذكاء الاصطناعي
try:
    from ai_integration_workaround import process_video as ai_process_video
    from ai_integration_workaround import get_ai_status
    AI_INTEGRATION_AVAILABLE = True
    log_message("✓ AI Integration system loaded successfully")
except ImportError as e:
    AI_INTEGRATION_AVAILABLE = False
    log_message(f"⚠ AI Integration system not available: {e}")
    log_message("Falling back to original implementation")

def get_settings():
    """Get settings from PostgreSQL database using Flask app context"""
    try:
        # Import Flask app and models
        sys.path.append(os.path.dirname(__file__))
        from app import app, db
        from models import Settings
        
        with app.app_context():
            settings = {}
            all_settings = Settings.query.all()
            for setting in all_settings:
                settings[setting.key] = setting.value
            return settings
    except Exception as e:
        log_message(f"Error reading settings from PostgreSQL: {e}")
        # Fallback to environment variables
        return {
            'ollama_api_url': os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate'),
            'ollama_model': os.environ.get('OLLAMA_MODEL', 'llama3'),
            'whisper_model': os.environ.get('WHISPER_MODEL', 'medium.en')
        }

def check_existing_translation(video_path):
    """Check if Arabic subtitle file already exists"""
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Check for Arabic subtitle file
    arabic_srt_path = os.path.join(video_dir, f"{video_name}.ar.srt")
    return os.path.exists(arabic_srt_path)

def update_translation_status(video_path, translated=True):
    """Update translation status in PostgreSQL database"""
    try:
        # Import Flask app and models
        sys.path.append(os.path.dirname(__file__))
        from app import app, db
        from models import MediaFile
        from datetime import datetime
        
        with app.app_context():
            # Find media file by path
            media_file = MediaFile.query.filter_by(path=video_path).first()
            
            if media_file:
                media_file.translated = translated
                if translated:
                    media_file.translation_completed_at = datetime.utcnow()
                db.session.commit()
                log_message(f"Updated translation status for: {os.path.basename(video_path)}")
                return True
            else:
                log_message(f"Warning: No database record found for: {os.path.basename(video_path)}")
                return False
                
    except Exception as e:
        log_message(f"Failed to update translation status: {str(e)}")
        return False

def extract_audio(video_path, audio_path):
    """Extract audio from video file using ffmpeg"""
    log_message(f"Extracting audio from: {os.path.basename(video_path)}")
    
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
        '-ar', '16000',  # 16 kHz sample rate for Whisper
        '-ac', '1',  # Mono
        '-y',  # Overwrite output file
        audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            raise Exception(f"ffmpeg error: {result.stderr}")
        log_message("Audio extraction completed successfully")
        return True
    except subprocess.TimeoutExpired:
        log_message("Audio extraction timed out (1 hour limit)")
        return False
    except Exception as e:
        log_message(f"Audio extraction failed: {str(e)}")
        return False

def transcribe_with_whisper(audio_path, settings):
    """Transcribe audio using Whisper"""
    log_message("Starting Whisper transcription...")
    
    model = settings.get('whisper_model', 'medium.en')
    gpu_id = settings.get('whisper_gpu_id', 'auto')
    
    # Determine device and GPU configuration
    device = 'cuda'
    gpu_device = '0'
    
    if gpu_id == 'cpu':
        device = 'cpu'
        log_message(f"Using Whisper model: {model} on CPU")
    elif gpu_id == 'auto':
        # Use auto GPU selection (default CUDA device)
        log_message(f"Using Whisper model: {model} on GPU (auto selection)")
    else:
        try:
            gpu_device = str(int(gpu_id))
            log_message(f"Using Whisper model: {model} on GPU {gpu_device}")
        except ValueError:
            log_message(f"Invalid GPU ID: {gpu_id}, using auto selection")
    
    cmd = [
        'whisper', audio_path,
        '--model', model,
        '--language', 'en',
        '--output_format', 'srt',
        '--output_dir', os.path.dirname(audio_path),
        '--device', device if device == 'cpu' else f'cuda:{gpu_device}',
        '--verbose', 'False'
    ]
    
    # Set CUDA_VISIBLE_DEVICES for this process
    env = os.environ.copy()
    if device == 'cpu':
        env['CUDA_VISIBLE_DEVICES'] = ''
    elif gpu_id != 'auto':
        env['CUDA_VISIBLE_DEVICES'] = gpu_device
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200, env=env)  # 2 hours
        if result.returncode != 0:
            raise Exception(f"Whisper error: {result.stderr}")
        
        # Find the generated SRT file
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        srt_path = os.path.join(os.path.dirname(audio_path), f"{audio_name}.srt")
        
        if os.path.exists(srt_path):
            log_message("Whisper transcription completed successfully")
            return srt_path
        else:
            raise Exception("Whisper did not generate SRT file")
            
    except subprocess.TimeoutExpired:
        log_message("Whisper transcription timed out (2 hour limit)")
        return None
    except Exception as e:
        log_message(f"Whisper transcription failed: {str(e)}")
        return None

def translate_with_ollama(text, settings):
    """Translate text using Ollama API"""
    api_url = settings.get('ollama_api_url', 'http://localhost:11434/api/generate')
    model = settings.get('ollama_model', 'llama3')
    gpu_id = settings.get('ollama_gpu_id', 'auto')
    
    # Log GPU configuration for Ollama
    if gpu_id == 'cpu':
        log_message(f"Using Ollama model: {model} on CPU")
    elif gpu_id == 'auto':
        log_message(f"Using Ollama model: {model} on GPU (auto selection)")
    else:
        try:
            gpu_device = int(gpu_id)
            log_message(f"Using Ollama model: {model} on GPU {gpu_device}")
        except ValueError:
            log_message(f"Invalid GPU ID: {gpu_id}, using auto selection")
    
    prompt = f"""Please translate the following English subtitle text to Arabic. Keep the timing format intact and translate only the text content:

{text}

Important instructions:
- Maintain all SRT formatting (timestamps, line numbers)
- Translate only the dialogue text, not the timestamps
- Keep the same structure and line breaks
- Use natural, fluent Arabic
- For proper nouns (names, places), use appropriate Arabic transliteration"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 4000
        }
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        if 'response' in result:
            return result['response'].strip()
        else:
            raise Exception("No response field in Ollama API result")
            
    except requests.exceptions.Timeout:
        raise Exception("Ollama API request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Ollama translation error: {str(e)}")

def process_srt_file(srt_path, settings):
    """Process SRT file and translate it to Arabic"""
    log_message("Starting SRT translation with Ollama...")
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(srt_path, 'r', encoding=encoding) as f:
                    original_content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Could not decode SRT file with any common encoding")
    
    if not original_content.strip():
        raise Exception("SRT file is empty")
    
    # Split content into chunks if it's too long
    max_chunk_size = 2000  # Characters
    chunks = []
    
    if len(original_content) <= max_chunk_size:
        chunks = [original_content]
    else:
        # Split by subtitle blocks
        blocks = original_content.split('\n\n')
        current_chunk = ""
        
        for block in blocks:
            if len(current_chunk + block) <= max_chunk_size:
                current_chunk += block + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = block + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
    
    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        log_message(f"Translating chunk {i+1}/{len(chunks)}...")
        try:
            translated_chunk = translate_with_ollama(chunk, settings)
            translated_chunks.append(translated_chunk)
        except Exception as e:
            log_message(f"Failed to translate chunk {i+1}: {str(e)}")
            # Use original chunk if translation fails
            translated_chunks.append(chunk)
    
    # Combine translated chunks
    final_translation = '\n\n'.join(translated_chunks)
    
    return final_translation

def main(video_path):
    """Main processing function"""
    if not os.path.exists(video_path):
        log_message(f"Error: Video file does not exist: {video_path}")
        return False
    
    log_message(f"Starting processing of: {os.path.basename(video_path)}")
    
    # Get settings
    settings = get_settings()
    if not settings:
        log_message("Warning: Could not load settings, using defaults")
        settings = {
            'whisper_model': 'medium.en',
            'ollama_api_url': 'http://localhost:11434/api/generate',
            'ollama_model': 'llama3'
        }
    
    # Check if Arabic subtitle already exists
    base_path = os.path.splitext(video_path)[0]
    arabic_srt_path = f"{base_path}.ar.srt"
    
    if os.path.exists(arabic_srt_path):
        log_message("Arabic subtitle already exists, skipping...")
        return True
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        # Step 1: Extract audio
        if not extract_audio(video_path, audio_path):
            log_message("Failed to extract audio")
            return False
        
        # Step 2: Transcribe with Whisper
        srt_path = transcribe_with_whisper(audio_path, settings)
        if not srt_path:
            log_message("Failed to transcribe audio")
            return False
        
        # Step 3: Translate SRT to Arabic
        try:
            arabic_content = process_srt_file(srt_path, settings)
            
            # Save Arabic subtitle
            with open(arabic_srt_path, 'w', encoding='utf-8') as f:
                f.write(arabic_content)
            
            log_message(f"Successfully created Arabic subtitle: {os.path.basename(arabic_srt_path)}")
            
            # Update translation status in database
            update_translation_status(video_path, translated=True)
            
            return True
            
        except Exception as e:
            log_message(f"Failed to translate subtitles: {str(e)}")
            # Update status to indicate failure
            update_translation_status(video_path, translated=False)
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_video.py <video_file_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    success = main(video_path)
    sys.exit(0 if success else 1)
