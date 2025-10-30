"""
Home Assistant MCP Client

Integrates with Home Assistant using the Model Context Protocol (MCP)
for executing device actions
"""

import os
import sys
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config.constants import HA_MIN_TOKEN_LENGTH, HA_REQUEST_TIMEOUT
except ImportError:
    # Fallback to hardcoded values if constants not available
    HA_MIN_TOKEN_LENGTH = 50
    HA_REQUEST_TIMEOUT = 30.0

logger = logging.getLogger(__name__)


def load_token_securely(token_env_var: str) -> str:
    """
    Load token with proper validation and error handling.

    Args:
        token_env_var: Environment variable name containing the token

    Returns:
        The token string

    Raises:
        ValueError: If token is not set or appears invalid
    """
    token = os.getenv(token_env_var)

    if not token:
        raise ValueError(
            f'Security: {token_env_var} not set. '
            'Please configure your Home Assistant token.'
        )

    if len(token) < HA_MIN_TOKEN_LENGTH:  # HA tokens are typically ~180+ chars
        logger.warning(f'{token_env_var} appears to be too short for a valid HA token')

    # Never log the actual token - only log metadata
    logger.info(f'Token loaded from {token_env_var} (length: {len(token)})')

    return token


class HomeAssistantMCPClient:
    """MCP client for Home Assistant integration"""

    def __init__(self, mcp_url: str, token_env_var: str = 'HA_TOKEN'):
        """
        Initialize Home Assistant MCP client

        Args:
            mcp_url: Home Assistant MCP server URL (SSE endpoint)
            token_env_var: Environment variable name containing access token

        Raises:
            ValueError: If token is not set or appears invalid
        """
        self.mcp_url = mcp_url
        self.token = load_token_securely(token_env_var)

        # Extract base URL from MCP URL
        # Example: http://localhost:8123/mcp_server/sse -> http://localhost:8123
        self.base_url = '/'.join(mcp_url.split('/')[:3])

        logger.info(f'Home Assistant MCP client initialized')
        logger.info(f'Base URL: {self.base_url}')

        # HTTP client
        self.http_client = None

    async def initialize(self):
        """Initialize async HTTP client"""
        self.http_client = httpx.AsyncClient(
            headers={
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            },
            timeout=HA_REQUEST_TIMEOUT
        )
        logger.info('HTTP client initialized')

    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info('HTTP client closed')

    async def call_service(self, domain: str, service: str, entity_id: str,
                          data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call a Home Assistant service

        Args:
            domain: Service domain (e.g., 'light', 'switch')
            service: Service name (e.g., 'turn_on', 'turn_off')
            entity_id: Entity ID (e.g., 'light.living_room')
            data: Additional service data (optional)

        Returns:
            Result dictionary with success status and message
        """
        if not self.http_client:
            await self.initialize()

        try:
            # Build service call URL
            url = f'{self.base_url}/api/services/{domain}/{service}'

            # Build payload
            payload = {
                'entity_id': entity_id
            }

            if data:
                payload.update(data)

            logger.info(f'Calling service: {domain}.{service} on {entity_id}')
            logger.debug(f'Payload: {payload}')

            # Make REST API call
            response = await self.http_client.post(url, json=payload)

            # Check response
            if response.status_code == 200:
                logger.info(f'Service call successful: {domain}.{service}')
                return {
                    'success': True,
                    'entity_id': entity_id,
                    'service': f'{domain}.{service}',
                    'message': f'{entity_id} - {service} executed successfully',
                    'response': response.json()
                }
            else:
                error_msg = f'Service call failed: HTTP {response.status_code}'
                logger.error(error_msg)
                logger.error(f'Response: {response.text}')

                return {
                    'success': False,
                    'entity_id': entity_id,
                    'service': f'{domain}.{service}',
                    'error': error_msg,
                    'status_code': response.status_code
                }

        except httpx.TimeoutException:
            error_msg = 'Service call timed out'
            logger.error(f'{error_msg}: {domain}.{service}')
            return {
                'success': False,
                'entity_id': entity_id,
                'service': f'{domain}.{service}',
                'error': error_msg
            }

        except httpx.HTTPError as e:
            error_msg = f'HTTP error: {str(e)}'
            logger.error(f'{error_msg}: {domain}.{service}')
            return {
                'success': False,
                'entity_id': entity_id,
                'service': f'{domain}.{service}',
                'error': error_msg
            }

        except Exception as e:
            error_msg = f'Unexpected error: {str(e)}'
            logger.error(f'{error_msg}: {domain}.{service}')
            return {
                'success': False,
                'entity_id': entity_id,
                'service': f'{domain}.{service}',
                'error': error_msg
            }

    async def turn_on(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        """
        Turn on a device

        Args:
            entity_id: Entity ID
            **kwargs: Additional service data (brightness, color, etc.)

        Returns:
            Result dictionary
        """
        domain = entity_id.split('.')[0]
        return await self.call_service(domain, 'turn_on', entity_id, kwargs or None)

    async def turn_off(self, entity_id: str) -> Dict[str, Any]:
        """
        Turn off a device

        Args:
            entity_id: Entity ID

        Returns:
            Result dictionary
        """
        domain = entity_id.split('.')[0]
        return await self.call_service(domain, 'turn_off', entity_id)

    async def toggle(self, entity_id: str) -> Dict[str, Any]:
        """
        Toggle a device

        Args:
            entity_id: Entity ID

        Returns:
            Result dictionary
        """
        domain = entity_id.split('.')[0]
        return await self.call_service(domain, 'toggle', entity_id)

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action from configuration

        Args:
            action: Action dictionary from config with:
                - entity_id: Entity ID
                - service: Service name (e.g., 'turn_on')
                - data: Optional service data

        Returns:
            Result dictionary
        """
        entity_id = action.get('entity_id')
        service = action.get('service')
        data = action.get('data', {})

        if not entity_id or not service:
            return {
                'success': False,
                'error': 'Missing entity_id or service in action'
            }

        # Extract domain from entity_id
        domain = entity_id.split('.')[0]

        return await self.call_service(domain, service, entity_id, data)

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get state of an entity

        Args:
            entity_id: Entity ID

        Returns:
            State dictionary or None
        """
        if not self.http_client:
            await self.initialize()

        try:
            url = f'{self.base_url}/api/states/{entity_id}'
            response = await self.http_client.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f'Failed to get state for {entity_id}: HTTP {response.status_code}')
                return None

        except Exception as e:
            logger.error(f'Error getting state for {entity_id}: {e}')
            return None

    async def test_connection(self) -> bool:
        """
        Test connection to Home Assistant

        Returns:
            True if connection successful, False otherwise
        """
        if not self.http_client:
            await self.initialize()

        try:
            url = f'{self.base_url}/api/'
            response = await self.http_client.get(url)

            if response.status_code == 200:
                data = response.json()
                logger.info(f'Connected to Home Assistant: {data.get("message", "OK")}')
                return True
            else:
                logger.error(f'Failed to connect to Home Assistant: HTTP {response.status_code}')
                return False

        except Exception as e:
            logger.error(f'Connection test failed: {e}')
            return False


class SyncHomeAssistantClient:
    """Synchronous wrapper for Home Assistant MCP client"""

    def __init__(self, mcp_url: str, token_env_var: str = 'HA_TOKEN'):
        """
        Initialize synchronous client

        Args:
            mcp_url: Home Assistant MCP server URL
            token_env_var: Environment variable name containing access token
        """
        self.client = HomeAssistantMCPClient(mcp_url, token_env_var)
        self.loop = None

    def _get_or_create_loop(self):
        """Get or create event loop"""
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        return self.loop

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action synchronously

        Args:
            action: Action dictionary

        Returns:
            Result dictionary
        """
        loop = self._get_or_create_loop()
        return loop.run_until_complete(self.client.execute_action(action))

    def test_connection(self) -> bool:
        """Test connection synchronously"""
        loop = self._get_or_create_loop()
        return loop.run_until_complete(self.client.test_connection())

    def close(self):
        """Close client"""
        if self.loop:
            self.loop.run_until_complete(self.client.close())
            self.loop.close()
