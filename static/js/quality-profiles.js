/**
 * Quality Profiles Management for Radarr and Sonarr
 * إدارة ملفات الجودة لـ Radarr و Sonarr
 */

class QualityProfilesManager {
    constructor() {
        this.cache = new Map();
        this.loadTimeout = 5000; // 5 seconds timeout
    }

    /**
     * Load quality profiles for Radarr
     */
    async loadRadarrProfiles() {
        try {
            const response = await fetch('/api/radarr_quality_profiles', {
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success && data.profiles) {
                this.cache.set('radarr', data.profiles);
                this.updateRadarrDropdown(data.profiles);
                console.log('Radarr quality profiles loaded:', data.profiles.length);
                return data.profiles;
            } else {
                console.warn('Failed to load Radarr quality profiles:', data.error);
                this.showError('radarr', data.error || 'Failed to load quality profiles');
                return [];
            }
        } catch (error) {
            console.error('Error loading Radarr quality profiles:', error);
            this.showError('radarr', 'Connection error');
            return [];
        }
    }

    /**
     * Load quality profiles for Sonarr
     */
    async loadSonarrProfiles() {
        try {
            const response = await fetch('/api/sonarr_quality_profiles', {
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success && data.profiles) {
                this.cache.set('sonarr', data.profiles);
                this.updateSonarrDropdown(data.profiles);
                console.log('Sonarr quality profiles loaded:', data.profiles.length);
                return data.profiles;
            } else {
                console.warn('Failed to load Sonarr quality profiles:', data.error);
                this.showError('sonarr', data.error || 'Failed to load quality profiles');
                return [];
            }
        } catch (error) {
            console.error('Error loading Sonarr quality profiles:', error);
            this.showError('sonarr', 'Connection error');
            return [];
        }
    }

    /**
     * Update Radarr quality profile dropdown
     */
    updateRadarrDropdown(profiles) {
        const dropdown = document.getElementById('radarr_quality_profile');
        if (!dropdown) return;

        // Get current value to preserve selection
        const currentValue = dropdown.value;

        // Clear existing options
        dropdown.innerHTML = '';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'اختر ملف الجودة - Select Quality Profile';
        dropdown.appendChild(defaultOption);

        // Add profiles from server
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.name;
            
            // Restore previous selection if it exists
            if (profile.id.toString() === currentValue) {
                option.selected = true;
            }
            
            dropdown.appendChild(option);
        });

        // Enable dropdown
        dropdown.disabled = false;
        
        // Update status
        this.showSuccess('radarr', `تم تحميل ${profiles.length} ملف جودة`);
    }

    /**
     * Update Sonarr quality profile dropdown
     */
    updateSonarrDropdown(profiles) {
        const dropdown = document.getElementById('sonarr_quality_profile');
        if (!dropdown) return;

        // Get current value to preserve selection
        const currentValue = dropdown.value;

        // Clear existing options
        dropdown.innerHTML = '';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'اختر ملف الجودة - Select Quality Profile';
        dropdown.appendChild(defaultOption);

        // Add profiles from server
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.name;
            
            // Restore previous selection if it exists
            if (profile.id.toString() === currentValue) {
                option.selected = true;
            }
            
            dropdown.appendChild(option);
        });

        // Enable dropdown
        dropdown.disabled = false;
        
        // Update status
        this.showSuccess('sonarr', `تم تحميل ${profiles.length} ملف جودة`);
    }

    /**
     * Show error message
     */
    showError(service, message) {
        const statusElement = this.getStatusElement(service);
        if (statusElement) {
            statusElement.innerHTML = `<span style="color: #dc3545;"><i data-feather="alert-circle"></i> خطأ: ${message}</span>`;
            if (window.feather) feather.replace();
        }
    }

    /**
     * Show success message
     */
    showSuccess(service, message) {
        const statusElement = this.getStatusElement(service);
        if (statusElement) {
            statusElement.innerHTML = `<span style="color: #28a745;"><i data-feather="check-circle"></i> ${message}</span>`;
            if (window.feather) feather.replace();
        }
    }

    /**
     * Get status element for service
     */
    getStatusElement(service) {
        return document.getElementById(`${service}_quality_status`);
    }

    /**
     * Load all quality profiles
     */
    async loadAllProfiles() {
        console.log('Loading quality profiles for all services...');
        
        // Load both services in parallel
        const promises = [
            this.loadRadarrProfiles(),
            this.loadSonarrProfiles()
        ];

        try {
            await Promise.allSettled(promises);
            console.log('All quality profiles loading completed');
        } catch (error) {
            console.error('Error in loading quality profiles:', error);
        }
    }

    /**
     * Refresh quality profiles for a specific service
     */
    async refreshProfiles(service) {
        if (service === 'radarr') {
            return await this.loadRadarrProfiles();
        } else if (service === 'sonarr') {
            return await this.loadSonarrProfiles();
        }
    }
}

