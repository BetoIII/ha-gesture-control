"""
Application Constants and Defaults

This module contains all application-wide constants and default values
to eliminate magic numbers throughout the codebase.
"""

# Gesture Recognition
DEFAULT_CONFIDENCE_THRESHOLD = 0.8
MIN_CONFIDENCE = 0.5
MAX_CONFIDENCE = 1.0

# Timing (seconds)
DEFAULT_COOLDOWN_SECONDS = 2.0
DEFAULT_MIN_HOLD_TIME = 0.5
FRAME_PROCESSING_DELAY = 0.01  # seconds between frame processing
SOCKET_TIMEOUT = 10.0  # seconds
SOCKET_ACCEPT_TIMEOUT = 1.0  # seconds for clean shutdown

# Camera Settings
DEFAULT_CAMERA_INDEX = 0
DEFAULT_CAMERA_WIDTH = 640
DEFAULT_CAMERA_HEIGHT = 480
DEFAULT_CAMERA_FPS = 30

# Socket Communication
DEFAULT_SOCKET_HOST = 'localhost'
DEFAULT_SOCKET_PORT = 5555
SOCKET_BUFFER_SIZE = 4096
SOCKET_RECV_SIZE = 1024

# Home Assistant
HA_REQUEST_TIMEOUT = 30.0  # seconds
HA_RETRY_ATTEMPTS = 3
HA_RETRY_DELAY = 1.0  # seconds
HA_MIN_TOKEN_LENGTH = 50  # HA tokens are typically ~180+ chars

# Logging
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FILE = 'logs/gesture_control.log'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# MediaPipe Settings
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.7
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
MEDIAPIPE_MIN_HAND_PRESENCE_CONFIDENCE = 0.7
MEDIAPIPE_MAX_NUM_HANDS = 2

# MJPEG Streaming
MJPEG_QUALITY = 85  # JPEG quality (0-100)
MJPEG_FRAME_RATE = 30  # Target FPS
MJPEG_FRAME_DELAY = 0.033  # seconds (1/30)

# Gesture Debouncing
GESTURE_DEBOUNCE_TIME = 1.0  # seconds between same gesture events
