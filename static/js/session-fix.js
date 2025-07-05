/**
 * Session Management Fix for Replit Environment
 * Fixes session cookies issue with fetch requests
 */

// Global session token for API requests
let sessionToken = null;

// Get session token from server
async function initializeSession() {
    try {
        const response = await fetch('/api/session-token', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            sessionToken = data.token;
            console.log('Session token initialized successfully');
        }
    } catch (error) {
        console.error('Failed to initialize session:', error);
    }
}

// Enhanced fetch with session support
async function sessionFetch(url, options = {}) {
    try {
        // Try to get session token if not available
        if (!sessionToken) {
            await initializeSession();
        }
        
        // If still no token, try regular fetch with credentials
        if (!sessionToken) {
            console.warn('No session token available, using regular fetch');
            return fetch(url, {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                ...options
            });
        }
        
        // Add session token to headers
        const headers = {
            'Content-Type': 'application/json',
            'X-Session-Token': sessionToken,
            ...options.headers
        };
        
        const config = {
            credentials: 'include',
            ...options,
            headers
        };
        
        const response = await fetch(url, config);
        
        // If unauthorized, try to refresh session
        if (response.status === 401) {
            console.log('Session expired, refreshing...');
            await initializeSession();
            if (sessionToken) {
                headers['X-Session-Token'] = sessionToken;
                return fetch(url, { ...config, headers });
            }
        }
        
        return response;
    } catch (error) {
        console.error('SessionFetch error:', error);
        // Fallback to regular fetch
        return fetch(url, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            ...options
        });
    }
}

// Initialize session when page loads
document.addEventListener('DOMContentLoaded', initializeSession);

// Export for use in other scripts
window.sessionFetch = sessionFetch;
window.initializeSession = initializeSession;