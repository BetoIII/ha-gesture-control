"""
WebSocket Event Handlers

This module contains all Socket.IO event handlers for real-time communication
between the server and clients.
"""

import logging
from flask_socketio import emit

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handles WebSocket events and state management"""

    def __init__(self, socketio):
        """
        Initialize WebSocket handler

        Args:
            socketio: Flask-SocketIO instance
        """
        self.socketio = socketio
        self.gesture_mode_active = False
        self.camera_active = False
        self.connected_clients = set()

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register all Socket.IO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            from flask import request
            client_id = request.sid
            self.connected_clients.add(client_id)
            logger.info(f'Client connected: {client_id} (Total: {len(self.connected_clients)})')

            # Send current state to newly connected client
            emit('connection_status', {'status': 'connected'})
            emit('system_state', {
                'gesture_mode_active': self.gesture_mode_active,
                'camera_active': self.camera_active
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            from flask import request
            client_id = request.sid
            self.connected_clients.discard(client_id)
            logger.info(f'Client disconnected: {client_id} (Total: {len(self.connected_clients)})')

        @self.socketio.on('toggle_gesture_mode')
        def handle_toggle_gesture_mode(data):
            enabled = data.get('enabled', False)
            self.gesture_mode_active = enabled

            logger.info(f'Gesture mode toggled: {enabled}')

            # Broadcast to all clients
            self.socketio.emit('gesture_mode_changed', {
                'enabled': enabled
            }, broadcast=True)

        @self.socketio.on('camera_status')
        def handle_camera_status(data):
            self.camera_active = data.get('active', False)
            logger.info(f'Camera status updated: {self.camera_active}')

            # Broadcast to all clients
            self.socketio.emit('camera_status_changed', {
                'active': self.camera_active
            }, broadcast=True)

        @self.socketio.on('request_config')
        def handle_request_config():
            """Client requests current configuration"""
            from flask import request
            logger.info(f'Client {request.sid} requested configuration')
            # This will be implemented when config manager is ready
            emit('config_data', {'mappings': []})

    def broadcast_gesture_event(self, gesture_data):
        """
        Broadcast gesture detection event to all connected clients

        Args:
            gesture_data: Dictionary containing:
                - timestamp: Unix timestamp
                - hand: 'Left' or 'Right'
                - gesture: Gesture name (e.g., 'Open_Palm')
                - confidence: Confidence score (0.0-1.0)
        """
        if not self.gesture_mode_active:
            return

        self.socketio.emit('gesture_detected', gesture_data, broadcast=True)
        logger.debug(f'Broadcasted gesture: {gesture_data["gesture"]} ({gesture_data["confidence"]:.2f})')

    def broadcast_action_result(self, action_data):
        """
        Broadcast Home Assistant action result to all connected clients

        Args:
            action_data: Dictionary containing:
                - success: Boolean
                - entity_id: Entity ID
                - service: Service name
                - message: Result message
                - error: Error message (if failed)
        """
        self.socketio.emit('action_result', action_data, broadcast=True)

        if action_data.get('success'):
            logger.info(f'Action success: {action_data["entity_id"]} - {action_data["service"]}')
        else:
            logger.error(f'Action failed: {action_data.get("error", "Unknown error")}')

    def broadcast_config_update(self, config_data):
        """
        Broadcast configuration update to all connected clients

        Args:
            config_data: Dictionary containing updated configuration
        """
        self.socketio.emit('config_updated', config_data, broadcast=True)
        logger.info('Configuration updated and broadcasted to all clients')

    def get_client_count(self):
        """Get number of connected clients"""
        return len(self.connected_clients)

    def is_gesture_mode_active(self):
        """Check if gesture mode is currently active"""
        return self.gesture_mode_active

    def is_camera_active(self):
        """Check if camera is currently active"""
        return self.camera_active
