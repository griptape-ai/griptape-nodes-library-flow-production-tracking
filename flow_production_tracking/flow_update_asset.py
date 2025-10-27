import urllib.parse
from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from image_utils import convert_image_for_shotgrid, get_mime_type, should_convert_image

from griptape_nodes.exe_types.core_types import Parameter, ParameterGroup, ParameterMessage, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowUpdateAsset(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Dynamic message that will be updated with the updated asset link - placed at top for prominence
        self.asset_message = ParameterMessage(
            name="asset_message",
            title="Asset Management",
            value="Update an asset to see the link to view it in ShotGrid. Click the button to view all assets.",
            button_link="",
            button_text="View All Assets",
            variant="info",
            full_width=True,
        )
        self.add_node_element(self.asset_message)

        # Set the initial link to the main assets page
        self._update_asset_message_initial()

        with ParameterGroup(name="asset_input") as asset_input:
            self.add_parameter(
                Parameter(
                    name="asset_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the asset to update.",
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

    def _download_image_from_url(self, image_url: str) -> bytes:
        """Download image from URL and return as bytes"""
        try:
            with httpx.Client() as client:
                response = client.get(image_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"{self.name}: Failed to download image from URL: {e}")
            raise

    def _get_upload_url(self, asset_id: int, filename: str, access_token: str, base_url: str) -> dict:
        """Get upload URL for asset thumbnail"""
        try:
            # URL-encode the filename to handle special characters
            encoded_filename = urllib.parse.quote(filename)
            upload_url = f"{base_url}api/v1/entity/assets/{asset_id}/image/_upload?filename={encoded_filename}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Requesting upload URL for asset {asset_id} with filename '{filename}'")

            with httpx.Client() as client:
                response = client.get(upload_url, headers=headers)
                response.raise_for_status()

                data = response.json()
                logger.info(f"{self.name}: Got upload URL response")
                return data

        except Exception as e:
            logger.error(f"{self.name}: Failed to get upload URL: {e}")
            raise

    def _upload_file_to_url(self, upload_url: str, image_bytes: bytes, mime_type: str) -> dict:
        """Upload file to the provided upload URL"""
        try:
            headers = {
                "Content-Type": mime_type,
                "Content-Length": str(len(image_bytes)),
            }

            logger.info(f"{self.name}: Uploading file to ShotGrid")

            with httpx.Client() as client:
                response = client.put(upload_url, headers=headers, content=image_bytes)
                response.raise_for_status()

                # Try to parse JSON response if available
                try:
                    data = response.json()
                    logger.info(f"{self.name}: File uploaded successfully with response data")
                    return data
                except:
                    # If no JSON response, that's okay for S3 uploads
                    logger.info(f"{self.name}: File uploaded successfully (no JSON response)")
                    return {"success": True}

        except Exception as e:
            logger.error(f"{self.name}: Failed to upload file: {e}")
            raise

    def _complete_upload(self, asset_id: int, upload_info: dict, access_token: str, base_url: str) -> dict:
        """Complete the upload process and return the file ID"""
        try:
            complete_url = f"{base_url}api/v1/entity/assets/{asset_id}/image/_upload"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Try different completion data structures
            # Option 1: Just the upload_info
            # complete_data = upload_info

            # Option 2: Wrap in upload_info key (if that's what the API expects)
            # complete_data = {"upload_info": upload_info}

            # Option 3: Include additional fields that might be required
            complete_data = {"upload_info": upload_info, "upload_data": {}}

            logger.info(f"{self.name}: Completing upload for asset {asset_id}")

            with httpx.Client() as client:
                response = client.post(complete_url, headers=headers, json=complete_data)

                # Log the response for debugging
                logger.info(f"{self.name}: Completion response status: {response.status_code}")

                response.raise_for_status()

                # Handle empty response (which is normal for successful completion)
                if response.text.strip():
                    try:
                        data = response.json()
                        logger.info(f"{self.name}: Completion response: {data}")
                    except:
                        logger.info(f"{self.name}: Completion response text: {response.text}")
                        data = {"success": True}
                else:
                    logger.info(f"{self.name}: Completion successful (empty response)")
                    data = {"success": True}

                logger.info(f"{self.name}: Upload completed successfully")
                return data

        except Exception as e:
            logger.error(f"{self.name}: Failed to complete upload: {e}")
            raise

    def _get_asset_data(self, asset_id: int, access_token: str, base_url: str) -> dict:
        """Get asset data to check if image field was updated"""
        try:
            asset_url = f"{base_url}api/v1/entity/assets/{asset_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Getting asset data for {asset_id}")

            with httpx.Client() as client:
                response = client.get(asset_url, headers=headers)
                response.raise_for_status()

                data = response.json()
                logger.info(f"{self.name}: Got asset data")
                return data

        except Exception as e:
            logger.error(f"{self.name}: Failed to get asset data: {e}")
            raise

    def _update_asset_thumbnail(self, asset_id: int, thumbnail_image, access_token: str, base_url: str) -> str:
        """Update the asset thumbnail and return the file ID"""
        try:
            # Step 1: Download the image from the URL
            logger.info(f"{self.name}: Downloading image from URL")
            thumbnail_url = thumbnail_image.value
            image_bytes = self._download_image_from_url(thumbnail_url)

            # Step 2: Determine filename and MIME type
            # Extract filename from URL or generate one
            if hasattr(thumbnail_image, "name") and thumbnail_image.name:
                filename = thumbnail_image.name
            else:
                # Generate filename from URL
                url_path = thumbnail_url.split("/")[-1]
                if "?" in url_path:
                    url_path = url_path.split("?")[0]
                # Ensure we have a valid filename with extension
                if "." in url_path and len(url_path) > 1:
                    filename = url_path
                else:
                    # Default filename if we can't extract one
                    filename = "asset_thumbnail.jpg"

            # Clean up filename - remove any problematic characters
            filename = filename.replace(" ", "_").replace("&", "and")

            # Ensure filename has an extension
            if "." not in filename:
                filename += ".jpg"

            # Step 2.5: Convert image if needed (e.g., WebP to PNG)
            if should_convert_image(filename):
                logger.info(f"{self.name}: Converting image format for ShotGrid compatibility")
                image_bytes, filename = convert_image_for_shotgrid(image_bytes, filename)
                logger.info(f"{self.name}: Converted to {filename}")

            # Determine MIME type
            mime_type = get_mime_type(filename)

            logger.info(f"{self.name}: Using filename '{filename}' with MIME type '{mime_type}'")

            # Step 3: Get upload URL
            logger.info(f"{self.name}: Getting upload URL")
            upload_response = self._get_upload_url(asset_id, filename, access_token, base_url)

            # Log the full response for debugging
            logger.info(f"{self.name}: Full upload response: {upload_response}")

            upload_url = upload_response.get("links", {}).get("upload")
            upload_info = upload_response.get("data", {})

            if not upload_url:
                logger.error(f"{self.name}: No upload URL found in response")
                logger.error(f"{self.name}: Available keys in response: {list(upload_response.keys())}")
                if "links" in upload_response:
                    logger.error(f"{self.name}: Available links: {list(upload_response['links'].keys())}")
                raise Exception("Failed to get upload URL from ShotGrid")

            # Step 4: Upload the file
            logger.info(f"{self.name}: Uploading file")
            upload_result = self._upload_file_to_url(upload_url, image_bytes, mime_type)

            # Step 5: Complete the upload
            logger.info(f"{self.name}: Completing upload")
            completion_response = self._complete_upload(asset_id, upload_info, access_token, base_url)

            # Get the file ID from the completion response
            upload_id = completion_response.get("data", {}).get("id")

            if not upload_id:
                logger.info(f"{self.name}: No file ID in completion response, checking asset image field")
                # If no file ID in completion response, the upload might have automatically
                # updated the asset's image field. Let's get the current asset data.
                try:
                    asset_response = self._get_asset_data(asset_id, access_token, base_url)
                    asset_data = asset_response.get("data", {})
                    upload_id = asset_data.get("attributes", {}).get("image")

                    if upload_id:
                        logger.info(f"{self.name}: Found file ID in asset image field: {upload_id}")
                        # Check if it's a pending thumbnail URL
                        if "thumbnail_pending" in upload_id:
                            logger.info(f"{self.name}: Thumbnail is still processing, not updating asset")
                            upload_id = "pending_thumbnail"
                    else:
                        logger.warning(f"{self.name}: No file ID found in asset image field")
                        # Continue anyway - the upload might have succeeded
                        upload_id = "uploaded_file"  # Placeholder
                except Exception as e:
                    logger.warning(f"{self.name}: Could not get asset data: {e}")
                    upload_id = "uploaded_file"  # Placeholder

            return upload_id

        except Exception as e:
            logger.error(f"{self.name}: Failed to update asset thumbnail: {e}")
            raise

    def _update_asset_message(self, asset_id: int, asset_code: str) -> None:
        """Update the ParameterMessage with a link to the updated asset in ShotGrid."""
        try:
            # Get the base URL from config
            base_url = self._get_shotgrid_config()["base_url"]

            # Create the ShotGrid URL for the asset
            shotgrid_url = f"{base_url}detail/Asset/{asset_id}"

            # Update the ParameterMessage
            message_param = self.get_element_by_name_and_type("asset_message", ParameterMessage)
            message_param.button_text = f"View Asset: {asset_code}"
            message_param.button_link = shotgrid_url
            message_param.value = (
                f"Asset '{asset_code}' (ID: {asset_id}) updated successfully! Click the button to view it in ShotGrid."
            )

            logger.info(f"{self.name}: Updated asset message with link: {shotgrid_url}")

        except Exception as e:
            logger.warning(f"{self.name}: Failed to update asset message: {e}")

    def _update_asset_message_initial(self) -> None:
        """Update the ParameterMessage to show a link to the main assets page."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            message_param = self.get_element_by_name_and_type("asset_message", ParameterMessage)
            message_param.button_text = "View All Assets"
            message_param.button_link = f"{base_url}assets"
            message_param.value = (
                "Update an asset to see the link to view it in ShotGrid. Click the button to view all assets."
            )
            logger.info(f"{self.name}: Updated asset message to show main assets page link.")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update asset message to show main assets page: {e}")

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update the ParameterMessage when asset_id changes to show a link to that specific asset."""
        if parameter.name == "asset_id" and value:
            try:
                # Get access token and base URL
                access_token = self._get_access_token()
                base_url = self._get_shotgrid_config()["base_url"]

                # Make API call to get asset data (which includes the proper URL)
                asset_url = f"{base_url}api/v1/entity/assets/{value}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }

                with httpx.Client() as client:
                    response = client.get(asset_url, headers=headers)
                    if response.status_code == 200:
                        asset_data = response.json()
                        # Get the self link from the asset data
                        shotgrid_url = asset_data.get("data", {}).get("links", {}).get("self", "")

                        if shotgrid_url:
                            # Construct the full URL by combining base URL with the self link
                            # The self link is relative (e.g., "/api/v1/entity/assets/2027")
                            # We need to convert it to a web URL (e.g., "https://griptape-ai.shotgrid.autodesk.com/detail/Asset/2027")
                            full_url = f"{base_url}detail/Asset/{value}"

                            # Update the ParameterMessage to show the specific asset
                            message_param = self.get_element_by_name_and_type("asset_message", ParameterMessage)
                            message_param.button_text = f"View Asset (ID: {value})"
                            message_param.button_link = full_url
                            message_param.value = f"Update asset ID {value}. Click the button to view it in ShotGrid."

                            logger.info(f"{self.name}: Updated asset message to show asset {value}")
                        else:
                            logger.warning(f"{self.name}: No self link found in asset data for {value}")
                    else:
                        logger.warning(f"{self.name}: Failed to get asset data for {value}: {response.status_code}")

            except Exception as e:
                logger.warning(f"{self.name}: Failed to update asset message for asset {value}: {e}")

        return super().after_value_set(parameter, value)

    def process(self) -> None:
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
                    upload_id = self._update_asset_thumbnail(asset_id, thumbnail_image, access_token, base_url)
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

            logger.info(f"{self.name}: Successfully updated asset {asset_id}")

            # Update the ParameterMessage with a link to the updated asset
            self._update_asset_message(asset_id, asset_code)

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
