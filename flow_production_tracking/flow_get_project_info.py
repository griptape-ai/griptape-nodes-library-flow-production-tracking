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


class FlowGetProjectInfo(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to get information for.",
                placeholder_text="Enter project ID (e.g., 1234)",
                converters=[lambda x: str(int(x.replace(",", "").replace(" ", ""))) if x else None],
            )
        )

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="project_url",
                default_value="",
                tooltip="The URL to view the project in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="project_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the project",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "project_id" and value:
            self._update_project_url()
        return super().after_value_set(parameter, value)

    def _update_project_url(self) -> None:
        """Update the project URL based on the current project_id."""
        project_id = self.get_parameter_value("project_id")

        if not project_id:
            return

        try:
            base_url = self._get_shotgrid_config()["base_url"]
            project_url = f"{base_url.rstrip('/')}/detail/Project/{project_id}"
        except Exception:
            project_url = f"https://shotgrid.autodesk.com/detail/Project/{project_id}"

        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name="project_url", value=project_url, node_name=self.name)
        )
        self.parameter_output_values["project_url"] = project_url
        self.publish_update_to_parameter("project_url", project_url)

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
        """Sync dynamic output parameters with project attributes."""
        static_params = {
            "project_url",
            "project_data",
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
                    tooltip=f"Project attribute: {param_name}",
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
        """Get project information from ShotGrid."""
        project_id = self.get_parameter_value("project_id")

        if not project_id:
            logger.error(f"{self.name}: Project ID is required")
            return

        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Default fields for projects
            fields = "id,name,code,description,created_at,updated_at,sg_status,image"
            url = f"{base_url}api/v1/entity/projects/{project_id}"
            params = {"fields": fields}
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                project_data = data.get("data", {})

                if not project_data:
                    logger.error(f"{self.name}: No project data returned")
                    return

                # Extract attributes
                attributes = project_data.get("attributes", {})

                # Update project_data output
                GriptapeNodes.handle_request(
                    SetParameterValueRequest(parameter_name="project_data", value=project_data, node_name=self.name)
                )
                self.parameter_output_values["project_data"] = project_data
                self.publish_update_to_parameter("project_data", project_data)

                # Sync dynamic parameters with project attributes
                self._sync_dynamic_parameters(attributes)

                # Update project URL
                self._update_project_url()

                logger.info(f"{self.name}: Successfully retrieved project {project_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error getting project: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error getting project: {e}")
