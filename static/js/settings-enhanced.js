/**
 * Enhanced Settings Interface - Fixed Dropdowns and Navigation
 * واجهة الإعدادات المحسنة - إصلاح القوائم والتنقل
 */

class SettingsManager {
    constructor() {
        this.currentLanguage = 'en';
        this.currentCategory = 'general';
        this.currentSection = 'AUTH';
        this.initialized = false;
        
        this.init();
    }
    
    init() {
        if (this.initialized) return;
        
        console.log('🔧 Initializing Enhanced Settings Manager...');
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        this.detectLanguage();
        this.setupCategoryMapping();
        this.setupEventListeners();
        this.fixDropdownOptions();
        this.initializeNavigation();
        
        this.initialized = true;
        console.log('✅ Settings Manager initialized successfully');
    }
    
    detectLanguage() {
        // Detect current language from session or HTML
        const htmlLang = document.documentElement.lang;
        const sessionLang = sessionStorage.getItem('language');
        this.currentLanguage = sessionLang || htmlLang || 'en';
        
        console.log(`🌍 Detected language: ${this.currentLanguage}`);
    }
    
    setupCategoryMapping() {
        this.categoryMapping = {
            'general': {
                name: { en: 'General Settings', ar: 'الإعدادات العامة' },
                sections: [
                    { id: 'AUTH', name: { en: 'Authentication', ar: 'المصادقة' } },
                    { id: 'UI', name: { en: 'User Interface', ar: 'واجهة المستخدم' } }
                ]
            },
            'ai': {
                name: { en: 'AI Services', ar: 'خدمات الذكاء الاصطناعي' },
                sections: [
                    { id: 'WHISPER', name: { en: 'Whisper Settings', ar: 'إعدادات Whisper' } },
                    { id: 'OLLAMA', name: { en: 'Ollama Settings', ar: 'إعدادات Ollama' } }
                ]
            },
            'media': {
                name: { en: 'Media Servers', ar: 'خوادم الوسائط' },
                sections: [
                    { id: 'PLEX', name: { en: 'Plex Media Server', ar: 'خادم Plex للوسائط' } },
                    { id: 'JELLYFIN', name: { en: 'Jellyfin Media Server', ar: 'خادم Jellyfin للوسائط' } },
                    { id: 'RADARR', name: { en: 'Radarr (Movies)', ar: 'Radarr (أفلام)' } },
                    { id: 'SONARR', name: { en: 'Sonarr (TV Shows)', ar: 'Sonarr (مسلسلات)' } }
                ]
            },
            'system': {
                name: { en: 'System Settings', ar: 'إعدادات النظام' },
                sections: [
                    { id: 'PATHS', name: { en: 'File Paths', ar: 'مسارات الملفات' } },
                    { id: 'PROCESSING', name: { en: 'Processing', ar: 'المعالجة' } },
                    { id: 'SERVER', name: { en: 'Server Configuration', ar: 'تكوين الخادم' } }
                ]
            },
            'development': {
                name: { en: 'Development Tools', ar: 'أدوات التطوير' },
                sections: [
                    { id: 'DEVELOPMENT', name: { en: 'Development Settings', ar: 'إعدادات التطوير' } }
                ]
            }
        };
    }
    
