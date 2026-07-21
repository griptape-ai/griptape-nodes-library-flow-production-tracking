from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowCreateSequence(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to create the sequence in (required).",
            )
        )
        self.add_parameter(
            Parameter(
                name="episode_id",
                type="string",
                default_value=None,
                tooltip="The ID of the episode to create the sequence in (optional, only if project uses episodes).",
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_code",
                default_value=None,
                tooltip="The code/name for the sequence to create.",
                placeholder_text="Enter the code for the sequence to create.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_description",
                type="string",
                default_value=None,
                tooltip="The description for the sequence to create.",
                multiline=True,
                placeholder_text="Enter the description for the sequence to create.",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The thumbnail image for the sequence (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_id",
                default_value=None,
                tooltip="The ID of the newly created sequence.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The ID of the newly created sequence.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_url",
                default_value="",
                tooltip="The URL of the newly created sequence.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The URL of the newly created sequence.",
            )
        )
        self.add_parameter(
            Parameter(
                name="created_sequence",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The created sequence data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self._create_status_parameters()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "sequence_id" and value:
            try:
                sequence_id = int(value)
                self._update_sequence_url(sequence_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid sequence_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update sequence_url for sequence {value}: {e}")

        return super().after_value_set(parameter, value)

    def _update_sequence_url(self, sequence_id: int) -> None:
        """Update the sequence_url output parameter with the ShotGrid URL."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            sequence_url = f"{base_url.rstrip('/')}/detail/Sequence/{sequence_id}"
            self.set_parameter_value("sequence_url", sequence_url)
            self.parameter_output_values["sequence_url"] = sequence_url
            self.publish_update_to_parameter("sequence_url", sequence_url)
            logger.info(f"{self.name}: Updated sequence_url to: {sequence_url}")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update sequence_url: {e}")






    def process(self) -> None:
        self._clear_execution_status()
        """Create a new sequence in ShotGrid."""
        try:
            project_id = self.get_parameter_value("project_id")
            episode_id = self.get_parameter_value("episode_id")
            sequence_code = self.get_parameter_value("sequence_code")
            sequence_description = self.get_parameter_value("sequence_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not project_id:
                logger.error(f"{self.name}: project_id is required")
                return

            if not sequence_code:
                logger.error(f"{self.name}: sequence_code is required")
                return

            try:
                project_id = int(project_id)
                if episode_id:
                    episode_id = int(episode_id)
            except (ValueError, TypeError) as e:
                logger.error(f"{self.name}: project_id and episode_id (if provided) must be valid integers: {e}")
                return

            try:
                access_token = self._get_access_token_with_password()
                logger.info(f"{self.name}: Using password authentication")
            except Exception as e:
                logger.warning(f"{self.name}: Password authentication failed, falling back to client credentials: {e}")
                access_token = self._get_access_token()

            base_url = self._get_shotgrid_config()["base_url"]

            sequence_data = {
                "code": sequence_code,
                "project": {"type": "Project", "id": project_id},
            }

            if episode_id:
                sequence_data["episode"] = {"type": "Episode", "id": episode_id}

            if sequence_description:
                sequence_data["description"] = sequence_description

            logger.info(f"{self.name}: Creating sequence with data: {sequence_data}")

            create_url = f"{base_url}api/v1/entity/sequences"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            with httpx.Client() as client:
                response = client.post(create_url, headers=headers, json=sequence_data)
                response.raise_for_status()

                data = response.json()
                created_sequence = data.get("data", {})
                sequence_id = created_sequence.get("id")

                if not sequence_id:
                    logger.error(f"{self.name}: No sequence ID returned from creation")
                    return

                logger.info(f"{self.name}: Sequence created successfully with ID: {sequence_id}")

                if thumbnail_image:
                    logger.info(f"{self.name}: Uploading thumbnail for sequence {sequence_id}")
                    try:
                        self._update_entity_thumbnail("sequences", sequence_id, thumbnail_image, access_token, base_url)
                        logger.info(f"{self.name}: Thumbnail uploaded successfully")
                    except Exception as e:
                        logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

                try:
                    sequence_url = f"{base_url}api/v1/entity/sequences/{sequence_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    }

                    with httpx.Client() as client:
                        response = client.get(sequence_url, headers=headers)
                        response.raise_for_status()

                        data = response.json()
                        final_sequence_data = data.get("data", {})
                        logger.info(f"{self.name}: Retrieved final sequence data")
                except Exception as e:
                    logger.warning(f"{self.name}: Could not get final sequence data: {e}")
                    final_sequence_data = created_sequence

                self.parameter_output_values["sequence_id"] = str(sequence_id)
                self.publish_update_to_parameter("sequence_id", str(sequence_id))

                self.parameter_output_values["created_sequence"] = final_sequence_data
                self.publish_update_to_parameter("created_sequence", final_sequence_data)

                self._update_sequence_url(sequence_id)

                self._set_status_results(was_successful=True, result_details=f"Successfully created sequence {sequence_id}")

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
