// Complete JavaScript Fix for Remote Server - إصلاح شامل للخادم البعيد
console.log('🚀 Loading complete JavaScript fix for remote server...');

// Define global functions first
window.switchCategory = function() {
    console.log('switchCategory called');
    const categorySelect = document.getElementById('category-select');
    if (categorySelect) {
        categorySelect.dispatchEvent(new Event('change'));
    }
};

window.switchTab = function() {
    console.log('switchTab called');
    const subcategorySelect = document.getElementById('subcategory-select');
    if (subcategorySelect) {
        subcategorySelect.dispatchEvent(new Event('change'));
    }
};

window.saveAllSettings = function() {
    console.log('saveAllSettings called');
    const form = document.querySelector('form');
    if (form) {
        form.submit();
    } else {
        console.error('Form not found');
    }
};

// Main initialization with comprehensive tab and dropdown fixes
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Settings tabs and dropdowns fix starting...');
    
    // Category mappings for proper navigation
    const categoryMappings = {
        'general': {
            label: '🔧 عام / General',
            subcategories: {
                'DEFAULT': 'إعدادات عامة / General Settings',
                'INTERFACE': 'الواجهة / Interface',
                'LANGUAGE': 'اللغة / Language'
            }
        },
        'ai': {
            label: '🤖 الذكاء الاصطناعي / AI',
            subcategories: {
                'WHISPER': 'Whisper (التعرف على الكلام)',
                'OLLAMA': 'Ollama (الترجمة)',
                'GPU': 'إعدادات GPU / GPU Settings'
            }
        },
        'media': {
            label: '📺 خوادم الوسائط / Media Servers',
            subcategories: {
                'PLEX': 'Plex Media Server',
                'JELLYFIN': 'Jellyfin Media Server',
                'EMBY': 'Emby Media Server',
                'KODI': 'Kodi Media Center',
                'RADARR': 'Radarr (Movies)',
                'SONARR': 'Sonarr (TV Shows)'
            }
        },
        'system': {
            label: '⚙️ النظام / System',
            subcategories: {
                'PATHS': 'مسارات الملفات / File Paths',
                'REMOTE_STORAGE': 'التخزين البعيد / Remote Storage',
                'SERVER': 'إعدادات الخادم / Server Settings'
            }
        },
        'development': {
            label: '🛠️ التطوير / Development',
            subcategories: {
                'DEBUG': 'إعدادات التصحيح / Debug Settings',
                'TESTING': 'إعدادات الاختبار / Testing Settings'
            }
        }
    };
    
    // Dropdown fixes
    function fixDropdowns() {
        const categorySelect = document.getElementById('category-select');
        const subcategorySelect = document.getElementById('subcategory-select');
        
        if (categorySelect && subcategorySelect) {
            console.log('✅ Found category dropdowns, fixing...');
            
            categorySelect.addEventListener('change', function() {
                const selectedCategory = this.value;
                console.log('Category changed to:', selectedCategory);
                
                subcategorySelect.innerHTML = '';
                
                if (categoryMappings[selectedCategory] && categoryMappings[selectedCategory].subcategories) {
                    Object.entries(categoryMappings[selectedCategory].subcategories).forEach(([key, label]) => {
                        const option = document.createElement('option');
                        option.value = key.toLowerCase();
                        option.textContent = label;
                        subcategorySelect.appendChild(option);
                    });
                }
                
                subcategorySelect.dispatchEvent(new Event('change'));
            });
            
            subcategorySelect.addEventListener('change', function() {
                const selectedSubcategory = this.value.toUpperCase();
                console.log('Subcategory changed to:', selectedSubcategory);
                showTabContent(selectedSubcategory);
            });
            
            categorySelect.dispatchEvent(new Event('change'));
        }
    }
    
    // Tab content management
    function showTabContent(tabId) {
        console.log('Showing tab content for:', tabId);
        
        const allTabs = document.querySelectorAll('.tab-content');
        allTabs.forEach(tab => {
            tab.classList.add('hidden');
            tab.style.display = 'none';
        });
        
        const targetTab = document.getElementById('tab-' + tabId) || 
                         document.querySelector(`[id*="${tabId}"]`) ||
                         document.querySelector('.tab-content');
        
        if (targetTab) {
            targetTab.classList.remove('hidden');
            targetTab.style.display = 'block';
            console.log('✅ Tab shown:', tabId);
        } else {
            if (allTabs.length > 0) {
                allTabs[0].classList.remove('hidden');
                allTabs[0].style.display = 'block';
                console.log('✅ Showing first tab as fallback');
            }
        }
    }
    
    // Dropdown options fixes
    function fixAllDropdownOptions() {
        console.log('🔧 Fixing all dropdown options...');
        
        const dropdowns = document.querySelectorAll('select');
        
        dropdowns.forEach(select => {
            if (select.name && (select.name.includes('enabled') || select.name.includes('debug'))) {
                const currentValue = select.value;
                select.innerHTML = '';
                
                const yesOption = document.createElement('option');
                yesOption.value = 'true';
                yesOption.textContent = 'نعم / Yes';
                select.appendChild(yesOption);
                
                const noOption = document.createElement('option');
                noOption.value = 'false';
                noOption.textContent = 'لا / No';
                select.appendChild(noOption);
                
                select.value = currentValue;
            }
        });
        
        console.log('✅ Dropdown options fixed');
    }
    
    // Run all fixes
    function runFixes() {
        console.log('🔧 Running all fixes...');
        
        setTimeout(() => {
            fixDropdowns();
            fixAllDropdownOptions();
            
            const firstTab = document.querySelector('.tab-content');
            if (firstTab) {
                firstTab.classList.remove('hidden');
                firstTab.style.display = 'block';
            }
            
            console.log('✅ All fixes completed');
        }, 500);
    }
    
    runFixes();
    
    // DOM observer for dynamic content
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                runFixes();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    window.fixAllDropdownOptions = fixAllDropdownOptions;
});

console.log('🚀 Complete JavaScript fix loaded successfully');