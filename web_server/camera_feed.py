"""
Camera Feed Module for MJPEG Streaming

Provides MJPEG video stream from the gesture recognition system
"""

import cv2
import logging
import time
from flask import Response
import numpy as np

logger = logging.getLogger(__name__)


class CameraFeed:
    """Manages camera feed and MJPEG streaming"""

    def __init__(self, gesture_recognizer=None):
        """
        Initialize camera feed

        Args:
            gesture_recognizer: GestureRecognizer instance (optional)
        """
        self.gesture_recognizer = gesture_recognizer
        self.active = False
        self.frame_count = 0

    def generate_frames(self):
        """
        Generator function for MJPEG streaming

        Yields:
            JPEG-encoded frames in multipart format
        """
        logger.info('Starting MJPEG stream generation')
        self.active = True

        try:
            while self.active:
                # Get frame from gesture recognizer if available
                frame = None

                if self.gesture_recognizer:
                    frame = self.gesture_recognizer.get_current_frame()

                # If no frame available, generate a placeholder
                if frame is None:
                    frame = self._generate_placeholder_frame()

                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

                if not ret:
                    logger.warning('Failed to encode frame')
                    time.sleep(0.1)
                    continue

                # Convert to bytes
                frame_bytes = buffer.tobytes()

                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                self.frame_count += 1

                # Small delay to control frame rate (30 FPS)
                time.sleep(0.033)

        except GeneratorExit:
            logger.info('Client disconnected from MJPEG stream')

        except Exception as e:
            logger.error(f'Error generating frames: {e}')

        finally:
            self.active = False
            logger.info(f'MJPEG stream ended (frames: {self.frame_count})')

    def _generate_placeholder_frame(self):
        """
        Generate a placeholder frame when camera is not available

        Returns:
            OpenCV frame (BGR format)
        """
        # Create black frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Add text
        text = 'Camera Initializing...'
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        thickness = 2
        color = (200, 200, 200)

        # Get text size
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)

        # Center text
        x = (640 - text_width) // 2
        y = (480 + text_height) // 2

        cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)

        # Add camera icon (simple circle with a dot)
        center_x, center_y = 320, 200
        cv2.circle(frame, (center_x, center_y), 50, (100, 100, 100), 3)
        cv2.circle(frame, (center_x, center_y), 20, (100, 100, 100), -1)
        cv2.rectangle(frame, (center_x - 10, center_y - 60), (center_x + 10, center_y - 50), (100, 100, 100), -1)

        return frame

    def stop(self):
        """Stop the camera feed"""
        logger.info('Stopping camera feed')
        self.active = False

    def is_active(self):
        """Check if camera feed is active"""
        return self.active

    def get_frame_count(self):
        """Get total number of frames streamed"""
        return self.frame_count


def create_mjpeg_response(camera_feed):
    """
    Create Flask response for MJPEG streaming

    Args:
        camera_feed: CameraFeed instance

    Returns:
        Flask Response with MJPEG stream
    """
    return Response(
        camera_feed.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# Global camera feed instance (will be initialized by app)
_camera_feed = None


def get_camera_feed():
    """Get or create global camera feed instance"""
    global _camera_feed

    if _camera_feed is None:
        _camera_feed = CameraFeed()

    return _camera_feed


def set_gesture_recognizer(gesture_recognizer):
    """
    Set the gesture recognizer for the camera feed

    Args:
        gesture_recognizer: GestureRecognizer instance
    """
    global _camera_feed

    if _camera_feed is None:
        _camera_feed = CameraFeed(gesture_recognizer)
    else:
        _camera_feed.gesture_recognizer = gesture_recognizer

    logger.info('Gesture recognizer set for camera feed')