// Global instance
let qualityProfilesManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    qualityProfilesManager = new QualityProfilesManager();
    
    // Auto-load quality profiles when on media settings page
    if (window.location.pathname.includes('/settings/media')) {
        // Small delay to ensure all elements are rendered
        setTimeout(() => {
            qualityProfilesManager.loadAllProfiles();
        }, 1000);
    }
});

// Global functions for manual refresh
window.refreshRadarrProfiles = function() {
    if (qualityProfilesManager) {
        qualityProfilesManager.refreshProfiles('radarr');
    }
};

window.refreshSonarrProfiles = function() {
    if (qualityProfilesManager) {
        qualityProfilesManager.refreshProfiles('sonarr');
    }
};

// Auto-refresh when settings are updated
window.addEventListener('settingsUpdated', function() {
    if (qualityProfilesManager) {
        setTimeout(() => {
            qualityProfilesManager.loadAllProfiles();
        }, 500);
    }
});

// Function to select all quality profiles for a service
window.selectAllProfiles = function(service) {
    const selectElement = document.getElementById(`${service}_quality_profile`);
    if (selectElement && selectElement.options.length > 1) {
        // Create array of all profile values (excluding loading/error options)
        const allValues = [];
        let validOptions = 0;
        
        for (let i = 0; i < selectElement.options.length; i++) {
            const option = selectElement.options[i];
            if (option.value && option.value !== '' && !option.disabled && 
                !option.textContent.includes('جاري التحميل') && 
                !option.textContent.includes('Loading') &&
                !option.textContent.includes('اختر ملف')) {
                allValues.push(option.value);
                validOptions++;
            }
        }
        
        if (validOptions === 0) {
            const statusDiv = document.getElementById(`${service}_quality_status`);
            if (statusDiv) {
                statusDiv.innerHTML = `<span style="color: #dc3545;">⚠ لا توجد ملفات جودة متوفرة للاختيار</span>`;
            }
            return;
        }
        
        // Set the select to multiple if not already
        if (!selectElement.multiple) {
            selectElement.multiple = true;
            selectElement.size = Math.min(validOptions + 1, 8); // Show options plus some padding
            selectElement.style.height = 'auto';
        }
        
        // Select all valid options
        for (let i = 0; i < selectElement.options.length; i++) {
            const option = selectElement.options[i];
            if (option.value && option.value !== '' && !option.disabled && 
                !option.textContent.includes('جاري التحميل') && 
                !option.textContent.includes('Loading') &&
                !option.textContent.includes('اختر ملف')) {
                option.selected = true;
            }
        }
        
        // Update status with better Arabic text
        const statusDiv = document.getElementById(`${service}_quality_status`);
        if (statusDiv) {
            const serviceName = service === 'radarr' ? 'الأفلام' : 'المسلسلات';
            statusDiv.innerHTML = `<span style="color: #10b981;"><i data-feather="check-circle"></i> ✓ تم اختيار جميع ملفات الجودة لـ${serviceName} (${validOptions} ملف)</span>`;
            if (window.feather) feather.replace();
        }
        
        console.log(`Selected all ${validOptions} quality profiles for ${service}`);
    } else {
        const statusDiv = document.getElementById(`${service}_quality_status`);
        if (statusDiv) {
            statusDiv.innerHTML = `<span style="color: #dc3545;"><i data-feather="alert-circle"></i> لم يتم تحميل ملفات الجودة بعد</span>`;
            if (window.feather) feather.replace();
        }
    }
};

// Function to clear all selections
window.clearAllProfiles = function(service) {
    const selectElement = document.getElementById(`${service}_quality_profile`);
    if (selectElement) {
        // Clear all selections
        for (let i = 0; i < selectElement.options.length; i++) {
            selectElement.options[i].selected = false;
        }
        
        // Reset to single selection mode
        selectElement.multiple = false;
        selectElement.size = 1;
        selectElement.style.height = '';
        
        // Select the default option if available
        if (selectElement.options.length > 0) {
            selectElement.selectedIndex = 0;
        }
        
        // Update status with better Arabic text
        const statusDiv = document.getElementById(`${service}_quality_status`);
        if (statusDiv) {
            const serviceName = service === 'radarr' ? 'الأفلام' : 'المسلسلات';
            statusDiv.innerHTML = `<span style="color: #6c757d;"><i data-feather="minus-circle"></i> تم مسح جميع اختيارات ملفات الجودة لـ${serviceName}</span>`;
            if (window.feather) feather.replace();
        }
        
        console.log(`Cleared all selections for ${service}`);
    }
};