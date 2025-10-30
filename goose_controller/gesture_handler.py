"""
Gesture Handler

Main controller that processes gesture events and triggers Home Assistant actions
"""

import json
import socket
import threading
import logging
import time
from typing import Dict, Any, Optional, Callable

from config_manager import ConfigManager
from debouncer import GestureDebouncer, HoldTimeValidator
from ha_mcp_client import SyncHomeAssistantClient

logger = logging.getLogger(__name__)


class GestureHandler:
    """Handles gesture events and executes Home Assistant actions"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize gesture handler

        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path)

        if not self.config_manager.load_config():
            raise RuntimeError('Failed to load configuration')

        # Initialize components
        ha_config = self.config_manager.get_ha_config()
        self.ha_client = SyncHomeAssistantClient(
            mcp_url=ha_config['mcp_url'],
            token_env_var=ha_config['token_env_var']
        )

        # Initialize debouncer
        cooldown = self.config_manager.get_cooldown_seconds()
        self.debouncer = GestureDebouncer(cooldown_seconds=cooldown)

        # Initialize hold time validator
        min_hold_time = self.config_manager.get_min_hold_time()
        self.hold_validator = HoldTimeValidator(min_hold_time=min_hold_time)

        # Confidence threshold
        self.confidence_threshold = self.config_manager.get_confidence_threshold()

        # Socket server
        self.socket_server = None
        self.socket_running = False
        self.socket_thread = None

        # Callback for broadcasting events (e.g., to Flask via WebSocket)
        self.gesture_callback: Optional[Callable] = None
        self.action_callback: Optional[Callable] = None

        # Statistics
        self.stats = {
            'gestures_received': 0,
            'gestures_below_threshold': 0,
            'gestures_debounced': 0,
            'actions_triggered': 0,
            'actions_succeeded': 0,
            'actions_failed': 0
        }

        logger.info('Gesture handler initialized')

    def set_gesture_callback(self, callback: Callable):
        """
        Set callback for gesture detection events

        Args:
            callback: Function to call with gesture data
        """
        self.gesture_callback = callback
        logger.info('Gesture callback set')

    def set_action_callback(self, callback: Callable):
        """
        Set callback for action result events

        Args:
            callback: Function to call with action result
        """
        self.action_callback = callback
        logger.info('Action callback set')

    def process_gesture(self, gesture_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a gesture event

        Args:
            gesture_data: Dictionary containing gesture information
                - gesture: Gesture name (e.g., 'Open_Palm')
                - hand: Hand name ('Left' or 'Right')
                - confidence: Confidence score (0.0-1.0)
                - timestamp: Unix timestamp

        Returns:
            Action result dictionary or None if no action taken
        """
        self.stats['gestures_received'] += 1

        gesture_name = gesture_data.get('gesture')
        hand = gesture_data.get('hand')
        confidence = gesture_data.get('confidence', 0.0)

        logger.debug(f'Processing gesture: {gesture_name} ({hand}) - confidence: {confidence:.2f}')

        # Broadcast gesture detection event
        if self.gesture_callback:
            try:
                self.gesture_callback(gesture_data)
            except Exception as e:
                logger.error(f'Error in gesture callback: {e}')

        # Check confidence threshold
        if confidence < self.confidence_threshold:
            self.stats['gestures_below_threshold'] += 1
            logger.debug(
                f'Gesture below confidence threshold: {confidence:.2f} < {self.confidence_threshold}'
            )
            return None

        # Check hold time
        is_held_long_enough, hold_duration = self.hold_validator.update_gesture(
            gesture_name, hand
        )

        if not is_held_long_enough:
            logger.debug(
                f'Gesture not held long enough: {hold_duration:.2f}s '
                f'(minimum: {self.hold_validator.get_min_hold_time()}s)'
            )
            return None

        # Check debouncing
        if not self.debouncer.should_trigger(gesture_name, hand):
            self.stats['gestures_debounced'] += 1
            return None

        # Find matching mapping
        mapping = self.config_manager.get_mapping_for_gesture(gesture_name, hand)

        if not mapping:
            logger.debug(f'No mapping found for: {gesture_name} ({hand})')
            return None

        # Execute action
        logger.info(f'Executing action for gesture: {gesture_name} ({hand})')
        logger.info(f'Mapping: {mapping["name"]}')

        self.stats['actions_triggered'] += 1

        action = mapping['action']
        result = self.ha_client.execute_action(action)

        # Update statistics
        if result.get('success'):
            self.stats['actions_succeeded'] += 1
        else:
            self.stats['actions_failed'] += 1

        # Broadcast action result
        if self.action_callback:
            try:
                self.action_callback(result)
            except Exception as e:
                logger.error(f'Error in action callback: {e}')

        return result

    def start_socket_server(self, host: str = 'localhost', port: int = 5555):
        """
        Start TCP socket server to receive gesture events

        Args:
            host: Server host
            port: Server port
        """
        logger.info(f'Starting socket server on {host}:{port}')

        self.socket_running = True
        self.socket_thread = threading.Thread(
            target=self._socket_server_loop,
            args=(host, port),
            daemon=True
        )
        self.socket_thread.start()

        logger.info('Socket server started')

    def _socket_server_loop(self, host: str, port: int):
        """Socket server main loop"""
        try:
            # Create socket
            self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_server.bind((host, port))
            self.socket_server.listen(5)
            self.socket_server.settimeout(1.0)  # Timeout for clean shutdown

            logger.info(f'Socket server listening on {host}:{port}')

            while self.socket_running:
                try:
                    # Accept connection
                    conn, addr = self.socket_server.accept()
                    logger.info(f'Socket connection from {addr}')

                    # Handle connection in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_socket_client,
                        args=(conn, addr),
                        daemon=True
                    )
                    client_thread.start()

                except socket.timeout:
                    continue

                except Exception as e:
                    if self.socket_running:
                        logger.error(f'Error accepting connection: {e}')

        except Exception as e:
            logger.error(f'Socket server error: {e}')

        finally:
            if self.socket_server:
                self.socket_server.close()
            logger.info('Socket server stopped')

    def _handle_socket_client(self, conn: socket.socket, addr):
        """Handle socket client connection"""
        buffer = ''

        try:
            while self.socket_running:
                # Receive data
                data = conn.recv(1024)

                if not data:
                    break

                # Decode and add to buffer
                buffer += data.decode('utf-8')

                # Process complete messages (newline-delimited JSON)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)

                    if line.strip():
                        try:
                            # Parse JSON
                            gesture_data = json.loads(line)

                            # Process gesture
                            self.process_gesture(gesture_data)

                        except json.JSONDecodeError as e:
                            logger.error(f'Invalid JSON from socket: {e}')

                        except Exception as e:
                            logger.error(f'Error processing gesture from socket: {e}')

        except Exception as e:
            logger.error(f'Error handling socket client {addr}: {e}')

        finally:
            conn.close()
            logger.info(f'Socket connection closed: {addr}')

    def stop_socket_server(self):
        """Stop socket server"""
        logger.info('Stopping socket server...')
        self.socket_running = False

        if self.socket_thread:
            self.socket_thread.join(timeout=5)

        logger.info('Socket server stopped')

    def test_ha_connection(self) -> bool:
        """
        Test connection to Home Assistant

        Returns:
            True if successful, False otherwise
        """
        logger.info('Testing Home Assistant connection...')
        result = self.ha_client.test_connection()

        if result:
            logger.info('Home Assistant connection successful')
        else:
            logger.error('Home Assistant connection failed')

        return result

    def reload_config(self):
        """Reload configuration from file"""
        logger.info('Reloading configuration...')

        if self.config_manager.reload_config():
            # Update debouncer settings
            cooldown = self.config_manager.get_cooldown_seconds()
            self.debouncer.set_cooldown(cooldown)

            # Update hold time validator
            min_hold_time = self.config_manager.get_min_hold_time()
            self.hold_validator.set_min_hold_time(min_hold_time)

            # Update confidence threshold
            self.confidence_threshold = self.config_manager.get_confidence_threshold()

            logger.info('Configuration reloaded successfully')
        else:
            logger.error('Failed to reload configuration')

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get handler statistics

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()
        stats['debouncer'] = self.debouncer.get_statistics()
        return stats

    def reset_statistics(self):
        """Reset all statistics"""
        self.stats = {
            'gestures_received': 0,
            'gestures_below_threshold': 0,
            'gestures_debounced': 0,
            'actions_triggered': 0,
            'actions_succeeded': 0,
            'actions_failed': 0
        }
        self.debouncer.reset_statistics()
        logger.info('Statistics reset')

    def cleanup(self):
        """Cleanup resources"""
        logger.info('Cleaning up gesture handler...')

        self.stop_socket_server()
        self.ha_client.close()

        logger.info('Gesture handler cleanup complete')
