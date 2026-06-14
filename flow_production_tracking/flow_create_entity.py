import json
from typing import Any

from base_shotgrid_node import BaseShotGridNode
from flow_utils import create_shotgrid_api
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.param_types.parameter_int import ParameterInt
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.events.node_events import ListParametersOnNodeRequest
from griptape_nodes.retained_mode.events.parameter_events import (
    AddParameterToNodeRequest,
    GetConnectionsForParameterRequest,
    GetConnectionsForParameterResultSuccess,
    RemoveParameterFromNodeRequest,
)
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
from griptape_nodes.traits.options import Options

# Entity types that can be created, including custom entities.
ENTITY_TYPES = [
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
    "Asset",
    "Shot",
    "Sequence",
    "Episode",
    "Task",
    "Note",
    "Playlist",
    "Version",
]

# Number of custom field name/value pairs the node starts with.
DEFAULT_FIELD_COUNT = 3
# Upper bound on the number of custom field pairs to guard against runaway values.
MAX_FIELD_COUNT = 25

# Parameters that are part of the node itself and must never be treated as custom fields.
STATIC_PARAMS = {
    "entity_type",
    "project_id",
    "num_custom_fields",
    "created_entity",
    "entity_id",
    "entity_url",
    "exec_out",
    "exec_in",
    "execution_environment",
    "job_group",
}


def entity_type_to_api(entity_type: str) -> str:
    """Convert a ShotGrid entity type to its REST API path segment.

    e.g. Asset -> assets, HumanUser -> human_users, CustomEntity01 -> custom_entity_01
    """
    entity_type_lower = entity_type.lower()
    if entity_type_lower == "humanuser":
        return "human_users"
    if entity_type_lower.startswith("customentity"):
        num = entity_type_lower.replace("customentity", "")
        return f"custom_entity_{num.zfill(2)}"
    return f"{entity_type_lower}s"


