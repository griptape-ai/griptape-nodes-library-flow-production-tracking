from typing import Any

from griptape_nodes.exe_types.core_types import (
    NodeMessageResult,
    Parameter,
    ParameterGroup,
    ParameterMessage,
    ParameterMode,
)
from griptape_nodes.exe_types.node_types import ControlNode
from griptape_nodes.exe_types.param_types.parameter_button import ParameterButton
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload, OnClickMessageResultPayload


class AutodeskFlowConfiguration(ControlNode):
    """Configuration node for Autodesk Flow Production Tracking settings."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Step 1: ShotGrid URL
        with ParameterGroup(name="Step_1_Autodesk_Flow_URL") as url_group:
            ParameterString(
                name="autodesk_flow_url",
                default_value=GriptapeNodes.SecretsManager().get_secret("SHOTGRID_URL") or "",
                tooltip="Your Autodesk Flow instance URL (e.g., https://your-company.shotgrid.autodesk.com/)",
                display_name="Autodesk Flow URL",
                placeholder_text="https://your-company.shotgrid.autodesk.com/",
            )

        self.add_node_element(url_group)

        # Step 2: Script Name
        with ParameterGroup(name="Step_2_Script Name") as script_group:
            ParameterMessage(
                name="step2_message",
                value="Set the name of your Autodesk Flow script. \nThis should match the script name you created in Autodesk Flow Admin > Scripts.\n\nIf you haven't created a script yet, you need to:\n1. Go to Autodesk Flow Admin > Scripts\n2. Create a new script with the name you want to use\n3. Copy the script key (API key) for use in Step 3",
                button_link="https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_py_python_api_create_manage_html",
                button_text="View Flow Documentation",
                button_icon="book",
                variant="none",
            )

            ParameterString(
                name="script_name",
                default_value=GriptapeNodes.SecretsManager().get_secret("SHOTGRID_SCRIPT_NAME") or "gtn",
                tooltip="Name of the script (should match the script name in Autodesk Flow)",
                display_name="Script Name",
                placeholder_text="gtn",
            )

        self.add_node_element(script_group)

        # Step 3: API Key
        with ParameterGroup(name="Step_3_API_Key") as api_key_group:
            ParameterMessage(
                name="step3_message",
                value="Configure your SHOTGRID_API_KEY (Script Key) in the settings.\n\nIf you don't have one, you can create one in Autodesk Flow Admin > Scripts,\nor ask your administrator for one.\n\nClick the link and paste the API key into the field.",
                button_link="#settings-secrets?filter=SHOTGRID_API_KEY",
                button_text="Open Settings",
                button_icon="key",
                variant="none",
            )
        self.add_node_element(api_key_group)

        with ParameterGroup(name="Step_4_Check_Configuration") as check_config_group:
            # Step 4: Check Configuration
            ParameterButton(
                name="check_configuration",
                label="Check Configuration",
                variant="secondary",
                icon="check-circle",
                on_click=self._check_configuration,
            )

            # Check configuration button
            ParameterString(
                name="configuration_status",
                default_value="",
                multiline=True,
                is_full_width=True,
                markdown=True,
                placeholder_text="Configuration status will be displayed here after testing.",
                tooltip="Test your Autodesk Flow configuration",
                allowed_modes={ParameterMode.PROPERTY, ParameterMode.OUTPUT},
            )
        self.add_node_element(check_config_group)

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Automatically set config values when parameters are changed."""
        if parameter.name == "autodesk_flow_url":
            GriptapeNodes.SecretsManager().set_secret("SHOTGRID_URL", value)
        elif parameter.name == "script_name":
            GriptapeNodes.SecretsManager().set_secret("SHOTGRID_SCRIPT_NAME", value)

        return super().after_value_set(parameter, value)

    def _check_configuration(self, button: Button, button_details: ButtonDetailsMessagePayload) -> NodeMessageResult:  # noqa: ARG002
        """Check the Autodesk Flow configuration when button is clicked."""
        # Get configuration from parameters
        autodesk_flow_url = self.get_parameter_value("autodesk_flow_url")
        script_name = self.get_parameter_value("script_name")

        # Get API key from secrets manager
        api_key = GriptapeNodes.SecretsManager().get_secret("SHOTGRID_API_KEY")

        # Validate required fields
        if not autodesk_flow_url or not api_key:
            status_message = "❌ **Configuration incomplete**\n\n"
            status_message += "**Missing:**\n\n"
            if not autodesk_flow_url:
                status_message += "- Autodesk Flow URL is required\n"
            if not api_key:
                status_message += "- API Key is required (set via `SHOTGRID_API_KEY` in secrets)\n"
            status_message += "\n**To complete configuration:**\n\n"
            status_message += "- Set `SHOTGRID_API_KEY` in your secrets settings\n"

            self.set_parameter_value("configuration_status", status_message)
            response = OnClickMessageResultPayload(button_details=button_details)
            return NodeMessageResult(success=False, details="Configuration incomplete", response=response)
        # Clean up URL
        if not autodesk_flow_url.endswith("/"):
            autodesk_flow_url += "/"

        # Test the configuration
        try:
            import httpx

            # ShotGrid uses OAuth2 client credentials flow
            # First, get an access token
            auth_url = f"{autodesk_flow_url}api/v1/auth/access_token"
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": script_name,
                "client_secret": api_key,
            }
            auth_headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

            auth_response = httpx.post(auth_url, data=auth_data, headers=auth_headers, timeout=10)

            # Check for authentication errors
            if auth_response.status_code == 400:
                try:
                    error_data = auth_response.json()
                    if "errors" in error_data and len(error_data["errors"]) > 0:
                        error = error_data["errors"][0]
                        if "Can't authenticate script" in error.get("title", ""):
                            raise Exception(
                                f"Script '{script_name}' not found or not properly configured in Autodesk Flow. Please check:\n• Script name is correct\n• Script is created in Autodesk Flow Admin > Scripts\n• API key matches the script key in Autodesk Flow"
                            )
                        raise Exception(f"Authentication error: {error.get('title', 'Unknown error')}")
                except Exception:
                    # If we can't parse the error, use the original response
                    auth_response.raise_for_status()

            auth_response.raise_for_status()

            # Extract the access token
            auth_result = auth_response.json()
            access_token = auth_result["access_token"]

            # Now test with a simple API call using the access token
            test_url = f"{autodesk_flow_url}api/v1/entity/Project"
            test_params = {"fields": ["id", "name"], "limit": 1}
            test_headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

            response = httpx.get(test_url, params=test_params, headers=test_headers, timeout=10)
            response.raise_for_status()

            # Configuration is valid
            status_message = "## ✅ Autodesk Flow configuration is valid!\n\n"
            status_message += "| Field | Value |\n"
            status_message += "|-------|-------|\n"
            status_message += f"| URL | `{autodesk_flow_url}` |\n"
            status_message += f"| API Key | `{api_key[:8]}...{api_key[-4:]}` |\n"
            status_message += f"| Script | `{script_name}` |\n"
            status_message += "| Auth | API key |\n"
            status_message += "\n🎉 You can now use other Autodesk Flow nodes!"

            self.set_parameter_value("configuration_status", status_message)
            response = OnClickMessageResultPayload(button_details=button_details)
            return NodeMessageResult(success=True, details="Configuration test successful", response=response)

        except Exception as e:
            status_message = "❌ **Configuration test failed**\n\n"
            status_message += f"```\n{e!s}\n```\n\n"
            status_message += "**Please check:**\n\n"
            status_message += "- Autodesk Flow URL is correct\n"
            status_message += "- API Key is valid\n"
            status_message += "- Script name matches Autodesk Flow settings\n"
            status_message += "- Network connection is working"

            self.set_parameter_value("configuration_status", status_message)
            response = OnClickMessageResultPayload(button_details=button_details)
            return NodeMessageResult(success=False, details=f"Configuration test failed: {e!s}", response=response)

    def process(self) -> None:
        """Process the Autodesk Flow configuration."""
        # Configuration is now handled by the button click
        # This method is kept for compatibility but doesn't do anything
