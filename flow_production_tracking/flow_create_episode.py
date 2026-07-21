from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowCreateEpisode(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to create the episode in.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_code",
                default_value=None,
                tooltip="The code/name for the episode to create.",
                placeholder_text="Enter the code for the episode to create.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_description",
                type="string",
                default_value=None,
                tooltip="The description for the episode to create.",
                multiline=True,
                placeholder_text="Enter the description for the episode to create.",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The thumbnail image for the episode (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_id",
                default_value=None,
                tooltip="The ID of the newly created episode.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The ID of the newly created episode.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_url",
                default_value="",
                tooltip="The URL of the newly created episode.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The URL of the newly created episode.",
            )
        )
        self.add_parameter(
            Parameter(
                name="created_episode",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The created episode data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self._create_status_parameters()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "episode_id" and value:
            try:
                episode_id = int(value)
                self._update_episode_url(episode_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid episode_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update episode_url for episode {value}: {e}")

        return super().after_value_set(parameter, value)

    def _update_episode_url(self, episode_id: int) -> None:
        """Update the episode_url output parameter with the ShotGrid URL."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            episode_url = f"{base_url.rstrip('/')}/detail/Episode/{episode_id}"
            self.set_parameter_value("episode_url", episode_url)
            self.parameter_output_values["episode_url"] = episode_url
            self.publish_update_to_parameter("episode_url", episode_url)
            logger.info(f"{self.name}: Updated episode_url to: {episode_url}")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update episode_url: {e}")

    def process(self) -> None:
        """Create a new episode in ShotGrid."""
        self._clear_execution_status()
        try:
            # Get input parameters
            project_id = self.get_parameter_value("project_id")
            episode_code = self.get_parameter_value("episode_code")
            episode_description = self.get_parameter_value("episode_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not project_id:
                self._set_status_results(was_successful=False, result_details="project_id is required")
                logger.error(f"{self.name}: project_id is required")
                return

            if not episode_code:
                self._set_status_results(was_successful=False, result_details="episode_code is required")
                logger.error(f"{self.name}: episode_code is required")
                return

            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                self._set_status_results(was_successful=False, result_details="project_id must be a valid integer")
                logger.error(f"{self.name}: project_id must be a valid integer")
                return

            # Get access token - try password auth first for better permissions
            try:
                access_token = self._get_access_token_with_password()
                logger.info(f"{self.name}: Using password authentication")
            except Exception as e:
                logger.warning(f"{self.name}: Password authentication failed, falling back to client credentials: {e}")
                access_token = self._get_access_token()

            base_url = self._get_shotgrid_config()["base_url"]

            # Prepare episode data
            episode_data = {
                "code": episode_code,
                "project": {"type": "Project", "id": project_id},
            }

            if episode_description:
                episode_data["description"] = episode_description

            logger.info(f"{self.name}: Creating episode with data: {episode_data}")

            # Create the episode
            create_url = f"{base_url}api/v1/entity/episodes"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            with httpx.Client() as client:
                response = client.post(create_url, headers=headers, json=episode_data)
                response.raise_for_status()

                data = response.json()
                created_episode = data.get("data", {})
                episode_id = created_episode.get("id")

                if not episode_id:
                    self._set_status_results(was_successful=False, result_details="No episode ID returned from creation")
                    logger.error(f"{self.name}: No episode ID returned from creation")
                    return

                logger.info(f"{self.name}: Episode created successfully with ID: {episode_id}")

                # Upload thumbnail if provided
                if thumbnail_image:
                    logger.info(f"{self.name}: Uploading thumbnail for episode {episode_id}")
                    try:
                        self._update_entity_thumbnail("episodes", episode_id, thumbnail_image, access_token, base_url)
                        logger.info(f"{self.name}: Thumbnail uploaded successfully")
                    except Exception as e:
                        logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

                # Get final episode data
                try:
                    episode_url = f"{base_url}api/v1/entity/episodes/{episode_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    }

                    with httpx.Client() as client:
                        response = client.get(episode_url, headers=headers)
                        response.raise_for_status()

                        data = response.json()
                        final_episode_data = data.get("data", {})
                        logger.info(f"{self.name}: Retrieved final episode data")
                except Exception as e:
                    logger.warning(f"{self.name}: Could not get final episode data: {e}")
                    final_episode_data = created_episode

                # Output the results
                self.parameter_output_values["episode_id"] = str(episode_id)
                self.publish_update_to_parameter("episode_id", str(episode_id))

                self.parameter_output_values["created_episode"] = final_episode_data
                self.publish_update_to_parameter("created_episode", final_episode_data)

                # Update the episode URL
                self._update_episode_url(episode_id)

                self._set_status_results(
                    was_successful=True, result_details=f"Successfully created episode {episode_id}"
                )

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
