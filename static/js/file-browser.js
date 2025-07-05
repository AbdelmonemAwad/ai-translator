/**
 * Enhanced File Browser System
 * Standalone JavaScript module for browsing folders
 */

class FileBrowser {
    constructor() {
        this.currentTargetInput = null;
        this.currentBrowserPath = '/';
        this.modalId = 'fileBrowserModal';
        this.init();
    }

    init() {
        // Create modal if it doesn't exist
        this.createModal();

        // Bind events
        this.bindEvents();

        console.log('File Browser initialized');
    }

    createModal() {
        // Check if modal already exists
        if (document.getElementById(this.modalId)) {
            console.log('Modal already exists');
            return;
        }

        const modalHTML = `
        <div id="${this.modalId}" class="file-browser-modal" style="display: none;">
            <div class="modal-backdrop"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h3><i class="feather-folder"></i> تصفح المجلدات</h3>
                    <button type="button" class="modal-close" onclick="fileBrowser.close()">
                        <i class="feather-x"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="browser-navigation">
                        <input type="text" id="currentBrowserPath" readonly class="path-display">
                        <button type="button" onclick="fileBrowser.navigateUp()" class="nav-button" title="المجلد الأعلى">
                            <i class="feather-arrow-up"></i>
                        </button>
                        <button type="button" onclick="fileBrowser.refresh()" class="nav-button" title="تحديث">
                            <i class="feather-refresh-cw"></i>
                        </button>
                    </div>
                    <div class="browser-content" id="folderList">
                        <div class="loading-state">جاري التحميل...</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="fileBrowser.close()">إلغاء</button>
                    <button type="button" class="btn btn-primary" onclick="fileBrowser.selectPath()">اختيار</button>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add CSS
        this.addStyles();

        console.log('Modal created successfully');
    }

    addStyles() {
        const css = `
        .file-browser-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
        }

        .modal-container {
            position: relative;
            background: var(--bg-primary, #1a1a2e);
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color, #2a2a4a);
            display: flex;
            flex-direction: column;
        }

        .modal-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color, #2a2a4a);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(135deg, var(--accent-primary, #4c9aff), var(--accent-secondary, #8c52ff));
            color: white;
            border-radius: 12px 12px 0 0;
        }

