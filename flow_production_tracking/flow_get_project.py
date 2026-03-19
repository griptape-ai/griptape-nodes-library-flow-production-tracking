import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowGetProject(BaseShotGridNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_parameter(
            Parameter(
                name="project_id",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The ID of the project to retrieve.",
            )
        )
        self.add_parameter(
            Parameter(
                name="project",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The project data.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="project_thumbnail",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The project thumbnail URL.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

    def process(self) -> None:
        try:
            # Get input parameters
            project_id = self.get_parameter_value("project_id")

            if not project_id:
                logger.error(f"{self.name}: project_id is required")
                return

            # Convert project_id to integer if it's a string
            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: project_id must be a valid integer")
                return

            # Get access token
            access_token = self._get_access_token()

            # Make request to get project
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Get base URL
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/projects/{project_id}"

            # Add fields parameter to get all fields plus thumbnail info
            params = {"fields": "*,image,sg_thumbnail"}

            logger.info(f"{self.name}: Getting project {project_id}")

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                project = data.get("data", {})

                # Extract thumbnail URL
                project_attributes = project.get("attributes", {})
                thumbnail_url = project_attributes.get("sg_thumbnail") or project_attributes.get("image") or ""

                # Output the project data and thumbnail
                self.parameter_output_values["project"] = project
                self.parameter_output_values["project_thumbnail"] = thumbnail_url
                logger.info(f"{self.name}: Retrieved project data: {project}")
                if thumbnail_url:
                    logger.info(f"{self.name}: Project thumbnail URL: {thumbnail_url}")
                else:
                    logger.info(f"{self.name}: No thumbnail found for project")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
