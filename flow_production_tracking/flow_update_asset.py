from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateAsset(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="asset_id",
                type="string",
                default_value=None,
                tooltip="The ID of the asset to update.",
            )
        )
        # Asset URL output parameter
        self.add_parameter(
            Parameter(
                name="asset_url",
                type="string",
                default_value="",
                tooltip="The URL to view the asset in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        # Note: Assets in ShotGrid don't have names, only codes
        # This parameter is kept for backward compatibility but will be ignored
        self.add_parameter(
            Parameter(
                name="asset_name",
                type="string",
                default_value=None,
                tooltip="The new name for the asset (optional). Note: Assets in ShotGrid only have codes, not names, so this field will be ignored.",
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_code",
                type="string",
                default_value=None,
                tooltip="The new code for the asset (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_type",
                type="string",
                default_value=None,
                tooltip="The new type for the asset (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_description",
                type="string",
                default_value=None,
                tooltip="The new description for the asset (optional).",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The new thumbnail image for the asset (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_asset",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated asset data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

        self._create_status_parameters()

    def _update_asset_url(self, asset_id: int) -> None:
        """Update the asset_url output parameter with the ShotGrid URL."""
        try:
            # Get the base URL from config
            base_url = self._get_shotgrid_config()["base_url"]

            # Create the ShotGrid URL for the asset
            asset_url = f"{base_url}detail/Asset/{asset_id}"

            # Set the output parameter
            self.set_parameter_value("asset_url", asset_url)
            self.parameter_output_values["asset_url"] = asset_url
            self.publish_update_to_parameter("asset_url", asset_url)

            logger.info(f"{self.name}: Updated asset_url to: {asset_url}")

        except Exception as e:
            logger.warning(f"{self.name}: Failed to update asset_url: {e}")

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update the asset_url output when asset_id changes."""
        if parameter.name == "asset_id" and value:
            try:
                # Convert asset_id to integer if it's a string
                asset_id = int(value)
                self._update_asset_url(asset_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid asset_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update asset_url for asset {value}: {e}")

        return super().after_value_set(parameter, value)

    def process(self) -> None:
        self._clear_execution_status()
        try:
            # Get input parameters
            asset_id = self.get_parameter_value("asset_id")
            asset_name = self.get_parameter_value("asset_name")
            asset_code = self.get_parameter_value("asset_code")
            asset_type = self.get_parameter_value("asset_type")
            asset_description = self.get_parameter_value("asset_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not asset_id:
                logger.error(f"{self.name}: asset_id is required")
                return

            # Convert asset_id to integer if it's a string
            try:
                asset_id = int(asset_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: asset_id must be a valid integer")
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Prepare update data for asset fields
            update_data = {}
            has_updates = False

            # Note: Assets in ShotGrid don't have names, only codes
            # The asset_name parameter is ignored for backward compatibility
            if asset_name is not None:
                logger.warning(
                    f"{self.name}: asset_name parameter is ignored - assets in ShotGrid only have codes, not names"
                )

            if asset_code is not None:
                update_data["code"] = asset_code
                has_updates = True

            if asset_type is not None:
                update_data["sg_asset_type"] = asset_type
                has_updates = True

            if asset_description is not None:
                update_data["description"] = asset_description
                has_updates = True

            # Update asset fields if any are provided
            if has_updates:
                logger.info(f"{self.name}: Updating asset fields")
                try:
                    # Try password authentication first for better permissions
                    try:
                        access_token = self._get_access_token_with_password()
                        logger.info(f"{self.name}: Using password authentication")
                    except Exception as e:
                        logger.warning(
                            f"{self.name}: Password authentication failed, falling back to client credentials: {e}"
                        )
                        access_token = self._get_access_token()

                    update_url = f"{base_url}api/v1/entity/assets/{asset_id}"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Updating asset {asset_id} with data: {update_data}")

                    with httpx.Client() as client:
                        response = client.put(update_url, headers=headers, json=update_data)
                        response.raise_for_status()

                        data = response.json()
                        updated_asset = data.get("data", {})
                        logger.info(f"{self.name}: Asset fields updated successfully")

                except Exception as e:
                    logger.error(f"{self.name}: Failed to update asset fields: {e}")
                    raise

            # Upload thumbnail if provided
            if thumbnail_image:
                logger.info(f"{self.name}: Uploading thumbnail for asset {asset_id}")
                try:
                    self._update_entity_thumbnail("assets", asset_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail uploaded successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to upload thumbnail: {e}")
                    # Don't fail the entire operation if thumbnail upload fails
                    # The asset fields were still updated successfully

            # Check if we have any updates (fields or thumbnail)
            if not has_updates and not thumbnail_image:
                logger.error(f"{self.name}: At least one field to update or thumbnail must be provided")
                return

            # Get final asset data
            try:
                asset_url = f"{base_url}api/v1/entity/assets/{asset_id}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }

                with httpx.Client() as client:
                    response = client.get(asset_url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    final_asset_data = data.get("data", {})
                    logger.info(f"{self.name}: Retrieved final asset data")
            except Exception as e:
                logger.warning(f"{self.name}: Could not get final asset data: {e}")
                # Use the updated asset data if we can't get the final data
                final_asset_data = updated_asset

            # Output the results
            self.parameter_output_values["updated_asset"] = final_asset_data

            self._set_status_results(was_successful=True, result_details=f"Successfully updated asset {asset_id}")

            # Update the asset_url output
            self._update_asset_url(asset_id)

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