    setupEventListeners() {
        const categorySelect = document.getElementById('category-select');
        const subcategorySelect = document.getElementById('subcategory-select');
        
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.switchCategory(e.target.value);
            });
        }
        
        if (subcategorySelect) {
            subcategorySelect.addEventListener('change', (e) => {
                this.switchSection(e.target.value);
            });
        }
    }
    
    switchCategory(category) {
        this.currentCategory = category;
        console.log(`📂 Switching to category: ${category}`);
        
        this.updateSubcategoryOptions();
        
        // Auto-select first subcategory
        const sections = this.categoryMapping[category]?.sections || [];
        if (sections.length > 0) {
            this.switchSection(sections[0].id);
        }
    }
    
    updateSubcategoryOptions() {
        const subcategorySelect = document.getElementById('subcategory-select');
        if (!subcategorySelect) return;
        
        const sections = this.categoryMapping[this.currentCategory]?.sections || [];
        
        // Clear existing options
        subcategorySelect.innerHTML = '';
        
        // Add new options
        sections.forEach(section => {
            const option = document.createElement('option');
            option.value = section.id;
            option.textContent = section.name[this.currentLanguage] || section.name.en;
            subcategorySelect.appendChild(option);
        });
        
        console.log(`📝 Updated subcategory options for ${this.currentCategory}: ${sections.length} sections`);
    }
    
    switchSection(sectionId) {
        this.currentSection = sectionId;
        console.log(`📄 Switching to section: ${sectionId}`);
        
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.add('hidden');
        });
        
        // Show selected tab
        const targetTab = document.getElementById(`tab-${sectionId}`);
        if (targetTab) {
            targetTab.classList.remove('hidden');
            console.log(`✅ Showed tab: tab-${sectionId}`);
        } else {
            console.warn(`⚠️ Tab not found: tab-${sectionId}`);
        }
        
        // Update subcategory select value
        const subcategorySelect = document.getElementById('subcategory-select');
        if (subcategorySelect && subcategorySelect.value !== sectionId) {
            subcategorySelect.value = sectionId;
        }
    }
    
    fixDropdownOptions() {
        console.log('🔧 Fixing dropdown options...');
        
        // Fix all select elements with options
        document.querySelectorAll('select[data-options], select').forEach(select => {
            this.fixSelectOptions(select);
        });
        
        // Fix boolean selects specifically
        this.fixBooleanSelects();
        
        console.log('✅ Dropdown options fixed');
    }
    
    fixSelectOptions(select) {
        if (!select.dataset.options && !select.getAttribute('data-type')) return;
        
        const options = select.dataset.options;
        const dataType = select.getAttribute('data-type');
        
        // Handle boolean selects
        if (dataType === 'boolean' || this.isBooleanSelect(select)) {
            this.fixBooleanSelect(select);
            return;
        }
        
        // Handle options string
        if (options) {
            try {
                this.parseAndSetOptions(select, options);
            } catch (e) {
                console.warn('Error parsing options for select:', select, e);
            }
        }
    }
    
    isBooleanSelect(select) {
        const options = Array.from(select.options);
        return options.some(opt => 
            opt.value === 'true' || opt.value === 'false' ||
            opt.textContent === 'true' || opt.textContent === 'false'
        );
    }
    
    fixBooleanSelect(select) {
        const currentValue = select.value;
        
        // Clear and rebuild options
        select.innerHTML = '';
        
        // Add proper boolean options
        const yesOption = document.createElement('option');
        yesOption.value = 'true';
        yesOption.textContent = this.currentLanguage === 'ar' ? 'نعم' : 'Yes';
        
        const noOption = document.createElement('option');
        noOption.value = 'false';
        noOption.textContent = this.currentLanguage === 'ar' ? 'لا' : 'No';
        
        select.appendChild(yesOption);
        select.appendChild(noOption);
        
        // Restore value
        select.value = currentValue;
        
        console.log(`🔧 Fixed boolean select: ${select.name || select.id}`);
    }
    
    fixBooleanSelects() {
        document.querySelectorAll('select').forEach(select => {
            if (this.isBooleanSelect(select)) {
                this.fixBooleanSelect(select);
            }
        });
    }
    
    parseAndSetOptions(select, optionsString) {
        const currentValue = select.value;
        
        // Parse options string (format: "value:label|value2:label2")
        const optionPairs = optionsString.split('|');
        
        // Clear existing options
        select.innerHTML = '';
        
        optionPairs.forEach(pair => {
            const [value, label] = pair.split(':');
            if (value && label) {
                const option = document.createElement('option');
                option.value = value.trim();
                option.textContent = label.trim();
                select.appendChild(option);
            }
        });
        
        // Restore value
        select.value = currentValue;
    }
    
    initializeNavigation() {
        // Set initial category and section
        const categorySelect = document.getElementById('category-select');
        if (categorySelect) {
            this.switchCategory(categorySelect.value || 'general');
        }
        
        // Initialize GPU options
        this.loadGPUOptions();
    }
    
    async loadGPUOptions() {
        try {
            const response = await fetch('/api/gpu-status');
            if (response.ok) {
                const data = await response.json();
                this.updateGPUSelects(data.gpu_options || []);
            }
        } catch (e) {
            console.warn('Could not load GPU options:', e);
            this.setDefaultGPUOptions();
        }
    }
    
    updateGPUSelects(gpuOptions) {
        document.querySelectorAll('select[name*="gpu"], select[id*="gpu"]').forEach(select => {
            const currentValue = select.value;
            
            // Clear existing options
            select.innerHTML = '';
            
            // Add GPU options
            gpuOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.value;
                optionElement.textContent = this.currentLanguage === 'ar' 
                    ? (option.label_ar || option.label) 
                    : option.label;
                select.appendChild(optionElement);
            });
            
            // Restore value
            select.value = currentValue;
        });
        
        console.log(`🎮 Updated GPU selects with ${gpuOptions.length} options`);
    }
    
    setDefaultGPUOptions() {
        const defaultOptions = [
            { value: 'auto', label: 'Auto', label_ar: 'تلقائي' },
            { value: 'cpu', label: 'CPU Only', label_ar: 'المعالج فقط' }
        ];
        
        this.updateGPUSelects(defaultOptions);
    }
    
    saveAllSettings() {
        console.log('💾 Saving all settings...');
        
        const form = document.querySelector('form');
        if (form) {
            // Show loading state
            const saveButton = document.querySelector('[onclick="saveAllSettings()"]');
            if (saveButton) {
                const originalText = saveButton.textContent;
                saveButton.disabled = true;
                saveButton.textContent = this.currentLanguage === 'ar' ? 'جاري الحفظ...' : 'Saving...';
                
                // Submit form
                form.submit();
                
                // Restore button after delay
                setTimeout(() => {
                    saveButton.disabled = false;
                    saveButton.textContent = originalText;
                }, 2000);
            }
        }
    }
    
    refreshSettings() {
        console.log('🔄 Refreshing settings...');
        
        this.fixDropdownOptions();
        this.loadGPUOptions();
        
        // Re-initialize navigation
        this.initializeNavigation();
    }
}

