/**
 * Main Application Logic for HA Gesture Control
 *
 * Handles UI interactions, state management, and visual feedback
 */

class GestureControlApp {
    constructor() {
        this.gestureModeActive = false;
        this.cameraActive = false;
        this.gestureMappings = [];
        this.lastAction = null;
        this.detectionTimeout = null;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize application
     */
    init() {
        console.log('Initializing HA Gesture Control App...');

        // Set up UI event listeners
        this.setupEventListeners();

        // Connect WebSocket
        window.wsClient.connect();

        // Register WebSocket event handlers
        this.setupWebSocketHandlers();

        console.log('App initialized successfully');
    }

    /**
     * Set up UI event listeners
     */
    setupEventListeners() {
        // Gesture mode toggle
        const gestureToggle = document.getElementById('gestureToggle');
        if (gestureToggle) {
            gestureToggle.addEventListener('change', (e) => {
                this.toggleGestureMode(e.target.checked);
            });
        }

        // Settings button
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.openSettings());
        }

        // Add gesture button
        const addGestureBtn = document.getElementById('addGestureBtn');
        if (addGestureBtn) {
            addGestureBtn.addEventListener('click', () => this.openAddGestureModal());
        }

        // Modal close buttons
        const closeModalBtn = document.getElementById('closeModalBtn');
        const cancelConfigBtn = document.getElementById('cancelConfigBtn');
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.closeModal());
        }
        if (cancelConfigBtn) {
            cancelConfigBtn.addEventListener('click', () => this.closeModal());
        }

        // Save config button
        const saveConfigBtn = document.getElementById('saveConfigBtn');
        if (saveConfigBtn) {
            saveConfigBtn.addEventListener('click', () => this.saveConfig());
        }

        // Camera feed error handling
        const cameraFeed = document.getElementById('cameraFeed');
        if (cameraFeed) {
            cameraFeed.addEventListener('load', () => {
                this.hideCameraLoading();
            });
            cameraFeed.addEventListener('error', () => {
                this.showCameraError();
            });
        }
    }

    /**
     * Set up WebSocket event handlers
     */
    setupWebSocketHandlers() {
        // Connection events
        window.wsClient.on('connect', () => {
            this.showToast('Connected to server', 'success');
        });

        window.wsClient.on('disconnect', () => {
            this.showToast('Disconnected from server', 'warning');
        });

        // System state
        window.wsClient.on('system_state', (data) => {
            this.updateSystemState(data);
        });

        // Gesture detected
        window.wsClient.on('gesture_detected', (data) => {
            this.handleGestureDetected(data);
        });

        // Action result
        window.wsClient.on('action_result', (data) => {
            this.handleActionResult(data);
        });

        // Gesture mode changed
        window.wsClient.on('gesture_mode_changed', (data) => {
            this.updateGestureMode(data.enabled);
        });

        // Camera status changed
        window.wsClient.on('camera_status_changed', (data) => {
            this.updateCameraStatus(data.active);
        });

        // Config updated
        window.wsClient.on('config_updated', (data) => {
            this.loadGestureMappings(data);
        });
    }

    /**
     * Toggle gesture mode on/off
     */
    toggleGestureMode(enabled) {
        console.log('Toggling gesture mode:', enabled);
        this.gestureModeActive = enabled;

        // Send to server
        window.wsClient.toggleGestureMode(enabled);

        // Update UI
        this.updateUI();
    }

    /**
     * Update system state from server
     */
    updateSystemState(data) {
        console.log('Updating system state:', data);
        this.gestureModeActive = data.gesture_mode_active;
        this.cameraActive = data.camera_active;

        // Update toggle switch
        const gestureToggle = document.getElementById('gestureToggle');
        if (gestureToggle) {
            gestureToggle.checked = this.gestureModeActive;
        }

        this.updateUI();
    }

    /**
     * Update gesture mode state
     */
    updateGestureMode(enabled) {
        this.gestureModeActive = enabled;
        this.updateUI();
    }

    /**
     * Update camera status
     */
    updateCameraStatus(active) {
        this.cameraActive = active;

        const cameraStatusEl = document.getElementById('cameraStatus');
        if (cameraStatusEl) {
            if (active) {
                cameraStatusEl.textContent = 'Active';
                cameraStatusEl.className = 'font-medium text-green-600';
            } else {
                cameraStatusEl.textContent = 'Inactive';
                cameraStatusEl.className = 'font-medium text-gray-500';
            }
        }
    }

    /**
     * Update UI based on current state
     */
    updateUI() {
        const inactiveState = document.getElementById('inactiveState');
        const activeState = document.getElementById('activeState');

        if (this.gestureModeActive) {
            // Show active state
            if (inactiveState) inactiveState.classList.add('hidden');
            if (activeState) activeState.classList.remove('hidden');

            // Start camera feed
            this.startCameraFeed();
        } else {
            // Show inactive state
            if (inactiveState) inactiveState.classList.remove('hidden');
            if (activeState) activeState.classList.add('hidden');

            // Stop camera feed
            this.stopCameraFeed();
        }
    }

    /**
     * Start camera feed
     */
    startCameraFeed() {
        const cameraFeed = document.getElementById('cameraFeed');
        const cameraLoading = document.getElementById('cameraLoading');

        if (cameraFeed) {
            // Show loading state
            if (cameraLoading) {
                cameraLoading.classList.remove('hidden');
            }

            // Add timestamp to prevent caching
            const timestamp = new Date().getTime();
            cameraFeed.src = `/camera_feed?t=${timestamp}`;

            // Notify server
            window.wsClient.sendCameraStatus(true);
        }
    }

    /**
     * Stop camera feed
     */
    stopCameraFeed() {
        const cameraFeed = document.getElementById('cameraFeed');
        if (cameraFeed) {
            cameraFeed.src = '';
        }

        // Notify server
        window.wsClient.sendCameraStatus(false);
    }

    /**
     * Hide camera loading indicator
     */
    hideCameraLoading() {
        const cameraLoading = document.getElementById('cameraLoading');
        if (cameraLoading) {
            cameraLoading.classList.add('hidden');
        }
    }

    /**
     * Show camera error
     */
    showCameraError() {
        const cameraLoading = document.getElementById('cameraLoading');
        if (cameraLoading) {
            cameraLoading.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                    <p class="text-gray-400">Camera not available</p>
                    <p class="text-sm text-gray-500 mt-2">Make sure the gesture recognition service is running</p>
                </div>
            `;
            cameraLoading.classList.remove('hidden');
        }
    }

    /**
     * Handle gesture detection event
     */
    handleGestureDetected(data) {
        console.log('Gesture detected:', data);

        // Show detection panel
        this.showDetectionPanel(data);

        // Flash camera border
        this.flashCameraBorder('blue');
    }

    /**
     * Show detection panel with gesture info
     */
    showDetectionPanel(gestureData) {
        const detectionPanel = document.getElementById('detectionPanel');
        const detectedGesture = document.getElementById('detectedGesture');
        const detectedConfidence = document.getElementById('detectedConfidence');

        if (detectionPanel && detectedGesture && detectedConfidence) {
            // Format gesture name (replace underscores with spaces, uppercase)
            const gestureName = gestureData.gesture.replace(/_/g, ' ').toUpperCase();
            const confidence = Math.round(gestureData.confidence * 100);

            detectedGesture.textContent = gestureName;
            detectedConfidence.textContent = `${confidence}%`;

            // Show panel
            detectionPanel.classList.remove('hidden');

            // Auto-hide after 2 seconds
            if (this.detectionTimeout) {
                clearTimeout(this.detectionTimeout);
            }
            this.detectionTimeout = setTimeout(() => {
                detectionPanel.classList.add('hidden');
            }, 2000);
        }
    }

    /**
     * Handle Home Assistant action result
     */
    handleActionResult(data) {
        console.log('Action result:', data);

        if (data.success) {
            // Show success toast
            this.showToast(data.message || 'Action executed successfully', 'success');

            // Flash camera border green
            this.flashCameraBorder('green');

            // Pulse detection panel
            this.pulseDetectionPanel();

            // Update last action
            this.updateLastAction(data);
        } else {
            // Show error toast
            this.showToast(data.error || 'Action failed', 'error');

            // Flash camera border red
            this.flashCameraBorder('red');
        }
    }

    /**
     * Flash camera container border
     */
    flashCameraBorder(color) {
        const cameraContainer = document.getElementById('cameraContainer');
        if (!cameraContainer) return;

        const colorClasses = {
            blue: 'border-blue-500',
            green: 'border-green-500',
            red: 'border-red-500'
        };

        const borderClass = colorClasses[color] || colorClasses.blue;

        // Add border
        cameraContainer.classList.add('border-4', borderClass, 'transition-all', 'duration-300');

        // Remove after 500ms
        setTimeout(() => {
            cameraContainer.classList.remove('border-4', 'border-blue-500', 'border-green-500', 'border-red-500');
        }, 500);
    }

    /**
     * Pulse detection panel animation
     */
    pulseDetectionPanel() {
        const detectionPanel = document.getElementById('detectionPanel');
        if (!detectionPanel) return;

        detectionPanel.classList.add('animate-pulse');

        setTimeout(() => {
            detectionPanel.classList.remove('animate-pulse');
        }, 1000);
    }

    /**
     * Update last action display
     */
    updateLastAction(actionData) {
        const lastActionEl = document.getElementById('lastAction');
        if (!lastActionEl) return;

        this.lastAction = {
            entity_id: actionData.entity_id,
            service: actionData.service,
            timestamp: Date.now()
        };

        const timeAgo = 'just now';
        lastActionEl.textContent = `Last Action: ${actionData.entity_id} - ${actionData.service} (${timeAgo})`;

        // Update time periodically
        this.updateLastActionTime();
    }

    /**
     * Update last action time display
     */
    updateLastActionTime() {
        if (!this.lastAction) return;

        const lastActionEl = document.getElementById('lastAction');
        if (!lastActionEl) return;

        const secondsAgo = Math.floor((Date.now() - this.lastAction.timestamp) / 1000);
        let timeAgo;

        if (secondsAgo < 5) {
            timeAgo = 'just now';
        } else if (secondsAgo < 60) {
            timeAgo = `${secondsAgo} seconds ago`;
        } else if (secondsAgo < 3600) {
            const minutes = Math.floor(secondsAgo / 60);
            timeAgo = `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            const hours = Math.floor(secondsAgo / 3600);
            timeAgo = `${hours} hour${hours > 1 ? 's' : ''} ago`;
        }

        lastActionEl.textContent = `Last Action: ${this.lastAction.entity_id} - ${this.lastAction.service} (${timeAgo})`;
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast-notification transform transition-all duration-300 translate-x-full';

        // Set color based on type
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };
        const bgColor = colors[type] || colors.info;

        // Set icon based on type
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        const icon = icons[type] || icons.info;

        toast.innerHTML = `
            <div class="${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3">
                <i class="fas ${icon} text-xl"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Slide in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 10);

        // Slide out and remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                toastContainer.removeChild(toast);
            }, 300);
        }, 5000);
    }

    /**
     * Load gesture mappings
     */
    loadGestureMappings(config) {
        this.gestureMappings = config.mappings || [];
        this.renderGestureList();
    }

    /**
     * Render gesture list in side panel
     */
    renderGestureList() {
        const gestureList = document.getElementById('gestureList');
        if (!gestureList) return;

        if (this.gestureMappings.length === 0) {
            gestureList.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="fas fa-hand-paper text-3xl mb-3"></i>
                    <p class="text-sm">No gestures configured</p>
                    <p class="text-xs mt-1">Click "Add Gesture Mapping" to get started</p>
                </div>
            `;
            return;
        }

        // Render gesture items
        gestureList.innerHTML = this.gestureMappings.map(mapping => `
            <div class="gesture-item p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors border border-gray-200">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <p class="font-medium text-gray-800 text-sm">${mapping.gesture.replace(/_/g, ' ')}</p>
                        <p class="text-xs text-gray-600 mt-1">${mapping.action.entity_id}</p>
                        <p class="text-xs text-blue-600 mt-1">${mapping.action.service}</p>
                    </div>
                    <div class="text-gray-400">
                        <i class="fas fa-chevron-right"></i>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Open settings modal
     */
    openSettings() {
        const modal = document.getElementById('configModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    /**
     * Open add gesture modal
     */
    openAddGestureModal() {
        this.openSettings();
        // Additional logic for add gesture form will be implemented later
    }

    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('configModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    /**
     * Save configuration
     */
    saveConfig() {
        // Configuration save logic will be implemented later
        this.showToast('Configuration saved', 'success');
        this.closeModal();
    }
}

// Initialize app when script loads
window.app = new GestureControlApp();

// Update last action time every 5 seconds
setInterval(() => {
    if (window.app && window.app.lastAction) {
        window.app.updateLastActionTime();
    }
}, 5000);
