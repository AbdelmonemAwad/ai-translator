/**
 * Debug script for dropdowns - الكشف عن مشاكل القوائم المنسدلة
 */

console.log('🔍 Starting dropdown debug...');

// Wait for page to load completely
setTimeout(() => {
    console.log('=== DROPDOWN DEBUG REPORT ===');
    
    // Find all select elements
    const allSelects = document.querySelectorAll('select');
    console.log(`Total select elements found: ${allSelects.length}`);
    
    if (allSelects.length === 0) {
        console.log('❌ No select elements found on this page!');
        
        // Check for elements that might be dynamically generated
        const allInputs = document.querySelectorAll('input');
        const allDivs = document.querySelectorAll('div[class*="select"], div[class*="dropdown"]');
        
        console.log(`Other form elements: ${allInputs.length} inputs, ${allDivs.length} dropdown divs`);
        
        return;
    }
    
    allSelects.forEach((select, index) => {
        const name = select.name || select.id || `unnamed-${index}`;
        const options = Array.from(select.options);
        
        console.log(`\n--- SELECT #${index}: ${name} ---`);
        console.log(`Current value: "${select.value}"`);
        console.log(`Options count: ${options.length}`);
        
        options.forEach((option, optIndex) => {
            const text = option.textContent.trim();
            const value = option.value.trim();
            const selected = option.selected ? ' [SELECTED]' : '';
            
            console.log(`  ${optIndex}: "${text}" = "${value}"${selected}`);
            
            // Check if this option needs fixing
            if (text === 'true' || text === 'false' || 
                text === 'en' || text === 'ar' ||
                text === 'enabled' || text === 'disabled') {
                console.log(`    ⚠️  NEEDS FIXING: Raw value shown as text`);
            }
        });
    });
    
    console.log('\n=== END DEBUG REPORT ===');
    
}, 2000);

// Also expose a manual debug function
window.debugDropdowns = function() {
    const selects = document.querySelectorAll('select');
    console.log('=== MANUAL DEBUG ===');
    console.log(`Found ${selects.length} selects`);
    
    selects.forEach((select, i) => {
        console.log(`Select ${i}:`, select);
        console.log(`  Name/ID: ${select.name || select.id}`);
        console.log(`  Options:`, Array.from(select.options).map(opt => ({ text: opt.textContent, value: opt.value })));
    });
};