// Initialize settings manager when DOM is ready
let settingsManager;

function initializeSettingsManager() {
    if (!settingsManager) {
        settingsManager = new SettingsManager();
    }
    return settingsManager;
}

// Global functions for template compatibility
function switchCategory() {
    const categorySelect = document.getElementById('category-select');
    if (categorySelect && settingsManager) {
        settingsManager.switchCategory(categorySelect.value);
    }
}

function switchTab() {
    const subcategorySelect = document.getElementById('subcategory-select');
    if (subcategorySelect && settingsManager) {
        settingsManager.switchSection(subcategorySelect.value);
    }
}

function saveAllSettings() {
    if (settingsManager) {
        settingsManager.saveAllSettings();
    }
}

function refreshSettingsDropdowns() {
    if (settingsManager) {
        settingsManager.refreshSettings();
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure all elements are loaded
    setTimeout(() => {
        initializeSettingsManager();
    }, 100);
});

// Re-initialize on dynamic content changes
const observer = new MutationObserver(function(mutations) {
    let shouldReinit = false;
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            const hasSelects = Array.from(mutation.addedNodes).some(node => 
                node.nodeType === 1 && (
                    node.tagName === 'SELECT' || 
                    node.querySelector && node.querySelector('select')
                )
            );
            if (hasSelects) shouldReinit = true;
        }
    });
    
    if (shouldReinit && settingsManager) {
        setTimeout(() => settingsManager.refreshSettings(), 100);
    }
});

// Start observing
observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log('📚 Enhanced Settings JavaScript loaded successfully');