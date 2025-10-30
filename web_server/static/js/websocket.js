/**
 * WebSocket Client for HA Gesture Control
 *
 * Handles real-time communication with the server using Socket.IO
 */

class WebSocketClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second

        this.eventHandlers = {
            connect: [],
            disconnect: [],
            gesture_detected: [],
            action_result: [],
            gesture_mode_changed: [],
            camera_status_changed: [],
            config_updated: [],
            system_state: []
        };
    }

    /**
     * Initialize and connect to the WebSocket server
     */
    connect() {
        console.log('Connecting to WebSocket server...');

        // Initialize Socket.IO connection
        this.socket = io({
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: this.maxReconnectAttempts
        });

        // Register event handlers
        this.socket.on('connect', () => this.handleConnect());
        this.socket.on('disconnect', () => this.handleDisconnect());
        this.socket.on('connection_status', (data) => this.handleConnectionStatus(data));
        this.socket.on('system_state', (data) => this.handleSystemState(data));
        this.socket.on('gesture_detected', (data) => this.handleGestureDetected(data));
        this.socket.on('action_result', (data) => this.handleActionResult(data));
        this.socket.on('gesture_mode_changed', (data) => this.handleGestureModeChanged(data));
        this.socket.on('camera_status_changed', (data) => this.handleCameraStatusChanged(data));
        this.socket.on('config_updated', (data) => this.handleConfigUpdated(data));

        // Reconnect handling
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}...`);
            this.reconnectAttempts = attemptNumber;
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log('Reconnected successfully!');
            this.reconnectAttempts = 0;
            this.showToast('Reconnected to server', 'success');
        });

        this.socket.on('reconnect_failed', () => {
            console.error('Failed to reconnect to server');
            this.showToast('Connection failed. Please refresh the page.', 'error');
        });
    }

    /**
     * Handle successful connection
     */
    handleConnect() {
        console.log('Connected to WebSocket server');
        this.connected = true;
        this.reconnectAttempts = 0;

        // Update connection status in UI
        this.updateConnectionStatus(true);

        // Trigger registered connect handlers
        this.triggerEvent('connect');
    }

    /**
     * Handle disconnection
     */
    handleDisconnect() {
        console.log('Disconnected from WebSocket server');
        this.connected = false;

        // Update connection status in UI
        this.updateConnectionStatus(false);

        // Trigger registered disconnect handlers
        this.triggerEvent('disconnect');
    }

    /**
     * Handle connection status message
     */
    handleConnectionStatus(data) {
        console.log('Connection status:', data);
    }

    /**
     * Handle system state update
     */
    handleSystemState(data) {
        console.log('System state:', data);
        this.triggerEvent('system_state', data);
    }

    /**
     * Handle gesture detection event
     */
    handleGestureDetected(data) {
        console.log('Gesture detected:', data);
        this.triggerEvent('gesture_detected', data);
    }

    /**
     * Handle action result from Home Assistant
     */
    handleActionResult(data) {
        console.log('Action result:', data);
        this.triggerEvent('action_result', data);
    }

    /**
     * Handle gesture mode change
     */
    handleGestureModeChanged(data) {
        console.log('Gesture mode changed:', data);
        this.triggerEvent('gesture_mode_changed', data);
    }

    /**
     * Handle camera status change
     */
    handleCameraStatusChanged(data) {
        console.log('Camera status changed:', data);
        this.triggerEvent('camera_status_changed', data);
    }

    /**
     * Handle configuration update
     */
    handleConfigUpdated(data) {
        console.log('Configuration updated:', data);
        this.triggerEvent('config_updated', data);
    }

    /**
     * Emit gesture mode toggle to server
     */
    toggleGestureMode(enabled) {
        if (!this.connected) {
            console.error('Cannot toggle gesture mode: not connected');
            return;
        }

        console.log('Toggling gesture mode:', enabled);
        this.socket.emit('toggle_gesture_mode', { enabled });
    }

    /**
     * Send camera status to server
     */
    sendCameraStatus(active) {
        if (!this.connected) {
            console.error('Cannot send camera status: not connected');
            return;
        }

        this.socket.emit('camera_status', { active });
    }

    /**
     * Request current configuration from server
     */
    requestConfig() {
        if (!this.connected) {
            console.error('Cannot request config: not connected');
            return;
        }

        this.socket.emit('request_config');
    }

    /**
     * Register event handler
     */
    on(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].push(handler);
        } else {
            console.warn(`Unknown event: ${event}`);
        }
    }

    /**
     * Trigger registered event handlers
     */
    triggerEvent(event, data = null) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${event} handler:`, error);
                }
            });
        }
    }

    /**
     * Update connection status indicator in UI
     */
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;

        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle text-green-500 mr-2"></i>Connected';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle text-red-500 mr-2"></i>Disconnected';
        }
    }

    /**
     * Show toast notification (will be implemented in app.js)
     */
    showToast(message, type = 'info') {
        if (window.app && window.app.showToast) {
            window.app.showToast(message, type);
        } else {
            console.log(`Toast [${type}]: ${message}`);
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.connected;
    }
}

// Create global WebSocket client instance
window.wsClient = new WebSocketClient();
