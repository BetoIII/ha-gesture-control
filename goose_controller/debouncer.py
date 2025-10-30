"""
Gesture Debouncer

Prevents duplicate gesture triggers by tracking recent gestures and
enforcing cooldown periods
"""

import time
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class GestureDebouncer:
    """Manages debouncing for gesture events"""

    def __init__(self, cooldown_seconds: float = 2.0):
        """
        Initialize debouncer

        Args:
            cooldown_seconds: Cooldown period in seconds
        """
        self.cooldown_seconds = cooldown_seconds

        # Track last trigger time for each gesture+hand combination
        # Key: "gesture_name|hand_name"
        # Value: timestamp of last trigger
        self.last_triggers: Dict[str, float] = {}

        # Statistics
        self.total_gestures = 0
        self.debounced_gestures = 0
        self.triggered_gestures = 0

    def should_trigger(self, gesture: str, hand: str) -> bool:
        """
        Check if a gesture should trigger an action

        Args:
            gesture: Gesture name (e.g., 'Open_Palm')
            hand: Hand name ('Left' or 'Right')

        Returns:
            True if gesture should trigger, False if debounced
        """
        self.total_gestures += 1

        # Create unique key for gesture+hand combination
        key = f"{gesture}|{hand}"

        # Get current time
        current_time = time.time()

        # Check if gesture was recently triggered
        if key in self.last_triggers:
            last_trigger_time = self.last_triggers[key]
            time_since_last = current_time - last_trigger_time

            if time_since_last < self.cooldown_seconds:
                # Still in cooldown period
                self.debounced_gestures += 1
                logger.debug(
                    f'Debounced: {gesture} ({hand}) - '
                    f'{time_since_last:.2f}s since last trigger '
                    f'(cooldown: {self.cooldown_seconds}s)'
                )
                return False

        # Update last trigger time
        self.last_triggers[key] = current_time
        self.triggered_gestures += 1

        logger.debug(f'Trigger allowed: {gesture} ({hand})')
        return True

    def reset(self):
        """Reset all debouncing state"""
        self.last_triggers.clear()
        logger.info('Debouncer state reset')

    def reset_gesture(self, gesture: str, hand: str):
        """
        Reset debouncing for a specific gesture

        Args:
            gesture: Gesture name
            hand: Hand name
        """
        key = f"{gesture}|{hand}"
        if key in self.last_triggers:
            del self.last_triggers[key]
            logger.debug(f'Reset debounce state for: {gesture} ({hand})')

    def set_cooldown(self, cooldown_seconds: float):
        """
        Set cooldown period

        Args:
            cooldown_seconds: New cooldown period in seconds
        """
        old_cooldown = self.cooldown_seconds
        self.cooldown_seconds = cooldown_seconds
        logger.info(f'Cooldown period changed: {old_cooldown}s -> {cooldown_seconds}s')

    def get_cooldown(self) -> float:
        """Get current cooldown period"""
        return self.cooldown_seconds

    def get_time_since_last_trigger(self, gesture: str, hand: str) -> Optional[float]:
        """
        Get time since last trigger for a gesture

        Args:
            gesture: Gesture name
            hand: Hand name

        Returns:
            Time in seconds since last trigger, or None if never triggered
        """
        key = f"{gesture}|{hand}"

        if key not in self.last_triggers:
            return None

        return time.time() - self.last_triggers[key]

    def get_remaining_cooldown(self, gesture: str, hand: str) -> float:
        """
        Get remaining cooldown time for a gesture

        Args:
            gesture: Gesture name
            hand: Hand name

        Returns:
            Remaining cooldown time in seconds (0 if not in cooldown)
        """
        time_since = self.get_time_since_last_trigger(gesture, hand)

        if time_since is None:
            return 0.0

        remaining = self.cooldown_seconds - time_since
        return max(0.0, remaining)

    def get_statistics(self) -> Dict[str, int]:
        """
        Get debouncing statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'total_gestures': self.total_gestures,
            'triggered_gestures': self.triggered_gestures,
            'debounced_gestures': self.debounced_gestures,
            'debounce_rate': (
                self.debounced_gestures / self.total_gestures * 100
                if self.total_gestures > 0 else 0.0
            )
        }

    def reset_statistics(self):
        """Reset statistics counters"""
        self.total_gestures = 0
        self.debounced_gestures = 0
        self.triggered_gestures = 0
        logger.info('Debouncer statistics reset')

    def get_active_cooldowns(self) -> Dict[str, float]:
        """
        Get all gestures currently in cooldown

        Returns:
            Dictionary mapping gesture keys to remaining cooldown time
        """
        current_time = time.time()
        active = {}

        for key, last_trigger_time in self.last_triggers.items():
            time_since = current_time - last_trigger_time
            remaining = self.cooldown_seconds - time_since

            if remaining > 0:
                active[key] = remaining

        return active


class HoldTimeValidator:
    """Validates that gestures are held for minimum duration"""

    def __init__(self, min_hold_time: float = 0.5):
        """
        Initialize hold time validator

        Args:
            min_hold_time: Minimum hold time in seconds
        """
        self.min_hold_time = min_hold_time

        # Track when each gesture first appeared
        # Key: "gesture_name|hand_name"
        # Value: timestamp when first detected
        self.gesture_start_times: Dict[str, float] = {}

    def update_gesture(self, gesture: str, hand: str) -> Tuple[bool, float]:
        """
        Update gesture state and check if held long enough

        Args:
            gesture: Gesture name
            hand: Hand name

        Returns:
            Tuple of (is_valid, hold_duration)
            - is_valid: True if gesture held long enough
            - hold_duration: How long gesture has been held
        """
        key = f"{gesture}|{hand}"
        current_time = time.time()

        # Check if this is a new gesture
        if key not in self.gesture_start_times:
            # Record start time
            self.gesture_start_times[key] = current_time
            return False, 0.0

        # Calculate hold duration
        hold_duration = current_time - self.gesture_start_times[key]

        # Check if held long enough
        is_valid = hold_duration >= self.min_hold_time

        return is_valid, hold_duration

    def clear_gesture(self, gesture: str, hand: str):
        """
        Clear gesture state (call when gesture is no longer detected)

        Args:
            gesture: Gesture name
            hand: Hand name
        """
        key = f"{gesture}|{hand}"
        if key in self.gesture_start_times:
            del self.gesture_start_times[key]

    def set_min_hold_time(self, min_hold_time: float):
        """Set minimum hold time"""
        self.min_hold_time = min_hold_time

    def get_min_hold_time(self) -> float:
        """Get minimum hold time"""
        return self.min_hold_time

    def reset(self):
        """Reset all hold time state"""
        self.gesture_start_times.clear()
