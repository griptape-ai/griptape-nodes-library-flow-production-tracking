from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateProject(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to update.",
            )
        )
        # Project URL output parameter
        self.add_parameter(
            Parameter(
                name="project_url",
                type="string",
                default_value="",
                tooltip="The URL to view the project in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )

        self.add_parameter(
            Parameter(
                name="project_name",
                type="string",
                default_value=None,
                tooltip="The new name for the project (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="project_code",
                type="string",
                default_value=None,
                tooltip="The new code for the project (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="project_description",
                type="string",
                default_value=None,
                tooltip="The new description for the project (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The new thumbnail image for the project (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_project",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated project data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

        self._create_status_parameters()

    def _update_project_url(self, project_id: int) -> None:
        """Update the project_url output parameter with the ShotGrid URL."""
        try:
            # Get the base URL from config
            base_url = self._get_shotgrid_config()["base_url"]

            # Create the ShotGrid URL for the project
            project_url = f"{base_url}detail/Project/{project_id}"

            # Set the output parameter
            self.set_parameter_value("project_url", project_url)
            self.parameter_output_values["project_url"] = project_url
            self.publish_update_to_parameter("project_url", project_url)

            logger.info(f"{self.name}: Updated project_url to: {project_url}")

        except Exception as e:
            logger.warning(f"{self.name}: Failed to update project_url: {e}")

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update the project_url output when project_id changes."""
        if parameter.name == "project_id" and value:
            try:
                # Convert project_id to integer if it's a string
                project_id = int(value)
                self._update_project_url(project_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid project_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update project_url for project {value}: {e}")

        return super().after_value_set(parameter, value)

    def process(self) -> None:
        self._clear_execution_status()
        try:
            # Get input parameters
            project_id = self.get_parameter_value("project_id")
            project_name = self.get_parameter_value("project_name")
            project_code = self.get_parameter_value("project_code")
            project_description = self.get_parameter_value("project_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not project_id:
                self._set_status_results(was_successful=False, result_details="project_id is required")
                logger.error(f"{self.name}: project_id is required")
                return

            # Convert project_id to integer if it's a string
            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                self._set_status_results(was_successful=False, result_details="project_id must be a valid integer")
                logger.error(f"{self.name}: project_id must be a valid integer")
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Prepare update data for basic project fields
            update_data = {}
            has_basic_updates = False
            updated_project = None

            if project_name is not None:
                update_data["name"] = project_name
                has_basic_updates = True

            if project_code is not None:
                update_data["code"] = project_code
                has_basic_updates = True

            if project_description is not None:
                update_data["sg_description"] = project_description
                has_basic_updates = True

            # Update basic project fields if any are provided
            if has_basic_updates:
                logger.info(f"{self.name}: Updating basic project fields")
                try:
                    update_url = f"{base_url}api/v1/entity/projects/{project_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Updating project {project_id} with data: {update_data}")

                    with httpx.Client() as client:
                        response = client.put(update_url, headers=headers, json=update_data)
                        response.raise_for_status()

                        data = response.json()
                        updated_project = data.get("data", {})
                        logger.info(f"{self.name}: Basic project fields updated successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to update basic project fields: {e}")
                    raise

            # Update thumbnail if provided
            if thumbnail_image:
                logger.info(f"{self.name}: Updating project thumbnail")
                try:
                    self._update_entity_thumbnail("projects", project_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail update completed")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to update thumbnail: {e}")
                    raise

            # Get final project data
            try:
                project_url = f"{base_url}api/v1/entity/projects/{project_id}"
                with httpx.Client() as client:
                    resp = client.get(
                        project_url, headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
                    )
                    resp.raise_for_status()
                    final_project_data = resp.json().get("data", {})
                    logger.info(f"{self.name}: Retrieved final project data")
            except Exception as e:
                logger.warning(f"{self.name}: Could not get final project data: {e}")
                final_project_data = updated_project if has_basic_updates else {"id": project_id, "status": "updated"}

            # Output the results
            self.parameter_output_values["updated_project"] = final_project_data

            self._set_status_results(was_successful=True, result_details=f"Successfully updated project {project_id}")

            # Update the project_url output
            self._update_project_url(project_id)

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