class FlowCreateEntity(BaseShotGridNode):
    """Create a new ShotGrid entity (including custom entities) with user-defined fields.

    Connection/configuration details are pulled from the Autodesk Flow Configuration
    via BaseShotGridNode (SHOTGRID_URL / SHOTGRID_API_KEY / SHOTGRID_SCRIPT_NAME).
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="entity_type",
                default_value=ENTITY_TYPES[0],  # Default to CustomEntity01
                tooltip="The type of entity to create. Custom entities appear as CustomEntityNN.",
                placeholder_text="Select the entity type to create",
                traits={Options(choices=ENTITY_TYPES)},
            )
        )
        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to create the entity in (optional for non-project entities).",
                placeholder_text="Enter project ID (e.g., 1234)",
            )
        )
        self.add_parameter(
            ParameterInt(
                name="num_custom_fields",
                default_value=DEFAULT_FIELD_COUNT,
                tooltip="How many custom field name/value pairs to show. Increase to add more fields.",
                step=1,
                min_val=0,
                max_val=MAX_FIELD_COUNT,
            )
        )

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="entity_id",
                default_value=None,
                tooltip="The ID of the created entity.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_url",
                default_value="",
                tooltip="The URL to view the created entity in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="created_entity",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the created entity.",
                ui_options={"hide_property": True},
            )
        )

        # Create the initial set of custom field name/value pairs.
        for i in range(1, DEFAULT_FIELD_COUNT + 1):
            self.add_parameter(
                ParameterString(
                    name=f"field_{i}_name",
                    default_value=None,
                    tooltip=f"Field #{i}: the ShotGrid field code (e.g., 'code', 'description', 'sg_my_field').",
                    placeholder_text="Field code",
                )
            )
            self.add_parameter(
                ParameterString(
                    name=f"field_{i}_value",
                    default_value=None,
                    tooltip=f"Field #{i}: the value to set. JSON is parsed for link fields (e.g., {{\"type\": \"Asset\", \"id\": 5}}).",
                    placeholder_text="Field value",
                )
            )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "num_custom_fields":
            try:
                count = int(value)
            except (ValueError, TypeError):
                count = DEFAULT_FIELD_COUNT
            self._sync_field_parameters(count)
        return super().after_value_set(parameter, value)

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

    def _sync_field_parameters(self, count: int) -> None:
        """Add or remove custom field name/value pairs to match the requested count."""
        count = max(0, min(count, MAX_FIELD_COUNT))
        existing = self._get_current_parameter_names()

        # Add any missing field pairs up to the requested count.
        for i in range(1, count + 1):
            name_param = f"field_{i}_name"
            value_param = f"field_{i}_value"

            if name_param not in existing:
                GriptapeNodes.handle_request(
                    AddParameterToNodeRequest(
                        node_name=self.name,
                        parameter_name=name_param,
                        default_value=None,
                        tooltip=f"Field #{i}: the ShotGrid field code (e.g., 'code', 'description', 'sg_my_field').",
                        type="str",
                        mode_allowed_output=False,
                        mode_allowed_input=True,
                        mode_allowed_property=True,
                        is_user_defined=True,
                        ui_options={"placeholder_text": "Field code"},
                    )
                )
            if value_param not in existing:
                GriptapeNodes.handle_request(
                    AddParameterToNodeRequest(
                        node_name=self.name,
                        parameter_name=value_param,
                        default_value=None,
                        tooltip=f"Field #{i}: the value to set. JSON is parsed for link fields.",
                        type="str",
                        mode_allowed_output=False,
                        mode_allowed_input=True,
                        mode_allowed_property=True,
                        is_user_defined=True,
                        ui_options={"placeholder_text": "Field value"},
                    )
                )

        # Remove any field pairs beyond the requested count (unless connected).
        for i in range(count + 1, MAX_FIELD_COUNT + 1):
            for param_name in (f"field_{i}_name", f"field_{i}_value"):
                if param_name not in existing:
                    continue
                if self._is_parameter_connected(param_name):
                    logger.info(f"{self.name}: Skipping removal of connected parameter '{param_name}'")
                    continue
                GriptapeNodes.handle_request(
                    RemoveParameterFromNodeRequest(parameter_name=param_name, node_name=self.name)
                )
                if param_name in self.parameter_output_values:
                    del self.parameter_output_values[param_name]

    def _collect_custom_fields(self) -> dict:
        """Collect non-empty field name/value pairs into a data dict for the API."""
        field_data = {}
        all_params = self._get_current_parameter_names()
        # Find every field index that currently has a name parameter.
        indices = sorted(
            int(p[len("field_") : -len("_name")])
            for p in all_params
            if p.startswith("field_") and p.endswith("_name")
        )

        for i in indices:
            field_name = self.get_parameter_value(f"field_{i}_name")
            field_value = self.get_parameter_value(f"field_{i}_value")

            if not field_name:
                continue

            field_name = str(field_name).strip()
            if not field_name:
                continue

            # Attempt to parse JSON values so link fields can be provided as objects/arrays.
            parsed_value: Any = field_value
            if isinstance(field_value, str):
                stripped = field_value.strip()
                if stripped and stripped[0] in "{[":
                    try:
                        parsed_value = json.loads(stripped)
                    except json.JSONDecodeError:
                        parsed_value = field_value

            field_data[field_name] = parsed_value
            logger.info(f"{self.name}: Will set '{field_name}' = {parsed_value!r}")

        return field_data

    def process(self) -> None:
        """Create the entity in ShotGrid."""
        entity_type = self.get_parameter_value("entity_type")
        project_id = self.get_parameter_value("project_id")

        if not entity_type:
            logger.error(f"{self.name}: entity_type is required")
            return

        # Build the create payload from the custom field pairs.
        entity_data = self._collect_custom_fields()

        # Attach the project link when provided.
        if project_id:
            try:
                entity_data["project"] = {"type": "Project", "id": int(project_id)}
            except (ValueError, TypeError):
                logger.error(f"{self.name}: project_id must be a valid integer")
                return

        if not entity_data:
            logger.error(f"{self.name}: No fields provided. Add at least one custom field name/value.")
            return

        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            entity_type_api = entity_type_to_api(entity_type)
            logger.info(f"{self.name}: Creating {entity_type} ({entity_type_api}) with data: {entity_data}")

            created_entity = api.create_entity(entity_type_api, entity_data)

            if not created_entity:
                logger.error(f"{self.name}: Failed to create {entity_type}")
                return

            entity_id = created_entity.get("id")
            entity_url = f"{base_url.rstrip('/')}/detail/{entity_type}/{entity_id}"

            self.parameter_output_values["created_entity"] = created_entity
            self.parameter_output_values["entity_id"] = str(entity_id)
            self.parameter_output_values["entity_url"] = entity_url

            logger.info(f"{self.name}: Successfully created {entity_type} {entity_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error creating entity: {e!s}")
