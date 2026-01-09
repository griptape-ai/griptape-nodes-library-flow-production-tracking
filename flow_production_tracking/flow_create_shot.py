import urllib.parse
from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from image_utils import convert_image_for_shotgrid, get_mime_type, should_convert_image

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowCreateShot(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to create the shot in (required).",
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_id",
                type="string",
                default_value=None,
                tooltip="The ID of the sequence to create the shot in (optional). Note: Sequences belong to episodes, so shots are linked to episodes through their sequence.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="shot_code",
                default_value=None,
                tooltip="The code/name for the shot to create.",
                placeholder_text="Enter the code for the shot to create.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="shot_description",
                type="string",
                default_value=None,
                tooltip="The description for the shot to create.",
                multiline=True,
                placeholder_text="Enter the description for the shot to create.",
            )
        )
        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The thumbnail image for the shot (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="shot_id",
                default_value=None,
                tooltip="The ID of the newly created shot.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The ID of the newly created shot.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="shot_url",
                default_value="",
                tooltip="The URL of the newly created shot.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The URL of the newly created shot.",
            )
        )
        self.add_parameter(
            Parameter(
                name="created_shot",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The created shot data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

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

    def _get_upload_url(self, shot_id: int, filename: str, access_token: str, base_url: str) -> dict:
        """Get upload URL for shot thumbnail"""
        try:
            encoded_filename = urllib.parse.quote(filename)
            upload_url = f"{base_url}api/v1/entity/shots/{shot_id}/image/_upload?filename={encoded_filename}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Requesting upload URL for shot {shot_id} with filename '{filename}'")

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

                try:
                    data = response.json()
                    logger.info(f"{self.name}: File uploaded successfully with response data")
                    return data
                except:
                    logger.info(f"{self.name}: File uploaded successfully (no JSON response)")
                    return {"success": True}

        except Exception as e:
            logger.error(f"{self.name}: Failed to upload file: {e}")
            raise

    def _complete_upload(self, shot_id: int, upload_info: dict, access_token: str, base_url: str) -> dict:
        """Complete the upload process and return the file ID"""
        try:
            complete_url = f"{base_url}api/v1/entity/shots/{shot_id}/image/_upload"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            complete_data = {"upload_info": upload_info, "upload_data": {}}

            logger.info(f"{self.name}: Completing upload for shot {shot_id}")

            with httpx.Client() as client:
                response = client.post(complete_url, headers=headers, json=complete_data)

                logger.info(f"{self.name}: Completion response status: {response.status_code}")

                response.raise_for_status()

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

    def _update_shot_thumbnail(self, shot_id: int, thumbnail_image, access_token: str, base_url: str) -> str:
        """Update the shot thumbnail and return the file ID"""
        try:
            logger.info(f"{self.name}: Downloading image from URL")
            thumbnail_url = thumbnail_image.value
            image_bytes = self._download_image_from_url(thumbnail_url)

            if hasattr(thumbnail_image, "name") and thumbnail_image.name:
                filename = thumbnail_image.name
            else:
                url_path = thumbnail_url.split("/")[-1]
                if "?" in url_path:
                    url_path = url_path.split("?")[0]
                if "." in url_path and len(url_path) > 1:
                    filename = url_path
                else:
                    filename = "shot_thumbnail.jpg"

            filename = filename.replace(" ", "_").replace("&", "and")

            if "." not in filename:
                filename += ".jpg"

            if should_convert_image(filename):
                logger.info(f"{self.name}: Converting image format for ShotGrid compatibility")
                image_bytes, filename = convert_image_for_shotgrid(image_bytes, filename)
                logger.info(f"{self.name}: Converted to {filename}")

            mime_type = get_mime_type(filename)

            logger.info(f"{self.name}: Using filename '{filename}' with MIME type '{mime_type}'")

            logger.info(f"{self.name}: Getting upload URL")
            upload_response = self._get_upload_url(shot_id, filename, access_token, base_url)

            logger.info(f"{self.name}: Full upload response: {upload_response}")

            upload_url = upload_response.get("links", {}).get("upload")
            upload_info = upload_response.get("data", {})

            if not upload_url:
                logger.error(f"{self.name}: No upload URL found in response")
                raise Exception("Failed to get upload URL from ShotGrid")

            logger.info(f"{self.name}: Uploading file")
            upload_result = self._upload_file_to_url(upload_url, image_bytes, mime_type)

            logger.info(f"{self.name}: Completing upload")
            completion_response = self._complete_upload(shot_id, upload_info, access_token, base_url)

            upload_id = completion_response.get("data", {}).get("id")

            if not upload_id:
                logger.info(f"{self.name}: No file ID in completion response, checking shot image field")
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
                        shot_data = data.get("data", {})
                        upload_id = shot_data.get("attributes", {}).get("image")

                        if upload_id:
                            logger.info(f"{self.name}: Found file ID in shot image field: {upload_id}")
                            if "thumbnail_pending" in str(upload_id):
                                logger.info(f"{self.name}: Thumbnail is still processing")
                                upload_id = "pending_thumbnail"
                except Exception as e:
                    logger.warning(f"{self.name}: Could not get shot data: {e}")
                    upload_id = "uploaded_file"

            return upload_id

        except Exception as e:
            logger.error(f"{self.name}: Failed to update shot thumbnail: {e}")
            raise

    def process(self) -> None:
        """Create a new shot in ShotGrid."""
        try:
            project_id = self.get_parameter_value("project_id")
            sequence_id = self.get_parameter_value("sequence_id")
            shot_code = self.get_parameter_value("shot_code")
            shot_description = self.get_parameter_value("shot_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")

            if not project_id:
                logger.error(f"{self.name}: project_id is required")
                return

            if not shot_code:
                logger.error(f"{self.name}: shot_code is required")
                return

            try:
                project_id = int(project_id)
                if sequence_id:
                    sequence_id = int(sequence_id)
            except (ValueError, TypeError) as e:
                logger.error(f"{self.name}: project_id and sequence_id (if provided) must be valid integers: {e}")
                return

            try:
                access_token = self._get_access_token_with_password()
                logger.info(f"{self.name}: Using password authentication")
            except Exception as e:
                logger.warning(f"{self.name}: Password authentication failed, falling back to client credentials: {e}")
                access_token = self._get_access_token()

            base_url = self._get_shotgrid_config()["base_url"]

            shot_data = {
                "code": shot_code,
                "project": {"type": "Project", "id": project_id},
            }

            # Add sequence if provided
            # Note: Shots link to episodes through sequences (sequences belong to episodes)
            if sequence_id:
                shot_data["sg_sequence"] = {"type": "Sequence", "id": sequence_id}

            if shot_description:
                shot_data["description"] = shot_description

            logger.info(f"{self.name}: Creating shot with data: {shot_data}")

            create_url = f"{base_url}api/v1/entity/shots"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            with httpx.Client() as client:
                response = client.post(create_url, headers=headers, json=shot_data)
                response.raise_for_status()

                data = response.json()
                created_shot = data.get("data", {})
                shot_id = created_shot.get("id")

                if not shot_id:
                    logger.error(f"{self.name}: No shot ID returned from creation")
                    return

                logger.info(f"{self.name}: Shot created successfully with ID: {shot_id}")

                if thumbnail_image:
                    logger.info(f"{self.name}: Uploading thumbnail for shot {shot_id}")
                    try:
                        upload_id = self._update_shot_thumbnail(shot_id, thumbnail_image, access_token, base_url)
                        logger.info(f"{self.name}: Thumbnail uploaded successfully")
                    except Exception as e:
                        logger.error(f"{self.name}: Failed to upload thumbnail: {e}")

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
                    final_shot_data = created_shot

                self.parameter_output_values["shot_id"] = str(shot_id)
                self.publish_update_to_parameter("shot_id", str(shot_id))

                self.parameter_output_values["created_shot"] = final_shot_data
                self.publish_update_to_parameter("created_shot", final_shot_data)

                self._update_shot_url(shot_id)

                logger.info(f"{self.name}: Successfully created shot {shot_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error creating shot: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error creating shot: {e}")

