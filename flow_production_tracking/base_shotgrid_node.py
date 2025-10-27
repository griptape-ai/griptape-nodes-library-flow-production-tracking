import time

import httpx

from griptape_nodes.exe_types.node_types import ControlNode
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger


class BaseShotGridNode(ControlNode):
    """Base class for all ShotGrid nodes with authentication handling."""

    # Class-level cache for the access token
    _access_token = None
    _token_expires_at = None

    SERVICE = "Autodesk"
    API_KEY_ENV_VAR = "SHOTGRID_API_KEY"
    SHOTGRID_URL_ENV_VAR = "SHOTGRID_URL"
    SCRIPT_NAME_ENV_VAR = "SHOTGRID_SCRIPT_NAME"

    def _get_access_token(self) -> str:
        """Get or refresh the access token using API key authentication."""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at and time.time() < self._token_expires_at:
            return self._access_token

        # Use API key authentication
        return self._get_access_token_api_key()

    def _get_access_token_api_key(self) -> str:
        """Get access token using API key authentication."""
        # Get configuration
        config = self._get_shotgrid_config()
        api_key = config["api_key"]
        base_url = config["base_url"]

        if not api_key:
            error_msg = "No API key available. Please configure SHOTGRID_API_KEY in settings."
            raise ValueError(error_msg)

        # Get script name from config
        script_name = GriptapeNodes.SecretsManager().get_secret(self.SCRIPT_NAME_ENV_VAR) or "Griptape Nodes"

        # Get a new token using client credentials
        auth_url = f"{base_url}api/v1/auth/access_token"
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": script_name,
            "client_secret": api_key,
        }
        auth_headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

        try:
            auth_response = httpx.post(auth_url, data=auth_data, headers=auth_headers)
            auth_response.raise_for_status()

            token_data = auth_response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour

            if not access_token:
                error_msg = "Failed to get access token from ShotGrid"
                raise ValueError(error_msg)

            # Cache the token
            self._access_token = access_token
            self._token_expires_at = time.time() + expires_in - 300  # Expire 5 minutes early

            return access_token

        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def _get_shotgrid_config(self) -> dict:
        """Get ShotGrid configuration values."""
        api_key = GriptapeNodes.SecretsManager().get_secret(self.API_KEY_ENV_VAR)
        base_url = GriptapeNodes.SecretsManager().get_secret(self.SHOTGRID_URL_ENV_VAR)
        script_name = GriptapeNodes.SecretsManager().get_secret(self.SCRIPT_NAME_ENV_VAR) or "Griptape Nodes"

        if not base_url.endswith("/"):
            base_url += "/"

        return {
            "api_key": api_key,
            "base_url": base_url,
            "script_name": script_name,
        }
