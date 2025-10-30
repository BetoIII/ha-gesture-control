"""
Main Controller for HA Gesture Control

Entry point that orchestrates gesture recognition, Home Assistant integration,
and web server communication
"""

import os
import sys
import logging
import signal
import time
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gesture_handler import GestureHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gesture_control.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GestureControlMain:
    """Main application controller"""

    def __init__(self, config_path: str = None):
        """
        Initialize main controller

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.gesture_handler = None
        self.running = False

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f'Received signal {signum}, shutting down...')
        self.stop()

    def initialize(self) -> bool:
        """
        Initialize all components

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info('='*60)
            logger.info('HA Gesture Control - Initializing')
            logger.info('='*60)

            # Create logs directory
            os.makedirs('logs', exist_ok=True)

            # Initialize gesture handler
            logger.info('Initializing gesture handler...')
            self.gesture_handler = GestureHandler(self.config_path)

            # Test Home Assistant connection
            logger.info('Testing Home Assistant connection...')
            if not self.gesture_handler.test_ha_connection():
                logger.warning('Home Assistant connection test failed')
                logger.warning('Actions may not work correctly')

            # Set up callbacks (these would be connected to Flask WebSocket)
            self.gesture_handler.set_gesture_callback(self._on_gesture_detected)
            self.gesture_handler.set_action_callback(self._on_action_result)

            logger.info('Initialization complete')
            return True

        except Exception as e:
            logger.error(f'Initialization failed: {e}', exc_info=True)
            return False

    def _on_gesture_detected(self, gesture_data):
        """
        Callback for gesture detection

        Args:
            gesture_data: Gesture data dictionary
        """
        # This would broadcast to Flask WebSocket
        logger.info(
            f'Gesture detected: {gesture_data["gesture"]} '
            f'({gesture_data["hand"]}) - '
            f'{gesture_data["confidence"]:.2f}'
        )

        # TODO: Broadcast to Flask via WebSocket
        # from web_server.app import broadcast_gesture_event
        # broadcast_gesture_event(gesture_data)

    def _on_action_result(self, action_data):
        """
        Callback for action result

        Args:
            action_data: Action result dictionary
        """
        if action_data.get('success'):
            logger.info(
                f'Action succeeded: {action_data["entity_id"]} - '
                f'{action_data["service"]}'
            )
        else:
            logger.error(
                f'Action failed: {action_data.get("error", "Unknown error")}'
            )

        # TODO: Broadcast to Flask via WebSocket
        # from web_server.app import broadcast_action_result
        # broadcast_action_result(action_data)

    def start(self):
        """Start the gesture control system"""
        if not self.initialize():
            logger.error('Failed to initialize, exiting')
            return

        logger.info('='*60)
        logger.info('HA Gesture Control - Starting')
        logger.info('='*60)

        # Start socket server to receive gesture events
        socket_config = self.gesture_handler.config_manager.config.get(
            'socket_communication', {}
        )
        host = socket_config.get('host', 'localhost')
        port = socket_config.get('port', 5555)

        logger.info(f'Starting socket server on {host}:{port}...')
        self.gesture_handler.start_socket_server(host, port)

        self.running = True

        logger.info('='*60)
        logger.info('HA Gesture Control - Running')
        logger.info('='*60)
        logger.info('Waiting for gesture events...')
        logger.info('Press Ctrl+C to stop')

        # Main loop
        try:
            while self.running:
                time.sleep(1)

                # Periodic tasks could go here
                # - Check Home Assistant connection
                # - Reload config if changed
                # - Log statistics

        except KeyboardInterrupt:
            logger.info('Keyboard interrupt received')

        finally:
            self.stop()

    def stop(self):
        """Stop the gesture control system"""
        if not self.running:
            return

        logger.info('='*60)
        logger.info('HA Gesture Control - Stopping')
        logger.info('='*60)

        self.running = False

        # Stop gesture handler
        if self.gesture_handler:
            self.gesture_handler.cleanup()

        # Print statistics
        if self.gesture_handler:
            stats = self.gesture_handler.get_statistics()
            logger.info('='*60)
            logger.info('Final Statistics:')
            logger.info(f"  Gestures received: {stats['gestures_received']}")
            logger.info(f"  Gestures below threshold: {stats['gestures_below_threshold']}")
            logger.info(f"  Gestures debounced: {stats['gestures_debounced']}")
            logger.info(f"  Actions triggered: {stats['actions_triggered']}")
            logger.info(f"  Actions succeeded: {stats['actions_succeeded']}")
            logger.info(f"  Actions failed: {stats['actions_failed']}")
            logger.info('='*60)

        logger.info('Shutdown complete')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='HA Gesture Control - Hand gesture control for Home Assistant'
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: config/gesture_config.yaml)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Create and run controller
    controller = GestureControlMain(config_path=args.config)
    controller.start()


if __name__ == '__main__':
    main()
