import time
import urllib.parse

import httpx
from griptape_nodes.exe_types.node_types import SuccessFailureNode
from griptape_nodes.files.file import File
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
from image_utils import convert_image_for_shotgrid, get_mime_type, should_convert_image


class BaseShotGridNode(SuccessFailureNode):
    """Base class for all ShotGrid nodes with authentication handling."""

    # Class-level cache for the access token
    _access_token = None
    _token_expires_at = None

    SERVICE = "Autodesk"
    API_KEY_ENV_VAR = "SHOTGRID_API_KEY"
    SHOTGRID_URL_ENV_VAR = "SHOTGRID_URL"
    SCRIPT_NAME_ENV_VAR = "SHOTGRID_SCRIPT_NAME"

    def _get_access_token(self) -> str:
        """Get or refresh the access token using API key authentication."""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at and time.time() < self._token_expires_at:
            return self._access_token

        # Use API key authentication
        return self._get_access_token_api_key()

    def _get_access_token_api_key(self) -> str:
        """Get access token using API key authentication."""
        # Get configuration
        config = self._get_shotgrid_config()
        api_key = config["api_key"]
        base_url = config["base_url"]

        if not api_key:
            error_msg = "No API key available. Please configure SHOTGRID_API_KEY in settings."
            raise ValueError(error_msg)

        # Get script name from config
        script_name = GriptapeNodes.SecretsManager().get_secret(self.SCRIPT_NAME_ENV_VAR) or "Griptape Nodes"

        # Get a new token using client credentials
        auth_url = f"{base_url}api/v1/auth/access_token"
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": script_name,
            "client_secret": api_key,
        }
        auth_headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

        try:
            auth_response = httpx.post(auth_url, data=auth_data, headers=auth_headers)
            auth_response.raise_for_status()

            token_data = auth_response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour

            if not access_token:
                error_msg = "Failed to get access token from ShotGrid"
                raise ValueError(error_msg)

            # Cache the token
            self._access_token = access_token
            self._token_expires_at = time.time() + expires_in - 300  # Expire 5 minutes early

            return access_token

        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def _download_image_from_url(self, image_url: str) -> bytes:
        """Download image from URL or workspace path and return as bytes."""
        try:
            return File(image_url).read_bytes()
        except Exception as e:
            logger.error(f"{self.name}: Failed to download image from URL: {e}")
            raise

    def _get_upload_url(
        self, entity_type_plural: str, entity_id: int, filename: str, access_token: str, base_url: str
    ) -> dict:
        """Get upload URL for an entity thumbnail."""
        try:
            encoded_filename = urllib.parse.quote(filename)
            upload_url = (
                f"{base_url}api/v1/entity/{entity_type_plural}/{entity_id}/image/_upload?filename={encoded_filename}"
            )
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            logger.info(
                f"{self.name}: Requesting upload URL for {entity_type_plural} {entity_id} with filename '{filename}'"
            )
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
        """Upload file to the provided upload URL."""
        try:
            headers = {"Content-Type": mime_type, "Content-Length": str(len(image_bytes))}
            logger.info(f"{self.name}: Uploading file to ShotGrid")
            with httpx.Client() as client:
                response = client.put(upload_url, headers=headers, content=image_bytes)
                response.raise_for_status()
                try:
                    data = response.json()
                    logger.info(f"{self.name}: File uploaded successfully with response data")
                    return data
                except Exception:
                    logger.info(f"{self.name}: File uploaded successfully (no JSON response)")
                    return {"success": True}
        except Exception as e:
            logger.error(f"{self.name}: Failed to upload file: {e}")
            raise

    def _complete_upload(
        self, entity_type_plural: str, entity_id: int, upload_info: dict, access_token: str, base_url: str
    ) -> dict:
        """Complete the upload process."""
        try:
            complete_url = f"{base_url}api/v1/entity/{entity_type_plural}/{entity_id}/image/_upload"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            complete_data = {"upload_info": upload_info, "upload_data": {}}
            logger.info(f"{self.name}: Completing upload for {entity_type_plural} {entity_id}")
            with httpx.Client() as client:
                response = client.post(complete_url, headers=headers, json=complete_data)
                logger.info(f"{self.name}: Completion response status: {response.status_code}")
                response.raise_for_status()
                if response.text.strip():
                    try:
                        data = response.json()
                        logger.info(f"{self.name}: Completion response: {data}")
                    except Exception:
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

    def _update_entity_thumbnail(
        self, entity_type_plural: str, entity_id: int, thumbnail_image, access_token: str, base_url: str
    ) -> str:
        """Upload a thumbnail image for any ShotGrid entity type."""
        try:
            logger.info(f"{self.name}: Downloading image from URL")
            if hasattr(thumbnail_image, "value"):
                thumbnail_url = thumbnail_image.value
            elif isinstance(thumbnail_image, dict):
                thumbnail_url = thumbnail_image.get("value") or thumbnail_image.get("url")
            elif isinstance(thumbnail_image, str):
                thumbnail_url = thumbnail_image
            else:
                raise ValueError(f"Unsupported thumbnail_image type: {type(thumbnail_image)}")

            image_bytes = self._download_image_from_url(thumbnail_url)

            if hasattr(thumbnail_image, "name") and thumbnail_image.name:
                filename = thumbnail_image.name
            else:
                url_path = thumbnail_url.split("/")[-1]
                if "?" in url_path:
                    url_path = url_path.split("?")[0]
                filename = url_path if ("." in url_path and len(url_path) > 1) else "thumbnail.jpg"

            filename = filename.replace(" ", "_").replace("&", "and")
            if "." not in filename:
                filename += ".jpg"

            if should_convert_image(filename):
                logger.info(f"{self.name}: Converting image format for ShotGrid compatibility")
                image_bytes, filename = convert_image_for_shotgrid(image_bytes, filename)
                logger.info(f"{self.name}: Converted to {filename}")

            mime_type = get_mime_type(filename)
            logger.info(f"{self.name}: Using filename '{filename}' with MIME type '{mime_type}'")

            upload_response = self._get_upload_url(entity_type_plural, entity_id, filename, access_token, base_url)
            logger.info(f"{self.name}: Full upload response: {upload_response}")

            upload_url = upload_response.get("links", {}).get("upload")
            upload_info = upload_response.get("data", {})

            if not upload_url:
                logger.error(f"{self.name}: No upload URL found in response")
                logger.error(f"{self.name}: Available keys in response: {list(upload_response.keys())}")
                if "links" in upload_response:
                    logger.error(f"{self.name}: Available links: {list(upload_response['links'].keys())}")
                raise Exception("Failed to get upload URL from ShotGrid")

            self._upload_file_to_url(upload_url, image_bytes, mime_type)

            completion_response = self._complete_upload(
                entity_type_plural, entity_id, upload_info, access_token, base_url
            )
            upload_id = completion_response.get("data", {}).get("id")

            if not upload_id:
                logger.info(f"{self.name}: No file ID in completion response, checking entity image field")
                try:
                    entity_url = f"{base_url}api/v1/entity/{entity_type_plural}/{entity_id}"
                    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
                    with httpx.Client() as client:
                        response = client.get(entity_url, headers=headers)
                        response.raise_for_status()
                        entity_data = response.json().get("data", {})
                        upload_id = entity_data.get("attributes", {}).get("image")
                        if upload_id:
                            logger.info(f"{self.name}: Found file ID in entity image field: {upload_id}")
                            if "thumbnail_pending" in str(upload_id):
                                logger.info(f"{self.name}: Thumbnail is still processing")
                                upload_id = "pending_thumbnail"
                        else:
                            logger.warning(f"{self.name}: No file ID found in entity image field")
                            upload_id = "uploaded_file"
                except Exception as e:
                    logger.warning(f"{self.name}: Could not get entity data: {e}")
                    upload_id = "uploaded_file"

            return upload_id

        except Exception as e:
            logger.error(f"{self.name}: Failed to update {entity_type_plural} thumbnail: {e}")
            raise

    def _get_shotgrid_config(self) -> dict:
        """Get ShotGrid configuration values."""
        api_key = GriptapeNodes.SecretsManager().get_secret(self.API_KEY_ENV_VAR)
        base_url = GriptapeNodes.SecretsManager().get_secret(self.SHOTGRID_URL_ENV_VAR)
        script_name = GriptapeNodes.SecretsManager().get_secret(self.SCRIPT_NAME_ENV_VAR) or "Griptape Nodes"

        if not base_url.endswith("/"):
            base_url += "/"

        return {
            "api_key": api_key,
            "base_url": base_url,
            "script_name": script_name,
        }
