import urllib.parse
from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from image_utils import convert_image_for_shotgrid, get_mime_type, should_convert_image

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

    def _get_upload_url(self, sequence_id: int, filename: str, access_token: str, base_url: str) -> dict:
        """Get upload URL for sequence thumbnail"""
        try:
            encoded_filename = urllib.parse.quote(filename)
            upload_url = f"{base_url}api/v1/entity/sequences/{sequence_id}/image/_upload?filename={encoded_filename}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Requesting upload URL for sequence {sequence_id} with filename '{filename}'")

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

    def _complete_upload(self, sequence_id: int, upload_info: dict, access_token: str, base_url: str) -> dict:
        """Complete the upload process and return the file ID"""
        try:
            complete_url = f"{base_url}api/v1/entity/sequences/{sequence_id}/image/_upload"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            complete_data = {"upload_info": upload_info, "upload_data": {}}

            logger.info(f"{self.name}: Completing upload for sequence {sequence_id}")

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

    def _update_sequence_thumbnail(self, sequence_id: int, thumbnail_image, access_token: str, base_url: str) -> str:
        """Update the sequence thumbnail and return the file ID"""
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
                    filename = "sequence_thumbnail.jpg"

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
            upload_response = self._get_upload_url(sequence_id, filename, access_token, base_url)

            logger.info(f"{self.name}: Full upload response: {upload_response}")

            upload_url = upload_response.get("links", {}).get("upload")
            upload_info = upload_response.get("data", {})

            if not upload_url:
                logger.error(f"{self.name}: No upload URL found in response")
                raise Exception("Failed to get upload URL from ShotGrid")

            logger.info(f"{self.name}: Uploading file")
            upload_result = self._upload_file_to_url(upload_url, image_bytes, mime_type)

            logger.info(f"{self.name}: Completing upload")
            completion_response = self._complete_upload(sequence_id, upload_info, access_token, base_url)

            upload_id = completion_response.get("data", {}).get("id")

            if not upload_id:
                logger.info(f"{self.name}: No file ID in completion response, checking sequence image field")
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
                        sequence_data = data.get("data", {})
                        upload_id = sequence_data.get("attributes", {}).get("image")

                        if upload_id:
                            logger.info(f"{self.name}: Found file ID in sequence image field: {upload_id}")
                            if "thumbnail_pending" in str(upload_id):
                                logger.info(f"{self.name}: Thumbnail is still processing")
                                upload_id = "pending_thumbnail"
                except Exception as e:
                    logger.warning(f"{self.name}: Could not get sequence data: {e}")
                    upload_id = "uploaded_file"

            return upload_id

        except Exception as e:
            logger.error(f"{self.name}: Failed to update sequence thumbnail: {e}")
            raise

    def process(self) -> None:
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
                        upload_id = self._update_sequence_thumbnail(sequence_id, thumbnail_image, access_token, base_url)
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

                logger.info(f"{self.name}: Successfully created sequence {sequence_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error creating sequence: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error creating sequence: {e}")







