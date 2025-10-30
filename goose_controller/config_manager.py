"""
Configuration Manager for HA Gesture Control

Loads, validates, and manages gesture configuration from YAML file
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages gesture control configuration"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to configuration file (defaults to config/gesture_config.yaml)
        """
        if config_path is None:
            # Default to config/gesture_config.yaml in project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / 'config' / 'gesture_config.yaml'

        self.config_path = Path(config_path)
        self.config = None
        self.gesture_mappings = []
        self.ha_config = {}
        self.gesture_settings = {}

    def load_config(self) -> bool:
        """
        Load configuration from YAML file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config_path.exists():
                logger.error(f'Configuration file not found: {self.config_path}')
                return False

            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            # Extract configuration sections
            self.ha_config = self.config.get('homeassistant', {})
            self.gesture_settings = self.config.get('gesture_recognition', {})
            self.gesture_mappings = self.config.get('gesture_mappings', [])

            logger.info(f'Configuration loaded successfully from {self.config_path}')
            logger.info(f'Loaded {len(self.gesture_mappings)} gesture mappings')

            # Validate configuration
            if not self.validate_config():
                logger.warning('Configuration validation failed')
                return False

            return True

        except yaml.YAMLError as e:
            logger.error(f'Failed to parse YAML configuration: {e}')
            return False

        except Exception as e:
            logger.error(f'Failed to load configuration: {e}')
            return False

    def validate_config(self) -> bool:
        """
        Validate configuration structure and values

        Returns:
            True if valid, False otherwise
        """
        # Check required sections
        if not self.ha_config:
            logger.error('Missing homeassistant configuration section')
            return False

        if not self.gesture_settings:
            logger.error('Missing gesture_recognition configuration section')
            return False

        # Validate Home Assistant config
        required_ha_fields = ['mcp_url', 'token_env_var']
        for field in required_ha_fields:
            if field not in self.ha_config:
                logger.error(f'Missing required Home Assistant config field: {field}')
                return False

        # Validate gesture settings
        confidence_threshold = self.gesture_settings.get('confidence_threshold', 0.8)
        if not (0.0 <= confidence_threshold <= 1.0):
            logger.error(f'Invalid confidence_threshold: {confidence_threshold} (must be 0.0-1.0)')
            return False

        # Validate gesture mappings
        valid_gestures = [
            'Closed_Fist', 'Open_Palm', 'Pointing_Up',
            'Thumb_Down', 'Thumb_Up', 'Victory', 'ILoveYou'
        ]

        for i, mapping in enumerate(self.gesture_mappings):
            # Check required fields
            required_fields = ['name', 'gesture', 'hand', 'action']
            for field in required_fields:
                if field not in mapping:
                    logger.error(f'Mapping {i}: Missing required field: {field}')
                    return False

            # Validate gesture name
            if mapping['gesture'] not in valid_gestures:
                logger.warning(f'Mapping {i}: Unknown gesture: {mapping["gesture"]}')

            # Validate hand
            valid_hands = ['Left', 'Right', 'Either']
            if mapping['hand'] not in valid_hands:
                logger.error(f'Mapping {i}: Invalid hand value: {mapping["hand"]}')
                return False

            # Validate action structure
            action = mapping['action']
            if 'entity_id' not in action or 'service' not in action:
                logger.error(f'Mapping {i}: Action missing entity_id or service')
                return False

        logger.info('Configuration validation passed')
        return True

    def save_config(self) -> bool:
        """
        Save current configuration to YAML file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup
            backup_path = Path(str(self.config_path) + '.bak')
            if self.config_path.exists():
                import shutil
                shutil.copy2(self.config_path, backup_path)
                logger.info(f'Created backup: {backup_path}')

            # Update config dictionary
            self.config['homeassistant'] = self.ha_config
            self.config['gesture_recognition'] = self.gesture_settings
            self.config['gesture_mappings'] = self.gesture_mappings

            # Write to file
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

            logger.info(f'Configuration saved to {self.config_path}')
            return True

        except Exception as e:
            logger.error(f'Failed to save configuration: {e}')
            return False

    def get_gesture_mappings(self) -> List[Dict[str, Any]]:
        """Get all gesture mappings"""
        return self.gesture_mappings

    def get_mapping_for_gesture(self, gesture: str, hand: str) -> Optional[Dict[str, Any]]:
        """
        Find mapping for a specific gesture and hand

        Args:
            gesture: Gesture name (e.g., 'Open_Palm')
            hand: Hand name ('Left' or 'Right')

        Returns:
            Matching mapping dictionary or None
        """
        for mapping in self.gesture_mappings:
            # Check if gesture matches
            if mapping['gesture'] != gesture:
                continue

            # Check if hand matches
            mapping_hand = mapping['hand']
            if mapping_hand == 'Either' or mapping_hand == hand:
                return mapping

        return None

    def add_gesture_mapping(self, mapping: Dict[str, Any]) -> bool:
        """
        Add a new gesture mapping

        Args:
            mapping: Gesture mapping dictionary

        Returns:
            True if successful, False otherwise
        """
        # Validate mapping
        required_fields = ['name', 'gesture', 'hand', 'action']
        for field in required_fields:
            if field not in mapping:
                logger.error(f'Cannot add mapping: Missing required field: {field}')
                return False

        self.gesture_mappings.append(mapping)
        logger.info(f'Added gesture mapping: {mapping["name"]}')
        return True

    def remove_gesture_mapping(self, index: int) -> bool:
        """
        Remove a gesture mapping by index

        Args:
            index: Index of mapping to remove

        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.gesture_mappings):
            removed = self.gesture_mappings.pop(index)
            logger.info(f'Removed gesture mapping: {removed["name"]}')
            return True

        logger.error(f'Cannot remove mapping: Invalid index {index}')
        return False

    def update_gesture_mapping(self, index: int, mapping: Dict[str, Any]) -> bool:
        """
        Update a gesture mapping

        Args:
            index: Index of mapping to update
            mapping: New mapping dictionary

        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.gesture_mappings):
            self.gesture_mappings[index] = mapping
            logger.info(f'Updated gesture mapping at index {index}')
            return True

        logger.error(f'Cannot update mapping: Invalid index {index}')
        return False

    def get_ha_config(self) -> Dict[str, Any]:
        """Get Home Assistant configuration"""
        return self.ha_config

    def get_gesture_settings(self) -> Dict[str, Any]:
        """Get gesture recognition settings"""
        return self.gesture_settings

    def get_confidence_threshold(self) -> float:
        """Get confidence threshold"""
        return self.gesture_settings.get('confidence_threshold', 0.8)

    def get_cooldown_seconds(self) -> float:
        """Get cooldown period in seconds"""
        return self.gesture_settings.get('cooldown_seconds', 2.0)

    def get_min_hold_time(self) -> float:
        """Get minimum gesture hold time"""
        return self.gesture_settings.get('min_hold_time', 0.5)

    def reload_config(self) -> bool:
        """
        Reload configuration from file

        Returns:
            True if successful, False otherwise
        """
        logger.info('Reloading configuration...')
        return self.load_config()
