from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateShot(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="shot_id",
                type="string",
                default_value=None,
                tooltip="The ID of the shot to update.",
            )
        )
        self.add_parameter(
            Parameter(
                name="shot_url",
                type="string",
                default_value="",
                tooltip="The URL to view the shot in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="shot_code",
                type="string",
                default_value=None,
                tooltip="The new code for the shot (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="shot_description",
                type="string",
                default_value=None,
                tooltip="The new description for the shot (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The new thumbnail image for the shot (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_shot",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated shot data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self._create_status_parameters()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "shot_id" and value:
            try:
                shot_id = int(value)
                self._update_shot_url(shot_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid shot_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update shot_url for shot {value}: {e}")

        return super().after_value_set(parameter, value)

    def _update_shot_url(self, shot_id: int) -> None:
        """Update the shot_url output parameter with the ShotGrid URL."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            shot_url = f"{base_url.rstrip('/')}/detail/Shot/{shot_id}"
            self.set_parameter_value("shot_url", shot_url)
            self.parameter_output_values["shot_url"] = shot_url
            self.publish_update_to_parameter("shot_url", shot_url)
            logger.info(f"{self.name}: Updated shot_url to: {shot_url}")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update shot_url: {e}")

    def process(self) -> None:
        self._clear_execution_status()
        try:
            shot_id = self.get_parameter_value("shot_id")
            shot_code = self.get_parameter_value("shot_code")
            shot_description = self.get_parameter_value("shot_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not shot_id:
                logger.error(f"{self.name}: shot_id is required")
                return

            try:
                shot_id = int(shot_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: shot_id must be a valid integer")
                return

            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            update_data = {}
            has_updates = False

            if shot_code is not None:
                update_data["code"] = shot_code
                has_updates = True

            if shot_description is not None:
                update_data["description"] = shot_description
                has_updates = True

            if has_updates:
                logger.info(f"{self.name}: Updating shot fields")
                try:
                    try:
                        access_token = self._get_access_token_with_password()
                        logger.info(f"{self.name}: Using password authentication")
                    except Exception as e:
                        logger.warning(
                            f"{self.name}: Password authentication failed, falling back to client credentials: {e}"
                        )
                        access_token = self._get_access_token()

                    update_url = f"{base_url}api/v1/entity/shots/{shot_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Updating shot {shot_id} with data: {update_data}")

                    with httpx.Client() as client:
                        response = client.put(update_url, headers=headers, json=update_data)
                        response.raise_for_status()

                        data = response.json()
                        updated_shot = data.get("data", {})
                        logger.info(f"{self.name}: Shot fields updated successfully")

                except Exception as e:
                    logger.error(f"{self.name}: Failed to update shot fields: {e}")
                    raise

            if thumbnail_image:
                logger.info(f"{self.name}: Uploading thumbnail for shot {shot_id}")
                try:
                    self._update_entity_thumbnail("shots", shot_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail uploaded successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

            if not has_updates and not thumbnail_image:
                logger.error(f"{self.name}: At least one field to update or thumbnail must be provided")
                return

            try:
                shot_url = f"{base_url}api/v1/entity/shots/{shot_id}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }

                with httpx.Client() as client:
                    response = client.get(shot_url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    final_shot_data = data.get("data", {})
                    logger.info(f"{self.name}: Retrieved final shot data")
            except Exception as e:
                logger.warning(f"{self.name}: Could not get final shot data: {e}")
                final_shot_data = updated_shot if has_updates else {}

            self.parameter_output_values["updated_shot"] = final_shot_data

            self._set_status_results(was_successful=True, result_details=f"Successfully updated shot {shot_id}")

            self._update_shot_url(shot_id)

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
