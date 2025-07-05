document.addEventListener('DOMContentLoaded', function() {
    console.log('Tabs fix loading...');
    
    // Fix main navigation tabs
    function fixMainTabs() {
        const mainNavLinks = document.querySelectorAll('.sidebar a, .nav-link, .main-nav a, [data-tab]');
        
        mainNavLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Remove active class from all main nav links
                mainNavLinks.forEach(nav => nav.classList.remove('active'));
                
                // Add active class to clicked link
                this.classList.add('active');
                
                console.log('Main tab clicked:', this.textContent.trim());
            });
        });
    }
    
    // Fix sub tabs within pages
    function fixSubTabs() {
        const tabTriggers = document.querySelectorAll('[data-bs-toggle="tab"], [data-toggle="tab"], .nav-tabs .nav-link, .tab-button');
        
        tabTriggers.forEach(trigger => {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                
                const target = this.getAttribute('href') || this.getAttribute('data-bs-target') || this.getAttribute('data-target');
                
                if (target) {
                    // Remove active from all tabs in this group
                    const tabGroup = this.closest('.nav-tabs, .tab-nav, .tabs-container');
                    if (tabGroup) {
                        const groupTabs = tabGroup.querySelectorAll('.nav-link, .tab-item, .tab-button');
                        groupTabs.forEach(tab => tab.classList.remove('active'));
                        
                        // Hide all tab panes
                        const tabPanes = document.querySelectorAll('.tab-pane, .tab-content');
                        tabPanes.forEach(pane => {
                            pane.classList.remove('active', 'show');
                            pane.style.display = 'none';
                        });
                    }
                    
                    // Activate clicked tab
                    this.classList.add('active');
                    
                    // Show target pane
                    const targetPane = document.querySelector(target);
                    if (targetPane) {
                        targetPane.classList.add('active', 'show');
                        targetPane.style.display = 'block';
                    }
                    
                    console.log('Sub tab activated:', target);
                }
            });
        });
    }
    
    // Fix settings category/subcategory dropdowns
    function fixSettingsDropdowns() {
        const categorySelect = document.getElementById('category');
        const subcategorySelect = document.getElementById('subcategory');
        
        if (categorySelect && subcategorySelect) {
            categorySelect.addEventListener('change', function() {
                const category = this.value;
                console.log('Category changed to:', category);
                
                // Clear subcategory options
                subcategorySelect.innerHTML = '<option value="">اختر القسم الفرعي</option>';
                
                const subcategories = {
                    'general': [
                        { value: 'interface', label: 'الواجهة' },
                        { value: 'language', label: 'اللغة' }
                    ],
                    'ai_services': [
                        { value: 'whisper', label: 'Whisper' },
                        { value: 'ollama', label: 'Ollama' },
                        { value: 'gpu', label: 'GPU' }
                    ],
                    'media_servers': [
                        { value: 'plex', label: 'Plex' },
                        { value: 'jellyfin', label: 'Jellyfin' },
                        { value: 'emby', label: 'Emby' },
                        { value: 'radarr', label: 'Radarr' },
                        { value: 'sonarr', label: 'Sonarr' }
                    ],
                    'system': [
                        { value: 'paths', label: 'المسارات' },
                        { value: 'remote_storage', label: 'التخزين البعيد' },
                        { value: 'database', label: 'قاعدة البيانات' }
                    ]
                };
                
                if (subcategories[category]) {
                    subcategories[category].forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.value;
                        option.textContent = sub.label;
                        subcategorySelect.appendChild(option);
                    });
                    subcategorySelect.disabled = false;
                } else {
                    subcategorySelect.disabled = true;
                }
            });
            
            // Trigger change if category is already selected
            if (categorySelect.value) {
                categorySelect.dispatchEvent(new Event('change'));
            }
        }
    }
    
    // Initialize all fixes
    setTimeout(() => {
        fixMainTabs();
        fixSubTabs();
        fixSettingsDropdowns();
        console.log('All tabs fixes applied');
    }, 500);
    
    // Re-initialize when new content is loaded
    const observer = new MutationObserver(function(mutations) {
        let shouldRefresh = false;
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                for (let node of mutation.addedNodes) {
                    if (node.nodeType === 1 && (
                        node.classList?.contains('tab-pane') ||
                        node.querySelector?.('.nav-tabs, .tab-button')
                    )) {
                        shouldRefresh = true;
                        break;
                    }
                }
            }
        });
        
        if (shouldRefresh) {
            setTimeout(() => {
                fixSubTabs();
            }, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Global refresh function
window.refreshTabs = function() {
    setTimeout(() => {
        document.dispatchEvent(new Event('DOMContentLoaded'));
    }, 100);
};