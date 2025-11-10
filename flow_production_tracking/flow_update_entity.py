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
from griptape_nodes.traits.options import Options

# Common ShotGrid entity types with "Unknown" option for auto-detection
ENTITY_TYPES = [
    "Unknown",
    "Asset",
    "Shot",
    "Sequence",
    "Project",
    "Task",
    "HumanUser",
    "Note",
    "Playlist",
    "Version",
]


class FlowUpdateEntity(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="entity_type",
                default_value=ENTITY_TYPES[0],  # Default to "Unknown"
                tooltip="The type of entity to update. Select 'Unknown' to auto-detect from entity_id.",
                placeholder_text="Select entity type or choose 'Unknown' for auto-detection",
                traits={
                    Options(choices=ENTITY_TYPES),
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_id",
                default_value=None,
                tooltip="The ID of the entity to update.",
                placeholder_text="Enter entity ID (e.g., 1234)",
                converters=[lambda x: str(int(x.replace(",", "").replace(" ", ""))) if x else None],
            )
        )
        # Output parameters
        self.add_parameter(
            ParameterString(
                name="entity_url",
                default_value="",
                tooltip="The URL to view the updated entity in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_entity",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the updated entity",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "entity_id" and value:
            # If entity_type is "Unknown", try to auto-detect it
            entity_type = self.get_parameter_value("entity_type")
            if entity_type == "Unknown":
                detected_type = self._detect_entity_type(str(value))
                if detected_type:
                    # Update the entity_type parameter with the detected value
                    GriptapeNodes.handle_request(
                        SetParameterValueRequest(parameter_name="entity_type", value=detected_type, node_name=self.name)
                    )
                    self.parameter_output_values["entity_type"] = detected_type
                    self.publish_update_to_parameter("entity_type", detected_type)
                    # Update entity URL with the detected type
                    self._update_entity_url()
                    # Load entity fields for the detected type
                    self._load_entity_fields(str(value), detected_type)
            else:
                # Update entity URL when entity_id changes
                self._update_entity_url()
        elif parameter.name == "entity_type" and value:
            # Update entity URL when entity_type changes
            self._update_entity_url()
            # Load entity fields when entity_type changes
            entity_id = self.get_parameter_value("entity_id")
            if entity_id and value != "Unknown":
                self._load_entity_fields(entity_id, value)
        return super().after_value_set(parameter, value)

    def _detect_entity_type(self, entity_id: str) -> str | None:
        """Attempt to auto-detect entity type by trying common entity types."""
        if not entity_id:
            return None

        # Try the most common entity types first
        common_types = ["Asset", "Shot", "Task", "Project", "HumanUser", "Sequence"]

        access_token = self._get_access_token()
        base_url = self._get_shotgrid_config()["base_url"]
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        for entity_type in common_types:
            try:
                # Convert entity type to API format
                entity_type_lower = entity_type.lower()
                if entity_type_lower == "humanuser":
                    entity_type_lower = "human_users"
                else:
                    entity_type_lower = f"{entity_type_lower}s"

                url = f"{base_url}api/v1/entity/{entity_type_lower}/{entity_id}"

                with httpx.Client() as client:
                    response = client.get(url, headers=headers, params={"fields": "id"})
                    if response.status_code == 200:
                        logger.info(f"{self.name}: Auto-detected entity type as {entity_type}")
                        return entity_type
            except Exception:
                continue

        logger.warning(f"{self.name}: Could not auto-detect entity type for ID {entity_id}")
        return None

    def _update_entity_url(self) -> None:
        """Update the entity URL based on the current entity_type and entity_id."""
        entity_type = self.get_parameter_value("entity_type")
        entity_id = self.get_parameter_value("entity_id")

        if not entity_type or not entity_id or entity_type == "Unknown":
            return

        try:
            base_url = self._get_shotgrid_config()["base_url"]
            entity_url = f"{base_url.rstrip('/')}/detail/{entity_type}/{entity_id}"
        except Exception:
            entity_url = f"https://shotgrid.autodesk.com/detail/{entity_type}/{entity_id}"

        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name="entity_url", value=entity_url, node_name=self.name)
        )
        self.parameter_output_values["entity_url"] = entity_url
        self.publish_update_to_parameter("entity_url", entity_url)

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

    def _get_default_fields(self, entity_type: str) -> str:
        """Get default fields for an entity type - matches flow_get_entity_info.py."""
        # Common fields that most entities have
        common_fields = "id,name,code,description,created_at,updated_at"

        # Entity-specific fields (same as get_entity_info)
        entity_specific = {
            "Asset": "sg_asset_type,sg_status_list,project,image",
            "Shot": "sg_sequence,project,sg_status_list,image",
            "Sequence": "project,sg_status_list,image",
            "Project": "sg_status,image",
            "Task": "content,sg_status_list,step,task_assignees,project,entity",
            "HumanUser": "email,login,sg_status_list,role,firstname,lastname,image",
            "Version": "code,description,project,entity,user,created_at,image",
            "Note": "subject,note,project,entity,user,created_at",
        }

        specific_fields = entity_specific.get(entity_type, "")
        if specific_fields:
            return f"{common_fields},{specific_fields}"
        return common_fields

    def _load_entity_fields(self, entity_id: str, entity_type: str) -> None:
        """Load entity data and create input parameters for editable fields."""
        if not entity_id or not entity_type or entity_type == "Unknown":
            return

        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Construct the API URL
            entity_type_lower = entity_type.lower()
            if entity_type_lower == "humanuser":
                entity_type_lower = "human_users"
            elif entity_type_lower.startswith("customentity"):
                num = entity_type_lower.replace("customentity", "")
                entity_type_lower = f"custom_entity_{num.zfill(2)}"
            else:
                entity_type_lower = f"{entity_type_lower}s"

            # Get default fields (same as get_entity_info)
            fields = self._get_default_fields(entity_type)
            url = f"{base_url}api/v1/entity/{entity_type_lower}/{entity_id}"
            params = {"fields": fields}
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            logger.info(f"{self.name}: Loading entity fields for {entity_type} {entity_id}")

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                entity_data = data.get("data", {})
                attributes = entity_data.get("attributes", {})

                if not attributes:
                    logger.warning(f"{self.name}: No attributes found for {entity_type} {entity_id}")
                    return

                # Filter out read-only fields that shouldn't be editable
                read_only_fields = {
                    "id",
                    "created_at",
                    "updated_at",
                }
                editable_attributes = {k: v for k, v in attributes.items() if k not in read_only_fields}

                logger.info(f"{self.name}: Found {len(editable_attributes)} editable fields for {entity_type}")

                # Sync dynamic input parameters with entity attributes
                self._sync_dynamic_parameters(editable_attributes)

                logger.info(f"{self.name}: Created/updated input parameters for {entity_type}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error loading entity fields: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error loading entity fields: {e}")

    def _sync_dynamic_parameters(self, attributes: dict) -> None:
        """Sync dynamic input parameters with entity attributes."""
        # Static parameters that should never be deleted
        static_params = {
            "entity_url",
            "updated_entity",
            "entity_type",
            "entity_id",
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
        logger.info(f"{self.name}: Parameters to create: {desired_params - current_dynamic_params}")
        logger.info(f"{self.name}: Parameters to update: {current_dynamic_params & desired_params}")
        logger.info(f"{self.name}: Parameters to delete: {current_dynamic_params - desired_params}")

        # Update existing parameters that are in both lists
        for param_name in current_dynamic_params & desired_params:
            attr_value = attributes[param_name]
            value_str = str(attr_value) if attr_value is not None else ""

            current_value = self.parameter_output_values.get(param_name, "")
            if current_value != value_str:
                logger.info(f"{self.name}: Updating '{param_name}' placeholder from '{current_value}' to '{value_str}'")
                GriptapeNodes.handle_request(
                    SetParameterValueRequest(parameter_name=param_name, value=value_str, node_name=self.name)
                )
                self.parameter_output_values[param_name] = value_str
                self.publish_update_to_parameter(param_name, value_str)

        # Add new parameters that don't exist yet (as INPUT parameters)
        for param_name in desired_params - current_dynamic_params:
            attr_value = attributes[param_name]
            current_value_str = str(attr_value) if attr_value is not None else ""

            GriptapeNodes.handle_request(
                AddParameterToNodeRequest(
                    node_name=self.name,
                    parameter_name=param_name,
                    default_value=None,
                    tooltip=f"Update {param_name} (leave empty to keep current value)",
                    type="str",
                    mode_allowed_output=False,
                    mode_allowed_input=True,
                    mode_allowed_property=False,
                    is_user_defined=True,
                    ui_options={"placeholder_text": current_value_str},
                )
            )

            self.parameter_output_values[param_name] = None
            logger.info(f"{self.name}: Created input parameter '{param_name}' with placeholder '{current_value_str}'")

        # Delete parameters that are no longer in the data (only if not connected)
        for param_name in current_dynamic_params - desired_params:
            is_connected = self._is_parameter_connected(param_name)

            if is_connected:
                logger.info(f"{self.name}: Skipping deletion of '{param_name}' - parameter is connected")
                continue

            GriptapeNodes.handle_request(RemoveParameterFromNodeRequest(parameter_name=param_name, node_name=self.name))

            if param_name in self.parameter_output_values:
                del self.parameter_output_values[param_name]

            logger.info(f"{self.name}: Deleted parameter '{param_name}'")

    def process(self) -> None:
        """Update entity information in ShotGrid."""
        # Get and validate input parameters
        entity_type = self.get_parameter_value("entity_type")
        entity_id = self.get_parameter_value("entity_id")

        if not entity_id:
            logger.error(f"{self.name}: Entity ID is required")
            return

        # Auto-detect entity type if "Unknown" is selected
        if entity_type == "Unknown":
            logger.info(f"{self.name}: Entity type is 'Unknown', attempting auto-detection...")
            entity_type = self._detect_entity_type(entity_id)
            if not entity_type:
                logger.error(f"{self.name}: Could not auto-detect entity type for ID {entity_id}")
                return

            # Update the entity_type parameter with the detected value
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="entity_type", value=entity_type, node_name=self.name)
            )
            self.parameter_output_values["entity_type"] = entity_type
            self.publish_update_to_parameter("entity_type", entity_type)

        # Validate entity type
        if entity_type != "Unknown" and entity_type not in ENTITY_TYPES:
            logger.warning(f"{self.name}: Unknown entity type '{entity_type}', proceeding anyway")

        # Collect update data from dynamic parameters (non-None values only)
        static_params = {
            "entity_url",
            "updated_entity",
            "entity_type",
            "entity_id",
            "exec_out",
            "exec_in",
            "execution_environment",
            "job_group",
        }

        update_data = {}
        all_params = self._get_current_parameter_names()
        dynamic_params = all_params - static_params

        for param_name in dynamic_params:
            param_value = self.get_parameter_value(param_name)
            # Only include non-None values in the update
            if param_value is not None:
                update_data[param_name] = param_value
                logger.info(f"{self.name}: Will update '{param_name}' to '{param_value}'")

        if not update_data:
            logger.error(f"{self.name}: No fields to update (all dynamic parameters are None)")
            return

        try:
            # Get access token - try password auth first for better permissions
            try:
                access_token = self._get_access_token_with_password()
                logger.info(f"{self.name}: Using password authentication")
            except Exception as e:
                logger.warning(f"{self.name}: Password authentication failed, falling back to client credentials: {e}")
                access_token = self._get_access_token()

            base_url = self._get_shotgrid_config()["base_url"]

            # Construct the API URL
            entity_type_lower = entity_type.lower()
            if entity_type_lower == "humanuser":
                entity_type_lower = "human_users"
            elif entity_type_lower.startswith("customentity"):
                # Handle custom entities (CustomEntity01 -> custom_entity_01)
                num = entity_type_lower.replace("customentity", "")
                entity_type_lower = f"custom_entity_{num.zfill(2)}"
            else:
                entity_type_lower = f"{entity_type_lower}s"

            url = f"{base_url}api/v1/entity/{entity_type_lower}/{entity_id}"

            # Prepare request headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Updating {entity_type} {entity_id} with data: {update_data}")

            # Make the update request
            with httpx.Client() as client:
                response = client.put(url, headers=headers, json=update_data)
                response.raise_for_status()

                # Process the response
                data = response.json()
                updated_entity = data.get("data", {})

                if not updated_entity:
                    logger.error(f"{self.name}: No entity data returned from update")
                    return

                # Update output parameters
                GriptapeNodes.handle_request(
                    SetParameterValueRequest(parameter_name="updated_entity", value=updated_entity, node_name=self.name)
                )
                self.parameter_output_values["updated_entity"] = updated_entity
                self.publish_update_to_parameter("updated_entity", updated_entity)

                # Update entity URL
                self._update_entity_url()

                # Reload entity fields to show the updated values
                self._load_entity_fields(entity_id, entity_type)

                logger.info(f"{self.name}: Successfully updated {entity_type} {entity_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error updating entity: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error updating entity: {e}")
