from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateEpisode(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="episode_id",
                type="string",
                default_value=None,
                tooltip="The ID of the episode to update.",
            )
        )
        # Episode URL output parameter
        self.add_parameter(
            Parameter(
                name="episode_url",
                type="string",
                default_value="",
                tooltip="The URL to view the episode in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="episode_code",
                type="string",
                default_value=None,
                tooltip="The new code for the episode (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="episode_description",
                type="string",
                default_value=None,
                tooltip="The new description for the episode (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The new thumbnail image for the episode (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_episode",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated episode data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self._create_status_parameters()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update the episode_url output when episode_id changes."""
        if parameter.name == "episode_id" and value:
            try:
                # Convert episode_id to integer if it's a string
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
        self._clear_execution_status()
        try:
            # Get input parameters
            episode_id = self.get_parameter_value("episode_id")
            episode_code = self.get_parameter_value("episode_code")
            episode_description = self.get_parameter_value("episode_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not episode_id:
                logger.error(f"{self.name}: episode_id is required")
                return

            try:
                episode_id = int(episode_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: episode_id must be a valid integer")
                return

            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Prepare update data for episode fields
            update_data = {}
            has_updates = False

            if episode_code is not None:
                update_data["code"] = episode_code
                has_updates = True

            if episode_description is not None:
                update_data["description"] = episode_description
                has_updates = True

            # Update episode fields if any are provided
            if has_updates:
                logger.info(f"{self.name}: Updating episode fields")
                try:
                    try:
                        access_token = self._get_access_token_with_password()
                        logger.info(f"{self.name}: Using password authentication")
                    except Exception as e:
                        logger.warning(
                            f"{self.name}: Password authentication failed, falling back to client credentials: {e}"
                        )
                        access_token = self._get_access_token()

                    update_url = f"{base_url}api/v1/entity/episodes/{episode_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Updating episode {episode_id} with data: {update_data}")

                    with httpx.Client() as client:
                        response = client.put(update_url, headers=headers, json=update_data)
                        response.raise_for_status()

                        data = response.json()
                        updated_episode = data.get("data", {})
                        logger.info(f"{self.name}: Episode fields updated successfully")

                except Exception as e:
                    logger.error(f"{self.name}: Failed to update episode fields: {e}")
                    raise

            # Upload thumbnail if provided
            if thumbnail_image:
                logger.info(f"{self.name}: Uploading thumbnail for episode {episode_id}")
                try:
                    self._update_entity_thumbnail("episodes", episode_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail uploaded successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

            # Check if we have any updates (fields or thumbnail)
            if not has_updates and not thumbnail_image:
                logger.error(f"{self.name}: At least one field to update or thumbnail must be provided")
                return

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
                final_episode_data = updated_episode if has_updates else {}

            # Output the results
            self.parameter_output_values["updated_episode"] = final_episode_data

            self._set_status_results(was_successful=True, result_details=f"Successfully updated episode {episode_id}")

            # Update the episode_url output
            self._update_episode_url(episode_id)

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
