# AI Translator API Documentation
# توثيق واجهة برمجة التطبيقات - المترجم الآلي

## Overview
This document provides comprehensive API documentation for AI Translator's REST API endpoints.

## Base URL
```
http://localhost:5000
```

## Authentication
All API endpoints require session-based authentication. Login through the web interface first.

## API Endpoints

### System Status
```http
GET /api/status
```
Returns current system status and translation progress.

**Response:**
```json
{
  "status": "idle|processing|error",
  "progress": 75.5,
  "current_file": "/path/to/video.mp4",
  "total_files": 10,
  "files_done": 7,
  "is_running": true,
  "log_tail": "Latest log entries..."
}
```

### Media Files Management
```http
GET /api/files
```
Returns paginated list of media files with filtering options.

**Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 24)
- `search` (string): Search query
- `media_type` (string): Filter by type (movie|episode)
- `status` (string): Filter by status (all|translated|untranslated|blacklisted)

**Response:**
```json
{
  "files": [
    {
      "id": 1,
      "title": "Movie Title",
      "year": 2023,
      "media_type": "movie",
      "translated": false,
      "blacklisted": false,
      "poster_url": "http://...",
      "service_source": "radarr"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 10,
    "per_page": 24,
    "total": 240
  }
}
```

### Media Services Integration

#### Test Service Connection
```http
GET /api/test-media-service/<service_type>
```
Tests connection to a specific media service.

**Service Types:** `plex`, `jellyfin`, `emby`, `kodi`, `radarr`, `sonarr`

**Response:**
```json
{
  "success": true,
  "message": "Successfully connected to Plex",
  "version": "1.32.5.7349",
  "status": "online"
}
```

#### Sync Media Service
```http
POST /api/sync-media-service/<service_type>
```
Syncs media library from specific service.

**Response:**
```json
{
  "success": true,
  "message": "Successfully synced 150 items from Plex",
  "media_count": 150,
  "sync_time": "2025-06-29T12:00:00Z"
}
```

#### Get All Services Status
```http
GET /api/media-services-status
```
Returns status of all configured media services.

**Response:**
```json
{
  "plex": {
    "success": true,
    "status": "online",
    "version": "1.32.5.7349"
  },
  "radarr": {
    "success": true,
    "status": "online", 
    "version": "4.7.5.7809"
  }
}
```

### GPU Management

#### Get GPU Status
```http
GET /api/gpu-status
```
Returns NVIDIA GPU information and allocation.

**Response:**
```json
{
  "nvidia_available": true,
  "gpus": [
    {
      "id": 0,
      "name": "NVIDIA GeForce RTX 4080",
      "memory_total": 16384,
      "memory_used": 2048,
      "memory_free": 14336,
      "utilization": 15,
      "temperature": 45,
      "performance_score": 95
    }
  ],
  "current_allocation": {
    "whisper_gpu": 0,
    "ollama_gpu": 0
  }
}
```

#### Auto-Allocate GPUs
```http
POST /api/gpu-auto-allocate
```
Automatically allocates GPUs based on optimal configuration.

### Translation Operations

#### Start Batch Translation
```http
POST /action/start-batch
```
Starts batch translation process.

#### Stop Translation
```http
POST /action/stop
```
Stops current translation process.

#### Scan Translation Status
```http
GET /action/scan-translation-status
```
Scans all media files and updates translation status.

**Response:**
```json
{
  "success": true,
  "scanned_files": 1250,
  "updated_files": 45,
  "message": "Translation status scan completed"
}
```

### System Monitoring

#### System Monitor Stats
```http
GET /api/system-monitor-stats
```
Returns real-time system resource usage.

**Response:**
```json
{
  "cpu": {
    "usage": 25.5,
    "cores": 8
  },
  "memory": {
    "used": 8192,
    "total": 16384,
    "percent": 50.0
  },
  "disk": {
    "used": 500000,
    "total": 1000000,
    "percent": 50.0
  },
  "gpu": [
    {
      "name": "RTX 4080",
      "utilization": 15,
      "memory_used": 2048,
      "memory_total": 16384
    }
  ]
}
```

### Database Administration

#### Database Stats
```http
GET /api/database-stats
```
Returns database statistics and table information.

#### Execute SQL Query
```http
POST /api/database-query
```
Executes SQL query (admin only).

**Request Body:**
```json
{
  "query": "SELECT COUNT(*) FROM media_files"
}
```

### Notifications

#### Get Notifications
```http
GET /api/notifications
```
Returns user notifications.

#### Mark Notification as Read
```http
POST /api/notifications/<id>/read
```

#### Clear All Notifications
```http
DELETE /api/notifications/clear
```

### File Browser

#### Browse Folders
```http
GET /api/browse-folders
```
Returns folder structure for file browser.

**Parameters:**
- `path` (string): Directory path to browse

**Response:**
```json
{
  "current_path": "/mnt/storage",
  "parent_path": "/mnt",
  "folders": [
    {
      "name": "movies",
      "path": "/mnt/storage/movies",
      "type": "folder"
    }
  ]
}
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `AUTH_REQUIRED`: Authentication required
- `INVALID_PARAMS`: Invalid request parameters
- `SERVICE_UNAVAILABLE`: External service unavailable
- `DATABASE_ERROR`: Database operation failed
- `GPU_ERROR`: GPU operation failed

## Rate Limiting
API endpoints are rate-limited to prevent abuse:
- 100 requests per minute for general endpoints
- 10 requests per minute for heavy operations (sync, scan)

## Video Format Support

### Supported Extensions
The system supports 16+ video formats:

```json
{
  "supported_formats": [
    "mp4", "mkv", "avi", "mov", "wmv", "flv", 
    "webm", "m4v", "3gp", "ogv", "ts", "m2ts", 
    "vob", "asf", "rm", "rmvb"
  ]
}
```

### Check Format Support
```http
GET /api/video-formats
```
Returns list of supported video formats with codec information.

## Webhook Integration

### Translation Complete
When translation completes, the system can send webhooks:

```json
{
  "event": "translation_complete",
  "file_path": "/path/to/video.mp4",
  "subtitle_path": "/path/to/video.ar.srt",
  "duration": 120.5,
  "status": "success"
}
```

## Examples

### Python Example
```python
import requests

# Login session
session = requests.Session()
response = session.post('http://localhost:5000/login', {
    'username': 'admin',
    'password': 'your_password'
})

# Get system status
status = session.get('http://localhost:5000/api/status').json()
print(f"Status: {status['status']}")

# Start batch translation
result = session.post('http://localhost:5000/action/start-batch')
print(f"Translation started: {result.json()}")
```

### JavaScript Example
```javascript
// Fetch system status
fetch('/api/status')
  .then(response => response.json())
  .then(data => {
    console.log('Status:', data.status);
    console.log('Progress:', data.progress + '%');
  });

// Test media service
fetch('/api/test-media-service/plex')
  .then(response => response.json())
  .then(data => {
    console.log('Plex Status:', data.status);
  });
```

## Development
For development purposes, all API endpoints can be tested using tools like:
- Postman
- curl
- Python requests
- JavaScript fetch

## Support
For API support and questions:
- Email: Eg2@live.com
- GitHub: https://github.com/AbdelmonemAwad
- Documentation: `/docs` page in the application