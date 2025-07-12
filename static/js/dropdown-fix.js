/**
 * Instant Dropdown Fix for AI Translator Settings
 * إصلاح فوري للقوائم المنسدلة في إعدادات الترجمان الآلي
 */

(function() {
    'use strict';
    
    console.log('🔧 Loading dropdown fix...');
    
    // Enhanced translation mappings for options
    const translations = {
        'true': 'نعم / Yes',
        'false': 'لا / No',
        'en': 'الإنجليزية / English',
        'ar': 'العربية / Arabic',
        'dark': 'داكن / Dark',
        'light': 'فاتح / Light',
        'system': 'النظام / System',
        'enabled': 'مفعل / Enabled',
        'disabled': 'معطل / Disabled',
        'auto': 'تلقائي / Auto',
        'cpu': 'المعالج فقط / CPU Only',
        'auto_select': 'اختيار تلقائي / Auto Select',
        'cpu_only': 'المعالج فقط / CPU Only',
        'gpu_0': 'كارت الشاشة 0 / GPU 0',
        'gpu_1': 'كارت الشاشة 1 / GPU 1',
        'gpu_2': 'كارت الشاشة 2 / GPU 2',
        // Categories
        'general_category': 'الإعدادات العامة',
        'ai_category': 'خدمات الذكاء الاصطناعي',
        'media_category': 'خوادم الوسائط',
        'storage_category': 'إدارة التخزين',
        'system_category': 'إدارة النظام',
        'development_category': 'أدوات التطوير'
    };
    
    function fixDropdowns() {
        console.log('🔄 Fixing all dropdowns...');
        let fixedCount = 0;
        
        // Find all select elements
        const selects = document.querySelectorAll('select');
        console.log(`🔍 Found ${selects.length} select elements total`);
        
        selects.forEach((select, index) => {
            const currentValue = select.value;
            const selectName = select.name || select.id || `select-${index}`;
            let needsFix = false;
            
            console.log(`🔍 Checking select "${selectName}" with ${select.options.length} options`);
            
            // Log all options for debugging
            Array.from(select.options).forEach((option, optIndex) => {
                const text = option.textContent.trim();
                const value = option.value.trim();
                console.log(`  Option ${optIndex}: text="${text}", value="${value}"`);
            });
            
            // Check if any option shows raw values or needs translation
            Array.from(select.options).forEach(option => {
                const text = option.textContent.trim();
                const value = option.value.trim();
                
                // Comprehensive detection for all dropdown types
                if (text === 'true' || text === 'false' || 
                    text === 'en' || text === 'ar' ||
                    text === 'dark' || text === 'light' || text === 'system' ||
                    text === 'enabled' || text === 'disabled' ||
                    text === 'auto' || text === 'cpu' ||
                    text === 'auto_select' || text === 'cpu_only' ||
                    text.includes('_category') || text.includes('_select') ||
                    // Check if text matches value exactly (indicating raw value display)
                    (text === value && translations[value]) ||
                    // Check for common patterns that need translation
                    /^[a-z_]+$/.test(text) && translations[text]) {
                    needsFix = true;
                    console.log(`🔍 Found option needing fix: "${text}" (value: "${value}") in select "${selectName}"`);
                }
            });
            
            if (needsFix) {
                const options = Array.from(select.options).map(opt => ({
                    value: opt.value,
                    text: opt.textContent,
                    selected: opt.selected
                }));
                
                // Clear and rebuild
                select.innerHTML = '';
                
                options.forEach(opt => {
                    const newOption = document.createElement('option');
                    newOption.value = opt.value;
                    newOption.textContent = translations[opt.value] || opt.text;
                    
                    if (opt.value === currentValue) {
                        newOption.selected = true;
                    }
                    
                    select.appendChild(newOption);
                });
                
                // Restore original value
                select.value = currentValue;
                
                fixedCount++;
                console.log(`✅ Fixed dropdown: ${select.name || select.id || 'unnamed'}`);
            }
        });
        
        if (fixedCount > 0) {
            console.log(`✅ Fixed ${fixedCount} dropdowns total`);
        } else {
            console.log('ℹ️ No dropdowns needed fixing');
        }
    }
    
    // Run immediately when script loads
    fixDropdowns();
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixDropdowns);
    } else {
        setTimeout(fixDropdowns, 100);
    }
    
    // Run periodically to catch dynamically loaded content (disabled for debugging)
    // setInterval(fixDropdowns, 2000);
    
    // Run when page becomes visible (tab switching)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            setTimeout(fixDropdowns, 300);
        }
    });
    
    // Expose global function for manual triggering
    window.fixDropdowns = fixDropdowns;
    
    console.log('✅ Dropdown fix system initialized');
})();