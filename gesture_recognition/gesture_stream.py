"""
MediaPipe Gesture Recognition with Socket Output

This module captures video from webcam, detects hand gestures using MediaPipe,
and streams both gesture events and video frames.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import json
import socket
import threading
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config.constants import (
        DEFAULT_CAMERA_INDEX,
        DEFAULT_CAMERA_WIDTH,
        DEFAULT_CAMERA_HEIGHT,
        DEFAULT_CAMERA_FPS,
        DEFAULT_SOCKET_HOST,
        DEFAULT_SOCKET_PORT,
        MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
        MEDIAPIPE_MIN_HAND_PRESENCE_CONFIDENCE,
        MEDIAPIPE_MAX_NUM_HANDS,
        FRAME_PROCESSING_DELAY,
        GESTURE_DEBOUNCE_TIME
    )
except ImportError:
    # Fallback to hardcoded values if constants not available
    DEFAULT_CAMERA_INDEX = 0
    DEFAULT_CAMERA_WIDTH = 640
    DEFAULT_CAMERA_HEIGHT = 480
    DEFAULT_CAMERA_FPS = 30
    DEFAULT_SOCKET_HOST = 'localhost'
    DEFAULT_SOCKET_PORT = 5555
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.7
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
    MEDIAPIPE_MIN_HAND_PRESENCE_CONFIDENCE = 0.7
    MEDIAPIPE_MAX_NUM_HANDS = 2
    FRAME_PROCESSING_DELAY = 0.01
    GESTURE_DEBOUNCE_TIME = 1.0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GestureRecognizer:
    """Hand gesture recognition using MediaPipe"""

    def __init__(self, model_path='gesture_recognizer.task',
                 camera_index=DEFAULT_CAMERA_INDEX,
                 socket_host=DEFAULT_SOCKET_HOST,
                 socket_port=DEFAULT_SOCKET_PORT):
        """
        Initialize gesture recognizer

        Args:
            model_path: Path to MediaPipe gesture recognizer model
            camera_index: Camera device index (0 for default webcam)
            socket_host: Host for TCP socket connection
            socket_port: Port for TCP socket connection
        """
        self.model_path = model_path
        self.camera_index = camera_index
        self.socket_host = socket_host
        self.socket_port = socket_port

        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Initialize gesture recognizer
        self.recognizer = None
        self.hands = None

        # Video capture
        self.cap = None

        # Socket connection
        self.socket_conn = None
        self.socket_connected = False

        # State
        self.running = False
        self.frame_count = 0
        self.last_gesture = None
        self.last_gesture_time = 0

        # MJPEG streaming
        self.current_frame = None
        self.frame_lock = threading.Lock()

    def initialize_mediapipe(self):
        """Initialize MediaPipe components"""
        try:
            # Initialize hands detector
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=MEDIAPIPE_MAX_NUM_HANDS,
                min_detection_confidence=MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=MEDIAPIPE_MIN_TRACKING_CONFIDENCE
            )

            # Initialize gesture recognizer
            base_options = mp.tasks.BaseOptions(model_asset_path=self.model_path)
            options = mp.tasks.vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=mp.tasks.vision.RunningMode.IMAGE,
                num_hands=MEDIAPIPE_MAX_NUM_HANDS,
                min_hand_detection_confidence=MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
                min_hand_presence_confidence=MEDIAPIPE_MIN_HAND_PRESENCE_CONFIDENCE,
                min_tracking_confidence=MEDIAPIPE_MIN_TRACKING_CONFIDENCE
            )
            self.recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)

            logger.info('MediaPipe initialized successfully')
            return True

        except Exception as e:
            logger.error(f'Failed to initialize MediaPipe: {e}')
            return False

    def initialize_camera(self):
        """Initialize video capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                logger.error(f'Failed to open camera {self.camera_index}')
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, DEFAULT_CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DEFAULT_CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, DEFAULT_CAMERA_FPS)

            logger.info(f'Camera {self.camera_index} initialized successfully')
            return True

        except Exception as e:
            logger.error(f'Failed to initialize camera: {e}')
            return False

    def connect_socket(self):
        """Connect to TCP socket for sending gesture events"""
        try:
            self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_conn.connect((self.socket_host, self.socket_port))
            self.socket_connected = True
            logger.info(f'Connected to socket {self.socket_host}:{self.socket_port}')
            return True

        except Exception as e:
            logger.warning(f'Failed to connect to socket: {e}')
            self.socket_connected = False
            return False

    def send_gesture_event(self, gesture_data):
        """
        Send gesture event through socket

        Args:
            gesture_data: Dictionary containing gesture information
        """
        if not self.socket_connected:
            return

        try:
            # Convert to JSON and send
            message = json.dumps(gesture_data) + '\n'
            self.socket_conn.sendall(message.encode('utf-8'))

        except Exception as e:
            logger.error(f'Failed to send gesture event: {e}')
            self.socket_connected = False

    def process_frame(self, frame):
        """
        Process a single frame for gesture recognition

        Args:
            frame: OpenCV frame (BGR format)

        Returns:
            Processed frame with annotations
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect hands
        hands_results = self.hands.process(rgb_frame)

        # Draw hand landmarks
        annotated_frame = frame.copy()

        if hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

        # Recognize gestures
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            gesture_results = self.recognizer.recognize(mp_image)

            if gesture_results.gestures:
                for i, gesture_list in enumerate(gesture_results.gestures):
                    if not gesture_list:
                        continue

                    # Get top gesture
                    gesture = gesture_list[0]
                    gesture_name = gesture.category_name
                    confidence = gesture.score

                    # Get handedness (Left or Right)
                    handedness = "Unknown"
                    if i < len(gesture_results.handedness):
                        handedness = gesture_results.handedness[i][0].category_name

                    # Create gesture event
                    gesture_data = {
                        'timestamp': int(time.time() * 1000),
                        'hand': handedness,
                        'gesture': gesture_name,
                        'confidence': float(confidence)
                    }

                    # Send gesture event (with debouncing)
                    current_time = time.time()
                    gesture_key = f"{handedness}_{gesture_name}"

                    if (self.last_gesture != gesture_key or
                        current_time - self.last_gesture_time > GESTURE_DEBOUNCE_TIME):

                        self.send_gesture_event(gesture_data)
                        self.last_gesture = gesture_key
                        self.last_gesture_time = current_time

                        logger.debug(f'Gesture: {gesture_name} ({handedness}) - {confidence:.2f}')

                    # Draw gesture text on frame
                    text = f'{handedness}: {gesture_name} ({confidence:.2f})'
                    cv2.putText(annotated_frame, text,
                               (10, 30 + i * 30),
                               cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (0, 255, 0), 2)

        except Exception as e:
            logger.error(f'Error recognizing gesture: {e}')

        return annotated_frame

    def get_current_frame(self):
        """Get the current frame for MJPEG streaming"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def run(self):
        """Main loop for gesture recognition"""
        logger.info('Starting gesture recognition...')

        # Initialize components
        if not self.initialize_mediapipe():
            logger.error('Failed to initialize MediaPipe')
            return

        if not self.initialize_camera():
            logger.error('Failed to initialize camera')
            return

        # Try to connect to socket (optional)
        self.connect_socket()

        self.running = True
        logger.info('Gesture recognition running')

        try:
            while self.running:
                # Read frame
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning('Failed to read frame from camera')
                    time.sleep(0.1)
                    continue

                # Process frame
                annotated_frame = self.process_frame(frame)

                # Store frame for MJPEG streaming
                with self.frame_lock:
                    self.current_frame = annotated_frame

                # Update frame count
                self.frame_count += 1

                # Small delay to prevent CPU overload
                time.sleep(FRAME_PROCESSING_DELAY)

        except KeyboardInterrupt:
            logger.info('Stopping gesture recognition (keyboard interrupt)')

        except Exception as e:
            logger.error(f'Error in main loop: {e}')

        finally:
            self.cleanup()

    def stop(self):
        """Stop gesture recognition"""
        logger.info('Stopping gesture recognition...')
        self.running = False

    def cleanup(self):
        """Clean up resources safely"""
        logger.info('Cleaning up resources...')

        # Safely release camera
        if self.cap is not None:
            try:
                self.cap.release()
                logger.info('Camera released')
            except Exception as e:
                logger.error(f'Error releasing camera: {e}')

        # Safely close MediaPipe components
        if self.hands is not None:
            try:
                self.hands.close()
                logger.info('MediaPipe hands closed')
            except Exception as e:
                logger.error(f'Error closing hands: {e}')

        if self.recognizer is not None:
            try:
                self.recognizer.close()
                logger.info('MediaPipe recognizer closed')
            except Exception as e:
                logger.error(f'Error closing recognizer: {e}')

        # Safely close socket
        if self.socket_conn is not None:
            try:
                self.socket_conn.close()
                logger.info('Socket connection closed')
            except Exception as e:
                logger.error(f'Error closing socket: {e}')

        logger.info('Cleanup complete')


def main():
    """Main entry point"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='MediaPipe Gesture Recognition')
    parser.add_argument('--model', type=str,
                       default='gesture_recognizer.task',
                       help='Path to gesture recognizer model')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device index')
    parser.add_argument('--socket-host', type=str, default='localhost',
                       help='Socket host for gesture events')
    parser.add_argument('--socket-port', type=int, default=5555,
                       help='Socket port for gesture events')

    args = parser.parse_args()

    # Check if model file exists
    if not os.path.exists(args.model):
        logger.error(f'Model file not found: {args.model}')
        logger.info('Please download the model from:')
        logger.info('https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task')
        return

    # Create and run gesture recognizer
    recognizer = GestureRecognizer(
        model_path=args.model,
        camera_index=args.camera,
        socket_host=args.socket_host,
        socket_port=args.socket_port
    )

    try:
        recognizer.run()
    except KeyboardInterrupt:
        recognizer.stop()


if __name__ == '__main__':
    main()
