from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateVersion(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="version_id",
                type="string",
                default_value=None,
                tooltip="The ID of the version to update.",
            )
        )
        # Version URL output parameter
        self.add_parameter(
            Parameter(
                name="version_url",
                type="string",
                default_value="",
                tooltip="The URL to view the version in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="version_code",
                type="string",
                default_value=None,
                tooltip="The new code for the version (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="version_description",
                type="string",
                default_value=None,
                tooltip="The new description for the version (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The new thumbnail image for the version (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_version",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated version data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self._create_status_parameters()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update the version_url output when version_id changes."""
        if parameter.name == "version_id" and value:
            try:
                # Convert version_id to integer if it's a string
                version_id = int(value)
                self._update_version_url(version_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid version_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update version_url for version {value}: {e}")

        return super().after_value_set(parameter, value)

    def _update_version_url(self, version_id: int) -> None:
        """Update the version_url output parameter with the ShotGrid URL."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            version_url = f"{base_url}detail/Version/{version_id}"
            self.set_parameter_value("version_url", version_url)
            self.parameter_output_values["version_url"] = version_url
            self.publish_update_to_parameter("version_url", version_url)
            logger.info(f"{self.name}: Updated version_url to: {version_url}")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update version_url: {e}")

    def process(self) -> None:
        self._clear_execution_status()
        try:
            # Get input parameters
            version_id = self.get_parameter_value("version_id")
            version_code = self.get_parameter_value("version_code")
            version_description = self.get_parameter_value("version_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not version_id:
                logger.error(f"{self.name}: version_id is required")
                return

            try:
                version_id = int(version_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: version_id must be a valid integer")
                return

            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Prepare update data for version fields
            update_data = {}
            has_updates = False

            if version_code is not None:
                update_data["code"] = version_code
                has_updates = True

            if version_description is not None:
                update_data["description"] = version_description
                has_updates = True

            # Update version fields if any are provided
            if has_updates:
                logger.info(f"{self.name}: Updating version fields")
                try:
                    try:
                        access_token = self._get_access_token_with_password()
                        logger.info(f"{self.name}: Using password authentication")
                    except Exception as e:
                        logger.warning(
                            f"{self.name}: Password authentication failed, falling back to client credentials: {e}"
                        )
                        access_token = self._get_access_token()

                    update_url = f"{base_url}api/v1/entity/versions/{version_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Updating version {version_id} with data: {update_data}")

                    with httpx.Client() as client:
                        response = client.put(update_url, headers=headers, json=update_data)
                        response.raise_for_status()

                        data = response.json()
                        updated_version = data.get("data", {})
                        logger.info(f"{self.name}: Version fields updated successfully")

                except Exception as e:
                    logger.error(f"{self.name}: Failed to update version fields: {e}")
                    raise

            # Upload thumbnail if provided
            if thumbnail_image:
                logger.info(f"{self.name}: Uploading thumbnail for version {version_id}")
                try:
                    self._update_entity_thumbnail("versions", version_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail uploaded successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

            # Check if we have any updates (fields or thumbnail)
            if not has_updates and not thumbnail_image:
                logger.error(f"{self.name}: At least one field to update or thumbnail must be provided")
                return

            # Get final version data
            try:
                version_url = f"{base_url}api/v1/entity/versions/{version_id}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }

                with httpx.Client() as client:
                    response = client.get(version_url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    final_version_data = data.get("data", {})
                    logger.info(f"{self.name}: Retrieved final version data")
            except Exception as e:
                logger.warning(f"{self.name}: Could not get final version data: {e}")
                final_version_data = updated_version if has_updates else {}

            # Output the results
            self.parameter_output_values["updated_version"] = final_version_data

            self._set_status_results(was_successful=True, result_details=f"Successfully updated version {version_id}")

            # Update the version_url output
            self._update_version_url(version_id)

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