        .modal-header h3 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .modal-close {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .modal-close:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .modal-body {
            padding: 20px;
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .browser-navigation {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }

        .path-display {
            flex: 1;
            padding: 10px 12px;
            border: 1px solid var(--border-color, #2a2a4a);
            border-radius: 6px;
            background: var(--bg-secondary, #16213e);
            color: var(--text-primary, #e0e0e0);
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }

        .nav-button {
            padding: 10px 12px;
            background: var(--accent-primary, #4c9aff);
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .nav-button:hover {
            background: var(--accent-blue, #1976d2);
            transform: translateY(-1px);
        }

        .browser-content {
            flex: 1;
            overflow-y: auto;
            border: 1px solid var(--border-color, #2a2a4a);
            border-radius: 6px;
            background: var(--bg-secondary, #16213e);
            min-height: 300px;
        }

        .loading-state {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--text-secondary, #9e9e9e);
            font-style: italic;
        }

        .folder-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            border-bottom: 1px solid var(--border-color, #2a2a4a);
        }

        .folder-item:hover {
            background: var(--accent-primary, #4c9aff);
            color: white;
        }

        .folder-item i {
            margin-right: 10px;
            color: var(--accent-blue, #1976d2);
            font-size: 16px;
        }

        .folder-item:hover i {
            color: white;
        }

        .folder-name {
            flex: 1;
            font-size: 14px;
        }

        .modal-footer {
            padding: 20px;
            border-top: 1px solid var(--border-color, #2a2a4a);
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
        }

        .btn-primary {
            background: var(--accent-primary, #4c9aff);
            color: white;
        }

        .btn-primary:hover {
            background: var(--accent-blue, #1976d2);
        }

        .btn-secondary {
            background: var(--bg-tertiary, #2a2a4a);
            color: var(--text-primary, #e0e0e0);
        }

        .btn-secondary:hover {
            background: var(--text-secondary, #9e9e9e);
        }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = css;
        document.head.appendChild(styleSheet);
    }

    bindEvents() {
        // Close modal when clicking backdrop
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.close();
            }
        });

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) {
                this.close();
            }
        });
    }

    open(targetInputId) {
        console.log('Opening file browser for:', targetInputId);

        this.currentTargetInput = targetInputId;
        const inputElement = document.getElementById(targetInputId);
        this.currentBrowserPath = inputElement ? inputElement.value || '/' : '/';

        const modal = document.getElementById(this.modalId);
        if (!modal) {
            console.error('File browser modal not found');
            return;
        }

        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        this.loadFolders(this.currentBrowserPath);
    }

    close() {
        const modal = document.getElementById(this.modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
        this.currentTargetInput = null;
    }

    isOpen() {
        const modal = document.getElementById(this.modalId);
        return modal && modal.style.display !== 'none';
    }

    async loadFolders(path) {
        const pathDisplay = document.getElementById('currentBrowserPath');
        const folderList = document.getElementById('folderList');

        if (pathDisplay) {
            pathDisplay.value = path;
        }

        if (folderList) {
            folderList.innerHTML = '<div class="loading-state">جاري التحميل...</div>';
        }

        try {
            const response = await fetch('/api/browse-folders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    path: path
                })
            });
            const data = await response.json();

            if (data.success && data.folders) {
                this.displayFolders(data.folders);
            } else {
                folderList.innerHTML = '<div class="loading-state">خطأ في تحميل المجلدات</div>';
            }
        } catch (error) {
            console.error('Error loading folders:', error);
            folderList.innerHTML = '<div class="loading-state">خطأ في الاتصال</div>';
        }
    }

    displayFolders(folders) {
        const folderList = document.getElementById('folderList');
        if (!folderList) return;

        folderList.innerHTML = '';

        if (folders.length === 0) {
            folderList.innerHTML = '<div class="loading-state">لا توجد مجلدات</div>';
            return;
        }

        folders.forEach(folder => {
            const item = document.createElement('div');
            item.className = 'folder-item';
            item.innerHTML = `
                <i class="feather-folder"></i>
                <span class="folder-name">${this.escapeHtml(folder.name)}</span>
            `;
            item.addEventListener('click', () => this.navigateToFolder(folder.path));
            folderList.appendChild(item);
        });

        // Initialize feather icons
        this.initFeatherIcons();
    }

    navigateToFolder(path) {
        this.currentBrowserPath = path;
        this.loadFolders(path);
    }

    navigateUp() {
        const parentPath = this.currentBrowserPath.split('/').slice(0, -1).join('/') || '/';
        this.currentBrowserPath = parentPath;
        this.loadFolders(parentPath);
    }

    refresh() {
        this.loadFolders(this.currentBrowserPath);
    }

    selectPath() {
        if (this.currentTargetInput && this.currentBrowserPath) {
            const inputElement = document.getElementById(this.currentTargetInput);
            if (inputElement) {
                inputElement.value = this.currentBrowserPath;
                inputElement.dispatchEvent(new Event('change'));
            }
        }
        this.close();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    initFeatherIcons() {
        // Replace feather icons with Unicode symbols if feather.js is not available
        if (typeof feather === 'undefined') {
            const icons = document.querySelectorAll('.feather-folder');
            icons.forEach(icon => {
                icon.textContent = '📁';
                icon.style.fontSize = '16px';
            });
        } else {
            feather.replace();
        }
    }
}

// Initialize global file browser instance
let fileBrowser;

// Wait for DOM to load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        fileBrowser = new FileBrowser();
    });
} else {
    fileBrowser = new FileBrowser();
}

// Global function for compatibility
function openFileBrowser(targetInputId) {
    if (fileBrowser) {
        fileBrowser.open(targetInputId);
    } else {
        console.error('File browser not initialized');
    }
}