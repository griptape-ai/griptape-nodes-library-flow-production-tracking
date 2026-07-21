from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateSequence(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="sequence_id",
                type="string",
                default_value=None,
                tooltip="The ID of the sequence to update.",
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_url",
                type="string",
                default_value="",
                tooltip="The URL to view the sequence in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_code",
                type="string",
                default_value=None,
                tooltip="The new code for the sequence (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_description",
                type="string",
                default_value=None,
                tooltip="The new description for the sequence (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The new thumbnail image for the sequence (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_sequence",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated sequence data.",
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
        try:
            sequence_id = self.get_parameter_value("sequence_id")
            sequence_code = self.get_parameter_value("sequence_code")
            sequence_description = self.get_parameter_value("sequence_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not sequence_id:
                logger.error(f"{self.name}: sequence_id is required")
                return

            try:
                sequence_id = int(sequence_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: sequence_id must be a valid integer")
                return

            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            update_data = {}
            has_updates = False

            if sequence_code is not None:
                update_data["code"] = sequence_code
                has_updates = True

            if sequence_description is not None:
                update_data["description"] = sequence_description
                has_updates = True

            if has_updates:
                logger.info(f"{self.name}: Updating sequence fields")
                try:
                    try:
                        access_token = self._get_access_token_with_password()
                        logger.info(f"{self.name}: Using password authentication")
                    except Exception as e:
                        logger.warning(
                            f"{self.name}: Password authentication failed, falling back to client credentials: {e}"
                        )
                        access_token = self._get_access_token()

                    update_url = f"{base_url}api/v1/entity/sequences/{sequence_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Updating sequence {sequence_id} with data: {update_data}")

                    with httpx.Client() as client:
                        response = client.put(update_url, headers=headers, json=update_data)
                        response.raise_for_status()

                        data = response.json()
                        updated_sequence = data.get("data", {})
                        logger.info(f"{self.name}: Sequence fields updated successfully")

                except Exception as e:
                    logger.error(f"{self.name}: Failed to update sequence fields: {e}")
                    raise

            if thumbnail_image:
                logger.info(f"{self.name}: Uploading thumbnail for sequence {sequence_id}")
                try:
                    self._update_entity_thumbnail("sequences", sequence_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail uploaded successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

            if not has_updates and not thumbnail_image:
                logger.error(f"{self.name}: At least one field to update or thumbnail must be provided")
                return

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
                final_sequence_data = updated_sequence if has_updates else {}

            self.parameter_output_values["updated_sequence"] = final_sequence_data

            self._set_status_results(was_successful=True, result_details=f"Successfully updated sequence {sequence_id}")

            self._update_sequence_url(sequence_id)

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
