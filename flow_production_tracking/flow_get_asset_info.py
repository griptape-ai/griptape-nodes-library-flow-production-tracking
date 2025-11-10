from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.events.node_events import ListParametersOnNodeRequest
from griptape_nodes.retained_mode.events.parameter_events import (
    AddParameterToNodeRequest,
    GetConnectionsForParameterRequest,
    GetConnectionsForParameterResultSuccess,
    RemoveParameterFromNodeRequest,
    SetParameterValueRequest,
)
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger


class FlowGetAssetInfo(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="asset_id",
                default_value=None,
                output_type="str",
                tooltip="The ID of the asset to get information for.",
                placeholder_text="Enter asset ID (e.g., 1234)",
                converters=[lambda x: str(int(x.replace(",", "").replace(" ", ""))) if x else None],
            )
        )

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="asset_url",
                default_value="",
                tooltip="The URL to view the asset in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the asset",
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value="",
                tooltip="The ID of the project this asset belongs to.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "asset_id" and value:
            self._update_asset_url()
        return super().after_value_set(parameter, value)

    def _update_asset_url(self) -> None:
        """Update the asset URL based on the current asset_id."""
        asset_id = self.get_parameter_value("asset_id")

        if not asset_id:
            return

        try:
            base_url = self._get_shotgrid_config()["base_url"]
            asset_url = f"{base_url.rstrip('/')}/detail/Asset/{asset_id}"
        except Exception:
            asset_url = f"https://shotgrid.autodesk.com/detail/Asset/{asset_id}"

        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name="asset_url", value=asset_url, node_name=self.name)
        )
        self.parameter_output_values["asset_url"] = asset_url
        self.publish_update_to_parameter("asset_url", asset_url)

    def _get_current_parameter_names(self) -> set[str]:
        """Get the actual parameter names that exist on this node."""
        try:
            result = GriptapeNodes.handle_request(ListParametersOnNodeRequest(node_name=self.name))
            if hasattr(result, "parameter_names"):
                return set(result.parameter_names)
            return set()
        except Exception as e:
            logger.warning(f"{self.name}: Error getting parameter names: {e}")
            return set()

    def _is_parameter_connected(self, param_name: str) -> bool:
        """Check if a parameter has any connections (incoming or outgoing)."""
        try:
            result = GriptapeNodes.handle_request(
                GetConnectionsForParameterRequest(parameter_name=param_name, node_name=self.name)
            )
            if isinstance(result, GetConnectionsForParameterResultSuccess):
                return result.has_incoming_connections() or result.has_outgoing_connections()
            return False
        except Exception as e:
            logger.warning(f"{self.name}: Error checking connections for '{param_name}': {e}")
            return True

    def _sync_dynamic_parameters(self, attributes: dict) -> None:
        """Sync dynamic output parameters with asset attributes."""
        static_params = {
            "asset_url",
            "asset_data",
            "asset_id",
            "project_id",
            "exec_out",
            "exec_in",
            "execution_environment",
            "job_group",
        }

        all_current_params = self._get_current_parameter_names()
        current_dynamic_params = all_current_params - static_params
        desired_params = set(attributes.keys())

        logger.info(f"{self.name}: Current dynamic params: {current_dynamic_params}")
        logger.info(f"{self.name}: Desired params: {desired_params}")

        # Update existing parameters
        for param_name in current_dynamic_params & desired_params:
            attr_value = attributes[param_name]
            value_str = str(attr_value) if attr_value is not None else ""

            current_value = self.parameter_output_values.get(param_name, "")
            if current_value != value_str:
                GriptapeNodes.handle_request(
                    SetParameterValueRequest(parameter_name=param_name, value=value_str, node_name=self.name)
                )
                self.parameter_output_values[param_name] = value_str
                self.publish_update_to_parameter(param_name, value_str)

        # Add new parameters
        for param_name in desired_params - current_dynamic_params:
            attr_value = attributes[param_name]
            value_str = str(attr_value) if attr_value is not None else ""

            GriptapeNodes.handle_request(
                AddParameterToNodeRequest(
                    node_name=self.name,
                    parameter_name=param_name,
                    default_value=value_str,
                    tooltip=f"Asset attribute: {param_name}",
                    type="str",
                    mode_allowed_output=True,
                    mode_allowed_input=False,
                    mode_allowed_property=False,
                    is_user_defined=True,
                )
            )

            self.parameter_output_values[param_name] = value_str
            self.publish_update_to_parameter(param_name, value_str)

        # Delete parameters that are no longer in the data (only if not connected)
        for param_name in current_dynamic_params - desired_params:
            is_connected = self._is_parameter_connected(param_name)

            if is_connected:
                logger.info(f"{self.name}: Skipping deletion of '{param_name}' - parameter is connected")
                continue

            GriptapeNodes.handle_request(RemoveParameterFromNodeRequest(parameter_name=param_name, node_name=self.name))

            if param_name in self.parameter_output_values:
                del self.parameter_output_values[param_name]

    def process(self) -> None:
        """Get asset information from ShotGrid."""
        asset_id = self.get_parameter_value("asset_id")

        if not asset_id:
            logger.error(f"{self.name}: Asset ID is required")
            return

        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Default fields for assets
            fields = "id,name,code,description,created_at,updated_at,sg_asset_type,sg_status_list,project,image"
            url = f"{base_url}api/v1/entity/assets/{asset_id}"
            params = {"fields": fields}
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                asset_data = data.get("data", {})

                if not asset_data:
                    logger.error(f"{self.name}: No asset data returned")
                    return

                # Extract attributes
                attributes = asset_data.get("attributes", {})

                # Extract project_id from relationships
                relationships = asset_data.get("relationships", {})
                project_id = ""
                if relationships.get("project"):
                    project_data = relationships["project"].get("data", {})
                    if project_data:
                        project_id = str(project_data.get("id", ""))

                # Update asset_data output
                GriptapeNodes.handle_request(
                    SetParameterValueRequest(parameter_name="asset_data", value=asset_data, node_name=self.name)
                )
                self.parameter_output_values["asset_data"] = asset_data
                self.publish_update_to_parameter("asset_data", asset_data)

                # Update project_id output
                GriptapeNodes.handle_request(
                    SetParameterValueRequest(parameter_name="project_id", value=project_id, node_name=self.name)
                )
                self.parameter_output_values["project_id"] = project_id
                self.publish_update_to_parameter("project_id", project_id)

                # Sync dynamic parameters with asset attributes
                self._sync_dynamic_parameters(attributes)

                # Update asset URL
                self._update_asset_url()

                logger.info(f"{self.name}: Successfully retrieved asset {asset_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error getting asset: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error getting asset: {e}")
