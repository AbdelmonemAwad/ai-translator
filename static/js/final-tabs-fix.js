// Enhanced Settings Fix - Dropdown Options and Navigation
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Enhanced settings fix loading...');
    
    // Wait for full page load
    setTimeout(initializeEnhancedSettings, 500);
    
    function initializeEnhancedSettings() {
        const categorySelect = document.getElementById('category-select');
        const subcategorySelect = document.getElementById('subcategory-select');
        
        if (!categorySelect || !subcategorySelect) {
            console.error('❌ Category or subcategory select not found');
            return;
        }
        
        console.log('✅ Found category and subcategory selects');
        
        // Fix dropdown options first
        fixAllDropdownOptions();
        
        // Initialize category and subcategory functionality
        setupCategoryDropdown();
        
        // Apply dropdown fixes immediately and repeatedly
        if (window.fixAllDropdownOptions) {
            window.fixAllDropdownOptions();
        }
        
        // Apply fixes after page load
        setTimeout(() => {
            if (window.fixAllDropdownOptions) {
                window.fixAllDropdownOptions();
                console.log('🔄 Applied dropdown fixes after 1 second');
            }
        }, 1000);
        
        // Apply fixes when settings are populated
        setTimeout(() => {
            if (window.fixAllDropdownOptions) {
                window.fixAllDropdownOptions();
                console.log('🔄 Applied dropdown fixes after 3 seconds');
            }
        }, 3000);
        
        // Mapping from UI categories to actual database sections
        const categoryMapping = {
            'general': {
                name: 'الإعدادات العامة / General Settings',
                sections: [
                    { id: 'DEFAULT', name: 'الإعدادات الأساسية / Basic Settings' },
                    { id: 'LANGUAGE', name: 'إعدادات اللغة / Language Settings' },
                    { id: 'FOOTER', name: 'إعدادات التذييل / Footer Settings' }
                ]
            },
            'ai': {
                name: 'خدمات الذكاء الاصطناعي / AI Services',
                sections: [
                    { id: 'WHISPER', name: 'إعدادات Whisper' },
                    { id: 'OLLAMA', name: 'إعدادات Ollama' },
                    { id: 'GPU', name: 'إدارة GPU / GPU Management' },
                    { id: 'API', name: 'إعدادات API / API Settings' }
                ]
            },
            'media': {
                name: 'خوادم الوسائط / Media Servers',
                sections: [
                    { id: 'PLEX', name: 'Plex Media Server' },
                    { id: 'JELLYFIN', name: 'Jellyfin Media Server' },
                    { id: 'EMBY', name: 'Emby Media Server' },
                    { id: 'KODI', name: 'Kodi Media Center' },
                    { id: 'RADARR', name: 'Radarr (أفلام / Movies)' },
                    { id: 'SONARR', name: 'Sonarr (مسلسلات / TV Shows)' }
                ]
            },
            'system': {
                name: 'إعدادات النظام / System Settings',
                sections: [
                    { id: 'PATHS', name: 'مسارات الملفات / File Paths' },
                    { id: 'REMOTE_STORAGE', name: 'التخزين البعيد / Remote Storage' },
                    { id: 'DATABASE', name: 'قاعدة البيانات / Database' },
                    { id: 'SECURITY', name: 'الأمان / Security' },
                    { id: 'SERVER', name: 'إعدادات الخادم / Server Settings' }
                ]
            },
            'development': {
                name: 'أدوات التطوير / Development Tools',
                sections: [
                    { id: 'DEBUG', name: 'أدوات التطوير / Debug Tools' },
                    { id: 'TESTING', name: 'الاختبار / Testing' },
                    { id: 'DEVELOPMENT', name: 'أدوات التطوير / Development' }
                ]
            }
        };
        
        // Find available sections in DOM
        function getAvailableSections() {
            const allTabs = document.querySelectorAll('.tab-content[id^="tab-"]');
            const available = [];
            
            allTabs.forEach(tab => {
                const id = tab.id.replace('tab-', '');
                available.push(id);
            });
            
            console.log('📋 Available sections in DOM:', available);
            return available;
        }
        
        const availableSections = getAvailableSections();
        
        // Hide all tab contents
        function hideAllTabs() {
            const allTabs = document.querySelectorAll('.tab-content, [id^="tab-"]');
            allTabs.forEach(tab => {
                tab.classList.add('hidden');
                tab.style.display = 'none';
                tab.style.visibility = 'hidden';
            });
        }
        
        // Show specific tab content
        function showTabContent(sectionId) {
            console.log('👁️ Showing content for section:', sectionId);
            
            hideAllTabs();
            
            const targetTab = document.getElementById('tab-' + sectionId);
            if (targetTab) {
                targetTab.classList.remove('hidden');
                targetTab.style.display = 'block';
                targetTab.style.visibility = 'visible';
                targetTab.style.opacity = '1';
                
                console.log('✅ Successfully showed:', sectionId);
                return true;
            } else {
                console.warn('❌ Tab not found for section:', sectionId);
                return false;
            }
        }
        
        // Populate subcategory dropdown
        function populateSubcategories(categoryKey) {
            console.log('📝 Populating subcategories for:', categoryKey);
            
            // Clear subcategory options
            subcategorySelect.innerHTML = '<option value="">اختر القسم الفرعي / Choose Subcategory</option>';
            
            const category = categoryMapping[categoryKey];
            if (!category) {
                console.warn('❌ Unknown category:', categoryKey);
                subcategorySelect.disabled = true;
                return;
            }
            
            // Filter available sections
            const availableInCategory = category.sections.filter(section => 
                availableSections.includes(section.id)
            );
            
            if (availableInCategory.length === 0) {
                console.warn('❌ No available sections for category:', categoryKey);
                subcategorySelect.disabled = true;
                return;
            }
            
            // Add options for available sections
            availableInCategory.forEach(section => {
                const option = document.createElement('option');
                option.value = section.id;
                option.textContent = section.name;
                subcategorySelect.appendChild(option);
            });
            
            subcategorySelect.disabled = false;
            
            // Auto-select first available option
            if (availableInCategory.length > 0) {
                subcategorySelect.value = availableInCategory[0].id;
                showTabContent(availableInCategory[0].id);
            }
            
            console.log('✅ Populated', availableInCategory.length, 'subcategories');
        }
        
        // Event handlers
        categorySelect.addEventListener('change', function() {
            const selectedCategory = this.value;
            console.log('📂 Category changed to:', selectedCategory);
            
            hideAllTabs();
            populateSubcategories(selectedCategory);
        });
        
        subcategorySelect.addEventListener('change', function() {
            const selectedSection = this.value;
            console.log('📄 Subcategory changed to:', selectedSection);
            
            if (selectedSection) {
                showTabContent(selectedSection);
            } else {
                hideAllTabs();
            }
        });
        
        // Legacy function compatibility
        window.switchCategory = function() {
            console.log('🔄 Legacy switchCategory called');
            categorySelect.dispatchEvent(new Event('change'));
        };
        
        window.switchTab = function() {
            console.log('🔄 Legacy switchTab called');
            subcategorySelect.dispatchEvent(new Event('change'));
        };
        
        // Initialize with first category
        if (categorySelect.value) {
            populateSubcategories(categorySelect.value);
        } else if (categorySelect.options.length > 0) {
            categorySelect.selectedIndex = 0;
            populateSubcategories(categorySelect.value);
        }
        
        console.log('✅ Final tabs fix initialized successfully');
    }
    
    // Debug and utility functions
    window.debugTabsSystem = function() {
        console.log('=== Tabs System Debug Info ===');
        
        const categorySelect = document.getElementById('category-select');
        const subcategorySelect = document.getElementById('subcategory-select');
        const allTabs = document.querySelectorAll('.tab-content[id^="tab-"]');
        
        console.log('Category Select:', categorySelect?.value || 'Not found');
        console.log('Subcategory Select:', subcategorySelect?.value || 'Not found');
        console.log('Available tabs count:', allTabs.length);
        
        allTabs.forEach((tab, index) => {
            const isVisible = tab.style.display !== 'none' && !tab.classList.contains('hidden');
            console.log(`Tab ${index + 1}: ${tab.id} - Visible: ${isVisible}`);
        });
        
        return {
            category: categorySelect?.value,
            subcategory: subcategorySelect?.value,
            tabsCount: allTabs.length,
            visibleTabs: Array.from(allTabs).filter(tab => 
                tab.style.display !== 'none' && !tab.classList.contains('hidden')
            ).map(tab => tab.id)
        };
    };
    
    window.forceShowTab = function(sectionId) {
        console.log('🎯 Force showing tab:', sectionId);
        
        // Hide all tabs
        document.querySelectorAll('.tab-content[id^="tab-"]').forEach(tab => {
            tab.classList.add('hidden');
            tab.style.display = 'none';
        });
        
        // Show target tab
        const targetTab = document.getElementById('tab-' + sectionId);
        if (targetTab) {
            targetTab.classList.remove('hidden');
            targetTab.style.display = 'block';
            targetTab.style.visibility = 'visible';
            console.log('✅ Force showed:', sectionId);
            return true;
        } else {
            console.error('❌ Tab not found:', sectionId);
            return false;
        }
    };
    
    window.refreshTabsSystem = function() {
        console.log('🔄 Refreshing entire tabs system...');
        setTimeout(() => {
            document.dispatchEvent(new Event('DOMContentLoaded'));
        }, 200);
    };
    
    // New function to fix dropdown options showing true/false
    window.fixAllDropdownOptions = function() {
        console.log('🔧 Fixing dropdown options...');
        
        // Fix boolean dropdowns showing true/false
        document.querySelectorAll('select').forEach(select => {
            const options = Array.from(select.options);
            const hasBooleanValues = options.some(opt => 
                opt.value === 'true' || opt.value === 'false' ||
                opt.textContent === 'true' || opt.textContent === 'false'
            );
            
            if (hasBooleanValues) {
                const currentValue = select.value;
                
                // Clear and rebuild options
                select.innerHTML = '';
                
                const yesOption = document.createElement('option');
                yesOption.value = 'true';
                yesOption.textContent = 'نعم / Yes';
                if (currentValue === 'true') yesOption.selected = true;
                
                const noOption = document.createElement('option');
                noOption.value = 'false';
                noOption.textContent = 'لا / No';
                if (currentValue === 'false') noOption.selected = true;
                
                select.appendChild(yesOption);
                select.appendChild(noOption);
                
                // Restore value
                select.value = currentValue;
                
                console.log('✅ Fixed boolean dropdown:', select.name || select.id);
            }
        });
        
        // Fix language dropdowns
        document.querySelectorAll('select[name*="language"], select[id*="language"]').forEach(select => {
            const currentValue = select.value;
            
            select.innerHTML = '';
            
            const enOption = document.createElement('option');
            enOption.value = 'en';
            enOption.textContent = 'الإنجليزية / English';
            if (currentValue === 'en') enOption.selected = true;
            
            const arOption = document.createElement('option');
            arOption.value = 'ar';
            arOption.textContent = 'العربية / Arabic';
            if (currentValue === 'ar') arOption.selected = true;
            
            select.appendChild(enOption);
            select.appendChild(arOption);
            
            select.value = currentValue;
            
            console.log('✅ Fixed language dropdown:', select.name || select.id);
        });
        
        // Fix theme dropdowns
        document.querySelectorAll('select[name*="theme"], select[id*="theme"]').forEach(select => {
            const currentValue = select.value;
            
            select.innerHTML = '';
            
            const lightOption = document.createElement('option');
            lightOption.value = 'light';
            lightOption.textContent = 'فاتح / Light';
            if (currentValue === 'light') lightOption.selected = true;
            
            const darkOption = document.createElement('option');
            darkOption.value = 'dark';
            darkOption.textContent = 'داكن / Dark';
            if (currentValue === 'dark') darkOption.selected = true;
            
            const systemOption = document.createElement('option');
            systemOption.value = 'system';
            systemOption.textContent = 'النظام / System';
            if (currentValue === 'system') systemOption.selected = true;
            
            select.appendChild(lightOption);
            select.appendChild(darkOption);
            select.appendChild(systemOption);
            
            select.value = currentValue;
            
            console.log('✅ Fixed theme dropdown:', select.name || select.id);
        });
        
        console.log('✅ All dropdown options fixed');
    };
    
    // Create a mutation observer to watch for dynamically added content
    const observer = new MutationObserver(function(mutations) {
        let shouldFix = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'SELECT' || node.querySelector && node.querySelector('select')) {
                            shouldFix = true;
                        }
                    }
                });
            }
        });
        
        if (shouldFix && window.fixAllDropdownOptions) {
            setTimeout(() => {
                window.fixAllDropdownOptions();
                console.log('🔄 Applied dropdown fixes after DOM change');
            }, 100);
        }
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Also fix dropdowns when tab content changes
    window.addEventListener('tab-changed', function() {
        setTimeout(() => {
            if (window.fixAllDropdownOptions) {
                window.fixAllDropdownOptions();
                console.log('🔄 Applied dropdown fixes after tab change');
            }
        }, 200);
    });
});