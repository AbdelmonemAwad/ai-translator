// GPU Management Functions for AI Translator
console.log('GPU Management JS loaded');

// Fallback notification function if not available globally
function showNotification(message, type) {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
        // Simple fallback notification
        alert(message);
    }
}

// Global GPU management functions
function refreshGPUOptions() {
    console.log('Refreshing GPU options...');
    console.log('sessionFetch function available?', typeof sessionFetch);
    showNotification('جاري تحديث خيارات كروت الشاشة...', 'info');
    
    if (typeof sessionFetch === 'undefined') {
        console.error('sessionFetch not available, using regular fetch');
        fetch('/api/gpu-refresh', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('GPU refresh response:', data);
            showNotification(data.message || 'تم تحديث كروت الشاشة بنجاح', 'success');
        })
        .catch(error => {
            console.error('Error refreshing GPU options:', error);
            showNotification('خطأ في تحديث كروت الشاشة', 'error');
        });
        return;
    }
    
    sessionFetch('/api/gpu-refresh', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('GPU refresh response:', data);
        if (data.success) {
            showNotification('تم تحديث خيارات كروت الشاشة بنجاح', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification(data.message || 'تحديث كروت الشاشة مكتمل', 'info');
        }
    })
    .catch(error => {
        console.error('Error refreshing GPU options:', error);
        showNotification('خطأ في تحديث خيارات كروت الشاشة', 'error');
    });
}

function smartGPUAllocation() {
    console.log('Running smart GPU allocation...');
    console.log('sessionFetch function available?', typeof sessionFetch);
    showNotification('جاري تطبيق التوزيع الذكي لكروت الشاشة...', 'info');
    
    if (typeof sessionFetch === 'undefined') {
        console.error('sessionFetch not available, using regular fetch');
        fetch('/api/gpu-optimize', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Smart allocation response:', data);
            showNotification(data.message || 'تم تطبيق التوزيع الذكي بنجاح', 'success');
        })
        .catch(error => {
            console.error('Error in smart allocation:', error);
            showNotification('خطأ في التوزيع الذكي', 'error');
        });
        return;
    }
    
    sessionFetch('/api/gpu-optimize', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Smart allocation response:', data);
        if (data.success) {
            showNotification('تم تطبيق التوزيع الذكي بنجاح', 'success');
            alert(data.message);
            
            // Refresh the page to show new settings
            setTimeout(() => window.location.reload(), 2000);
        } else {
            showNotification(data.message || 'تم إكمال التوزيع الذكي', 'info');
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error in smart GPU allocation:', error);
        showNotification('خطأ في التوزيع الذكي لكروت الشاشة', 'error');
    });
}

function showGPUInstallationHelper() {
    console.log('Running GPU diagnosis...');
    
    sessionFetch('/api/gpu-diagnostics', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('GPU diagnostics response:', data);
        let diagnosisText = '=== تشخيص كروت الشاشة ===\n\n';
        
        if (data.success) {
            diagnosisText += data.message + '\n\n';
            
            if (data.diagnostics && data.diagnostics.recommendations) {
                diagnosisText += 'التوصيات:\n';
                data.diagnostics.recommendations.forEach(rec => {
                    diagnosisText += `• ${rec}\n`;
                });
            }
        } else {
            diagnosisText += data.message || 'تم إكمال تشخيص كروت الشاشة';
        }
        
        alert(diagnosisText);
    })
    .catch(error => {
        console.error('Error in GPU diagnosis:', error);
        showNotification('خطأ في تشخيص كروت الشاشة', 'error');
    });
}

// API Configuration Functions
async function testOllamaConnection() {
    try {
        const response = await sessionFetch('/api/test-ollama', {
            method: 'POST'
        });
        const result = await response.json();
        alert(result.message);
    } catch (error) {
        alert('Ollama test failed: ' + error.message);
    }
}

async function testWhisperAPI() {
    try {
        const response = await sessionFetch('/api/test-whisper', {
            method: 'POST'
        });
        const result = await response.json();
        alert(result.message);
    } catch (error) {
        alert('Whisper test failed: ' + error.message);
    }
}

async function benchmarkModels() {
    try {
        const response = await sessionFetch('/api/benchmark-models', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            let benchmarkText = '=== Model Benchmark Results ===\n\n';
            for (const [model, status] of Object.entries(result.results)) {
                benchmarkText += `${model}: ${status}\n`;
            }
            alert(benchmarkText);
        } else {
            alert(result.message);
        }
    } catch (error) {
        alert('Benchmark failed: ' + error.message);
    }
}

// Helper function to show notifications if not available in main page
if (typeof showNotification === 'undefined') {
    function showNotification(message, type) {
        console.log(`Notification [${type}]: ${message}`);
        
        // Create notification element
        var notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        // Set background color based on type
        if (type === 'success') {
            notification.style.backgroundColor = '#28a745';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#dc3545';
        } else if (type === 'warning') {
            notification.style.backgroundColor = '#ffc107';
            notification.style.color = '#212529';
        } else {
            notification.style.backgroundColor = '#17a2b8';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

console.log('GPU management functions ready: refreshGPUOptions, smartGPUAllocation, showGPUDiagnosis');