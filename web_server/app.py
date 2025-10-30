"""
Flask Web Server for HA Gesture Control

This module provides the web interface for the gesture control system.
It serves the UI, handles WebSocket connections, and provides REST API endpoints.
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
from camera_feed import get_camera_feed, create_mjpeg_response

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Socket.IO with eventlet
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
gesture_mode_active = False
camera_active = False


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gesture_mode': gesture_mode_active,
        'camera_active': camera_active
    })


@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'gesture_mode_active': gesture_mode_active,
        'camera_active': camera_active,
        'confidence_threshold': float(os.getenv('GESTURE_CONFIDENCE_THRESHOLD', 0.8)),
        'cooldown_seconds': int(os.getenv('GESTURE_COOLDOWN_SECONDS', 2))
    })


@app.route('/camera_feed')
def camera_feed():
    """MJPEG camera stream endpoint"""
    camera = get_camera_feed()
    return create_mjpeg_response(camera)


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f'Client connected: {request.sid}')
    emit('connection_status', {'status': 'connected'})

    # Send current system state to newly connected client
    emit('system_state', {
        'gesture_mode_active': gesture_mode_active,
        'camera_active': camera_active
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f'Client disconnected: {request.sid}')


@socketio.on('toggle_gesture_mode')
def handle_toggle_gesture_mode(data):
    """Handle gesture mode toggle from client"""
    global gesture_mode_active

    enabled = data.get('enabled', False)
    gesture_mode_active = enabled

    logger.info(f'Gesture mode toggled: {enabled}')

    # Broadcast to all clients
    socketio.emit('gesture_mode_changed', {
        'enabled': enabled
    }, broadcast=True)

    # Start/stop camera based on gesture mode
    if enabled:
        socketio.emit('start_camera', {})
    else:
        socketio.emit('stop_camera', {})


@socketio.on('camera_status')
def handle_camera_status(data):
    """Handle camera status updates"""
    global camera_active

    camera_active = data.get('active', False)
    logger.info(f'Camera status: {camera_active}')

    # Broadcast to all clients
    socketio.emit('camera_status_changed', {
        'active': camera_active
    }, broadcast=True)


# Helper function to broadcast gesture events (called from gesture recognition)
def broadcast_gesture_event(gesture_data):
    """
    Broadcast gesture detection event to all connected clients

    Args:
        gesture_data: Dictionary containing gesture information
            - timestamp: Unix timestamp
            - hand: 'Left' or 'Right'
            - gesture: Gesture name (e.g., 'Open_Palm')
            - confidence: Confidence score (0.0-1.0)
    """
    socketio.emit('gesture_detected', gesture_data, broadcast=True)
    logger.info(f'Gesture detected: {gesture_data}')


# Helper function to broadcast action results (called from Goose controller)
def broadcast_action_result(action_data):
    """
    Broadcast Home Assistant action result to all connected clients

    Args:
        action_data: Dictionary containing action result
            - success: Boolean
            - entity_id: Entity ID
            - service: Service name
            - message: Result message
            - error: Error message (if failed)
    """
    socketio.emit('action_result', action_data, broadcast=True)
    logger.info(f'Action result: {action_data}')


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Get host and port from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f'Starting Flask server on {host}:{port}')
    logger.info(f'Debug mode: {debug}')

    # Run the server with Socket.IO
    socketio.run(app, host=host, port=port, debug=debug)
