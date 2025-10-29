from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import (
    Parameter,
    ParameterMode,
)
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.events.parameter_events import SetParameterValueRequest
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
    "CustomEntity01",
    "CustomEntity02",
    "CustomEntity03",
    "CustomEntity04",
    "CustomEntity05",
    "CustomEntity06",
    "CustomEntity07",
    "CustomEntity08",
    "CustomEntity09",
    "CustomEntity10",
]


class FlowGetEntityInfo(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="entity_type",
                default_value=ENTITY_TYPES[0],  # Default to "Unknown"
                tooltip="The type of entity to get information for. Select 'Unknown' to auto-detect from entity_id.",
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
                tooltip="The ID of the entity to get information for.",
                placeholder_text="Enter entity ID (e.g., 1234)",
            )
        )
        self.add_parameter(
            ParameterString(
                name="fields",
                default_value=None,
                tooltip="Comma-separated list of specific fields to retrieve (optional). If not provided, will get all available fields.",
                placeholder_text="Enter fields (e.g., name,code,description) or leave empty for all",
            )
        )

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="entity_url",
                default_value="",
                tooltip="The URL to view the entity in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="entity_id_output",
                type="str",
                default_value="",
                tooltip="ID of the entity",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_name",
                default_value="",
                tooltip="Name of the entity",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_code",
                default_value="",
                tooltip="Code of the entity",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_type_output",
                default_value="",
                tooltip="Type of the entity",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="entity_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the entity",
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="attributes",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Attributes of the entity",
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="relationships",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Relationships of the entity",
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
            else:
                # Update entity URL when entity_id changes
                self._update_entity_url()
        elif parameter.name == "entity_type" and value:
            # Update entity URL when entity_type changes
            self._update_entity_url()
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

        if not entity_type or not entity_id:
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

    def _get_entity_schema(self, entity_type: str) -> dict:
        """Get the schema for an entity type to determine available fields."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/schema/{entity_type.lower()}s"

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"{self.name}: Could not get schema for {entity_type}: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"{self.name}: Error getting schema for {entity_type}: {e}")
            return {}

    def _get_default_fields(self, entity_type: str) -> str:
        """Get default fields for an entity type based on common patterns."""
        # Common fields that most entities have
        common_fields = "id,name,code,description,created_at,updated_at"

        # Entity-specific fields
        entity_specific = {
            "Asset": "sg_asset_type,sg_status_list,project",
            "Shot": "sg_sequence,project,sg_status_list",
            "Sequence": "project,sg_status_list",
            "Project": "sg_status,image",
            "Task": "content,sg_status_list,step,task_assignees,project,entity",
            "HumanUser": "email,login,sg_status_list,role,firstname,lastname",
            "Version": "code,description,project,entity,user,created_at",
            "Note": "subject,note,project,entity,user,created_at",
        }

        specific_fields = entity_specific.get(entity_type, "")
        if specific_fields:
            return f"{common_fields},{specific_fields}"
        return common_fields

    def _extract_entity_info(self, entity_data: dict) -> dict:
        """Extract and process entity data from API response."""
        attributes = entity_data.get("attributes", {})
        relationships = entity_data.get("relationships", {})

        # Extract common fields
        entity_name = (
            attributes.get("name")
            or attributes.get("code")
            or f"{entity_data.get('type', 'Entity')} {entity_data.get('id', '')}"
        )

        return {
            "id": entity_data.get("id"),
            "type": entity_data.get("type"),
            "name": entity_name,
            "code": attributes.get("code", ""),
            "description": attributes.get("description", ""),
            "created_at": attributes.get("created_at", ""),
            "updated_at": attributes.get("updated_at", ""),
            "attributes": attributes,
            "relationships": relationships,
        }

    def _update_output_parameters(self, processed_data: dict) -> None:
        """Update all output parameters with the processed entity data."""
        params = {
            "entity_id_output": str(processed_data.get("id", "")),
            "entity_name": processed_data.get("name", ""),
            "entity_code": processed_data.get("code", ""),
            "entity_type_output": processed_data.get("type", ""),
            "entity_data": processed_data,
            "attributes": processed_data.get("attributes", {}),
            "relationships": processed_data.get("relationships", {}),
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def process(self) -> None:
        """Get entity information from ShotGrid."""
        try:
            # Get and validate input parameters
            entity_type = self.get_parameter_value("entity_type")
            entity_id = self.get_parameter_value("entity_id")
            fields = self.get_parameter_value("fields")

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

            # Validate entity type (skip validation for "Unknown" since it gets replaced)
            if entity_type != "Unknown" and entity_type not in ENTITY_TYPES:
                logger.warning(f"{self.name}: Unknown entity type '{entity_type}', proceeding anyway")

            # Determine fields to request
            if not fields:
                fields = self._get_default_fields(entity_type)
                logger.info(f"{self.name}: Using default fields for {entity_type}: {fields}")

            # Get access token
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Construct the API URL
            entity_type_lower = entity_type.lower()
            if entity_type_lower == "humanuser":
                entity_type_lower = "human_users"
            elif entity_type_lower == "customentity01":
                entity_type_lower = "custom_entity_01"
            elif entity_type_lower == "customentity02":
                entity_type_lower = "custom_entity_02"
            elif entity_type_lower == "customentity03":
                entity_type_lower = "custom_entity_03"
            elif entity_type_lower == "customentity04":
                entity_type_lower = "custom_entity_04"
            elif entity_type_lower == "customentity05":
                entity_type_lower = "custom_entity_05"
            elif entity_type_lower == "customentity06":
                entity_type_lower = "custom_entity_06"
            elif entity_type_lower == "customentity07":
                entity_type_lower = "custom_entity_07"
            elif entity_type_lower == "customentity08":
                entity_type_lower = "custom_entity_08"
            elif entity_type_lower == "customentity09":
                entity_type_lower = "custom_entity_09"
            elif entity_type_lower == "customentity10":
                entity_type_lower = "custom_entity_10"
            else:
                entity_type_lower = f"{entity_type_lower}s"

            url = f"{base_url}api/v1/entity/{entity_type_lower}/{entity_id}"

            # Prepare request parameters
            params = {"fields": fields}
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            # Make the request
            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                # Process the response
                data = response.json()
                entity_data = data.get("data", {})

                if not entity_data:
                    logger.error(f"{self.name}: No entity data returned")
                    return

                # Extract and process entity data
                processed_data = self._extract_entity_info(entity_data)

                # Update output parameters
                self._update_output_parameters(processed_data)

                # Update entity URL
                self._update_entity_url()

                logger.info(f"{self.name}: Successfully retrieved {entity_type} {entity_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error getting entity: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error getting entity: {e}")
