// Components JavaScript

// Sidebar Management
class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.overlay = document.getElementById('sidebar-overlay');
        this.mobileMenuBtn = document.getElementById('mobile-menu-btn');
        this.mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        
        this.init();
    }
    
    init() {
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', () => this.toggleMobile());
        }
        
        if (this.mobileSidebarToggle) {
            this.mobileSidebarToggle.addEventListener('click', () => this.toggleMobile());
        }
        
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleDesktop());
        }
        
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.closeMobile());
        }
        
        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
        
        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobile();
            }
        });
    }
    
    toggleMobile() {
        if (!this.sidebar || !this.overlay) return;
        
        const isExpanded = this.sidebar.classList.contains('expanded');
        
        if (isExpanded) {
            this.closeMobile();
        } else {
            this.openMobile();
        }
    }
    
    openMobile() {
        if (!this.sidebar || !this.overlay || !this.mobileMenuBtn) return;
        
        this.sidebar.classList.add('mobile-expanded');
        this.overlay.style.display = 'block';
        this.overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Change menu icon to X
        const icon = this.mobileMenuBtn.querySelector('i');
        if (icon) {
            icon.setAttribute('data-feather', 'x');
            feather.replace();
        }
    }
    
    closeMobile() {
        if (!this.sidebar || !this.overlay || !this.mobileMenuBtn) return;
        
        this.sidebar.classList.remove('mobile-expanded');
        this.overlay.classList.remove('active');
        this.overlay.style.display = 'none';
        document.body.style.overflow = '';
        
        // Change X icon back to menu
        const icon = this.mobileMenuBtn.querySelector('i');
        if (icon) {
            icon.setAttribute('data-feather', 'menu');
            feather.replace();
        }
    }
    
    toggleDesktop() {
        if (!this.sidebar) return;
        
        const isCollapsed = this.sidebar.classList.contains('collapsed');
        
        if (isCollapsed) {
            this.sidebar.classList.remove('collapsed');
            localStorage.setItem('sidebar-collapsed', 'false');
        } else {
            this.sidebar.classList.add('collapsed');
            localStorage.setItem('sidebar-collapsed', 'true');
        }
    }
    
    handleResize() {
        const isMobile = window.innerWidth <= 768;
        
        if (!isMobile) {
            this.closeMobile();
        }
    }
    
    // Restore sidebar state
    restoreState() {
        const collapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        
        if (collapsed && this.sidebar) {
            this.sidebar.classList.add('collapsed');
        }
    }
}

// Theme Management
class ThemeManager {
    constructor() {
        this.themeButtons = document.querySelectorAll('.theme-btn');
        this.currentTheme = localStorage.getItem('theme') || 'system';
        
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        
        this.themeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const theme = btn.getAttribute('data-theme');
                this.setTheme(theme);
            });
        });
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (this.currentTheme === 'system') {
                    this.applySystemTheme();
                }
            });
        }
    }
    
    setTheme(theme) {
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
        this.applyTheme(theme);
        this.updateButtons();
        
        // Send to server
        this.updateServerTheme(theme);
    }
    
    applyTheme(theme) {
        const html = document.documentElement;
        
        if (theme === 'system') {
            this.applySystemTheme();
        } else {
            html.setAttribute('data-theme', theme);
        }
    }
    
    applySystemTheme() {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const systemTheme = prefersDark ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', systemTheme);
    }
    
    updateButtons() {
        this.themeButtons.forEach(btn => {
            const theme = btn.getAttribute('data-theme');
            btn.classList.toggle('active', theme === this.currentTheme);
        });
    }
    
    async updateServerTheme(theme) {
        try {
            await fetch('/api/user/theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ theme })
            });
        } catch (error) {
            console.log('Could not update server theme:', error);
        }
    }
}

// Language Management
class LanguageManager {
    constructor() {
        this.langButtons = document.querySelectorAll('.lang-btn');
        
        this.init();
    }
    
    init() {
        this.langButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const lang = btn.getAttribute('data-lang');
                this.setLanguage(lang);
            });
        });
    }
    
    async setLanguage(lang) {
        try {
            await fetch('/api/user/language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ language: lang })
            });
            
            // Reload page to apply language changes
            window.location.reload();
        } catch (error) {
            console.error('Could not update language:', error);
        }
    }
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    const sidebarManager = new SidebarManager();
    const themeManager = new ThemeManager();
    const languageManager = new LanguageManager();
    
    // Restore sidebar state
    sidebarManager.restoreState();
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Auto-hide mobile menu on page navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                setTimeout(() => sidebarManager.closeMobile(), 100);
            }
        });
    });
});