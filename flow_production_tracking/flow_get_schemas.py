import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowGetSchemas(BaseShotGridNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_parameter(
            Parameter(
                name="entity_type",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The entity type to get schema for (e.g., 'Project', 'Asset', 'Task'). Leave empty to get all schemas.",
            )
        )
        self.add_parameter(
            Parameter(
                name="schemas",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The schema data for the requested entity type(s).",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )

    def process(self) -> None:
        try:
            # Get input parameters
            entity_type = self.get_parameter_value("entity_type")

            # Get access token
            access_token = self._get_access_token()

            # Make request to get schemas
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Get base URL
            base_url = self._get_shotgrid_config()["base_url"]

            if entity_type:
                # Get schema for specific entity type
                url = f"{base_url}api/v1/schema/{entity_type}"
                logger.info(f"{self.name}: Getting schema for entity type: {entity_type}")
            else:
                # Get all schemas
                url = f"{base_url}api/v1/schema"
                logger.info(f"{self.name}: Getting all schemas")

            with httpx.Client() as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                schemas = data.get("data", {})

                # Output the schema data
                self.parameter_output_values["schemas"] = schemas
                logger.info(f"{self.name}: Retrieved schema data")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
