import os
from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import (
    Parameter,
    ParameterMode,
)
from griptape_nodes.exe_types.node_types import AsyncResult
from griptape_nodes.exe_types.param_components.progress_bar_component import ProgressBarComponent
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.events.parameter_events import SetParameterValueRequest
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
from griptape_nodes.traits.file_system_picker import FileSystemPicker
from griptape_nodes.traits.options import Options

# Common ShotGrid entity types that can have files
ENTITY_TYPES = [
    "Unknown",
    "Asset",
    "Shot",
    "Sequence",
    "Project",
    "Task",
    "Version",
    "Note",
    "Playlist",
    "CustomEntity01",
    "CustomEntity02",
    "CustomEntity03",
    "CustomEntity04",
    "CustomEntity05",
    "CustomEntity06",
    "CustomEntity07",
    "CustomEntity08",
    "CustomEntity09",
    "CustomEntity10",
]


class FlowUploadFile(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Instance variables for async processing
        self._file_data: bytes = b""
        self._original_filename: str = ""
        self._content_type: str = ""
        self._final_filename: str = ""
        self._version_data: dict = {}

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="entity_type",
                default_value=ENTITY_TYPES[0],  # Default to "Unknown"
                tooltip="The type of entity to upload file to. Select 'Unknown' to auto-detect from entity_id.",
                placeholder_text="Select entity type or choose 'Unknown' for auto-detection",
                traits={
                    Options(choices=ENTITY_TYPES),
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_id",
                default_value=None,
                tooltip="The ID of the entity to upload file to.",
                placeholder_text="Enter entity ID (e.g., 1234)",
            )
        )
        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="Project ID for the upload (required for version creation).",
                placeholder_text="Enter project ID (e.g., 1234)",
            )
        )
        self.add_parameter(
            ParameterString(
                name="file_path",
                default_value=None,
                tooltip="Path to the file to upload (local file path or URL).",
                placeholder_text="Enter file path or URL",
                traits={
                    FileSystemPicker(
                        workspace_only=False,
                        allow_files=True,
                        allow_directories=False,
                        allow_create=False,
                        allow_rename=True,
                    )
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="file_name",
                default_value=None,
                tooltip="Name for the uploaded file (optional). If not provided, uses the original filename.",
                placeholder_text="Enter custom filename (optional)",
            )
        )
        self.add_parameter(
            ParameterString(
                name="description",
                default_value=None,
                tooltip="Description for the uploaded file (optional).",
                placeholder_text="Enter file description (optional)",
            )
        )

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="upload_url",
                default_value="",
                tooltip="URL to view the uploaded version in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_url",
                default_value="",
                tooltip="URL to view the entity (Task/Asset/etc.) where the version was uploaded",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="version_id",
                type="str",
                default_value="",
                tooltip="ID of the created version",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="file_name_output",
                default_value="",
                tooltip="Name of the uploaded file",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="file_size",
                default_value="",
                tooltip="Size of the uploaded file in bytes",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        # Initialize progress bar component
        self.progress_bar_component = ProgressBarComponent(self)
        self.progress_bar_component.add_property_parameters()
        self.add_parameter(
            ParameterString(
                name="upload_status",
                default_value="",
                tooltip="Status of the upload operation",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="version_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the created version",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "entity_id" and value:
            # If entity_type is "Unknown", try to auto-detect it
            entity_type = self.get_parameter_value("entity_type")
            if entity_type == "Unknown":
                detected_type = self._detect_entity_type(str(value))
                if detected_type:
                    # Update the entity_type parameter with the detected value
                    GriptapeNodes.handle_request(
                        SetParameterValueRequest(parameter_name="entity_type", value=detected_type, node_name=self.name)
                    )
                    self.parameter_output_values["entity_type"] = detected_type
                    self.publish_update_to_parameter("entity_type", detected_type)
        return super().after_value_set(parameter, value)

    def _detect_entity_type(self, entity_id: str) -> str | None:
        """Attempt to auto-detect entity type by trying common entity types."""
        if not entity_id:
            return None

        # Try the most common entity types first
        common_types = ["Asset", "Shot", "Task", "Project", "Version", "Sequence"]

        access_token = self._get_access_token()
        base_url = self._get_shotgrid_config()["base_url"]
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        for entity_type in common_types:
            try:
                # Convert entity type to API format
                entity_type_lower = entity_type.lower()
                if entity_type_lower == "humanuser":
                    entity_type_lower = "human_users"
                else:
                    entity_type_lower = f"{entity_type_lower}s"

                url = f"{base_url}api/v1/entity/{entity_type_lower}/{entity_id}"

                with httpx.Client() as client:
                    response = client.get(url, headers=headers, params={"fields": "id"})
                    if response.status_code == 200:
                        logger.info(f"{self.name}: Auto-detected entity type as {entity_type}")
                        return entity_type
            except Exception:
                continue

        logger.warning(f"{self.name}: Could not auto-detect entity type for ID {entity_id}")
        return None

    def _resolve_localhost_url(self, file_path: str) -> str:
        """Convert localhost workspace URL to absolute filesystem path."""
        if not file_path.startswith(("http://localhost", "http://127.0.0.1")):
            return file_path

        # Strip query parameters
        clean_url = file_path.split("?")[0]

        # Extract the workspace-relative path (after /workspace/)
        if "/workspace/" in clean_url:
            workspace_relative = clean_url.split("/workspace/", 1)[1]
            workspace_path = GriptapeNodes.ConfigManager().workspace_path
            absolute_path = os.path.join(workspace_path, workspace_relative)
            # Resolve to handle any .. or . in the path
            resolved_path = os.path.abspath(absolute_path)
            logger.info(f"{self.name}: Resolved localhost URL to: {resolved_path}")
            return resolved_path

        return file_path

    def _get_file_data(self, file_path: str) -> tuple[bytes, str, str]:
        """Get file data, filename, and content type from file path or URL."""
        try:
            # First, try to resolve localhost URLs to filesystem paths
            file_path = self._resolve_localhost_url(file_path)

            # Check if it's a URL (non-localhost)
            if file_path.startswith(("http://", "https://")):
                with httpx.Client() as client:
                    response = client.get(file_path)
                    response.raise_for_status()
                    file_data = response.content

                    # Strip query parameters from URL for filename extraction
                    clean_path = file_path.split("?")[0]
                    filename = os.path.basename(clean_path)
                    content_type = response.headers.get("content-type", "application/octet-stream")
            else:
                # Local file
                with open(file_path, "rb") as f:
                    file_data = f.read()
                filename = os.path.basename(file_path)

                # Try to determine content type from file extension
                import mimetypes

                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"

            return file_data, filename, content_type

        except Exception as e:
            logger.error(f"{self.name}: Error reading file {file_path}: {e}")
            raise

    def _get_upload_field(self, content_type: str, filename: str, entity_type: str) -> str:
        """Determine the appropriate upload field based on file type and entity type."""
        # Check file extension first
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        # Only projects with images use field-specific upload
        if entity_type.lower() == "project" and (
            ext in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"] or content_type.startswith("image/")
        ):
            return "image"

        # Everything else uses generic upload (no field name)
        return ""

    def _upload_file_to_entity(
        self,
        entity_type: str,
        entity_id: str,
        file_data: bytes,
        filename: str,
        content_type: str,
        description: str | None = None,
    ) -> dict:
        """Upload file to a specific entity using the ShotGrid Version upload pattern."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                # Step 1: Create a Version entity for all entity types (including Tasks)
                project_id = self.get_parameter_value("project_id")
                if not project_id:
                    raise Exception("Project ID is required for version uploads.")

                # For tasks, fetch the task to get its parent entity
                parent_entity = None
                if entity_type.lower() == "task":
                    task_url = f"{base_url}api/v1/entity/tasks/{entity_id}"
                    task_response = client.get(task_url, headers=headers, params={"fields": "entity"})
                    if task_response.status_code == 200:
                        task_data = task_response.json().get("data", {})
                        relationships = task_data.get("relationships", {})
                        entity_rel = relationships.get("entity", {})
                        if entity_rel.get("data"):
                            parent_entity = entity_rel["data"]

                version_create_data = {
                    "code": filename,
                    "description": description or f"Uploaded: {filename}",
                    "project": {"type": "Project", "id": int(project_id)},
                }

                # Link version to entity: use parent entity if task, otherwise the entity itself
                if entity_type.lower() == "task" and parent_entity:
                    # For tasks, link to BOTH the parent entity AND the task itself
                    version_create_data["entity"] = {
                        "type": parent_entity.get("type", ""),
                        "id": parent_entity.get("id", 0),
                    }
                    # Also link the task directly - try different field names
                    version_create_data["sg_task"] = {"type": "Task", "id": int(entity_id)}
                    logger.info(
                        f"{self.name}: Task {entity_id} belongs to {parent_entity.get('type')} {parent_entity.get('id')}, linking both"
                    )
                else:
                    version_create_data["entity"] = {"type": entity_type, "id": int(entity_id)}

                logger.info(f"{self.name}: Creating version: {version_create_data}")
                version_response = client.post(
                    f"{base_url}api/v1/entity/versions",
                    headers={**headers, "Content-Type": "application/json"},
                    json=version_create_data,
                )
                version_response.raise_for_status()
                version_data = version_response.json()
                version_id = version_data["data"]["id"]

                logger.info(f"{self.name}: Created version {version_id}")

                # Step 2: Request upload URL for the version's sg_uploaded_movie field
                upload_url = (
                    f"{base_url}api/v1/entity/versions/{version_id}/sg_uploaded_movie/_upload?filename={filename}"
                )
                logger.info(f"{self.name}: Requesting upload URL: {upload_url}")

                upload_response = client.get(upload_url, headers=headers)
                upload_response.raise_for_status()
                upload_info = upload_response.json()

                logger.info(f"{self.name}: Got upload response: {upload_info}")

                # Step 3: Upload file to S3 (no extra headers - S3 signed URL only expects 'host')
                upload_link = upload_info["links"]["upload"]
                # S3 signed URLs reject extra headers - only 'host' is signed
                upload_headers = {}

                logger.info(f"{self.name}: Uploading file to S3: {upload_link}")
                logger.info(f"{self.name}: File size: {len(file_data)} bytes")

                upload_file_response = client.put(upload_link, headers=upload_headers, content=file_data)
                upload_file_response.raise_for_status()

                logger.info(f"{self.name}: File uploaded successfully to S3")

                # Step 4: Finalize the upload (following community example)
                complete_url = f"{base_url}{upload_info['links']['complete_upload']}"
                complete_data = {
                    "upload_info": {
                        "timestamp": upload_info["data"].get("timestamp", ""),
                        "upload_type": upload_info["data"].get("upload_type", ""),
                        "upload_id": upload_info["data"].get("upload_id"),
                        "storage_service": upload_info["data"].get("storage_service", "s3"),
                        "original_filename": upload_info["data"].get("original_filename", filename),
                        "multipart_upload": upload_info["data"].get("multipart_upload", False),
                    },
                    "links": {
                        "upload": upload_info["links"]["upload"],
                        "complete_upload": upload_info["links"]["complete_upload"],
                    },
                    "upload_data": {"display_name": filename},
                }

                logger.info(f"{self.name}: Finalizing upload: {complete_url}")
                logger.info(f"{self.name}: Finalize data: {complete_data}")

                finalize_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                finalize_response = client.post(complete_url, headers=finalize_headers, json=complete_data)
                finalize_response.raise_for_status()

                logger.info(f"{self.name}: Upload finalized successfully")

                # Return the version info
                return {
                    "version_id": version_id,
                    "version_data": version_data["data"],
                    "filename": filename,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "status": "uploaded",
                }

        except Exception as e:
            logger.error(f"{self.name}: Error uploading file: {e}")
            raise

    def _get_version_upload_field(self, content_type: str, filename: str) -> str:
        """Determine the appropriate upload field for version uploads."""
        # Check file extension first
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        # Video files
        if ext in ["mp4", "mov", "avi", "mkv", "wmv", "flv", "webm"] or content_type.startswith("video/"):
            return "sg_uploaded_movie"

        # Image files
        if ext in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"] or content_type.startswith("image/"):
            return "sg_uploaded_movie"  # Versions use sg_uploaded_movie for images too

        # Audio files
        if ext in ["mp3", "wav", "aac", "flac", "ogg", "m4a"] or content_type.startswith("audio/"):
            return "sg_uploaded_movie"

        # Default to sg_uploaded_movie for everything else
        return "sg_uploaded_movie"

    def process(self) -> AsyncResult[None]:
        """Upload file to the specified entity with progress tracking."""
        try:
            # Get and validate input parameters
            entity_type = self.get_parameter_value("entity_type")
            entity_id = self.get_parameter_value("entity_id")
            file_path = self.get_parameter_value("file_path")
            file_name = self.get_parameter_value("file_name")
            description = self.get_parameter_value("description")

            if not entity_id:
                logger.error(f"{self.name}: Entity ID is required")
                return

            if not file_path:
                logger.error(f"{self.name}: File path is required")
                return

            # Initialize progress bar (5 steps: validate, detect, read, upload, complete)
            self.progress_bar_component.initialize(total_steps=5)

            # Step 1: Auto-detect entity type if "Unknown" is selected
            def _validate_and_detect() -> None:
                nonlocal entity_type
                self.progress_bar_component.increment()
                self.publish_update_to_parameter("upload_status", "Validating parameters...")

                if entity_type == "Unknown":
                    logger.info(f"{self.name}: Entity type is 'Unknown', attempting auto-detection...")
                    entity_type = self._detect_entity_type(entity_id)
                    if not entity_type:
                        raise Exception(f"Could not auto-detect entity type for ID {entity_id}")

                    # Update the entity_type parameter with the detected value
                    GriptapeNodes.handle_request(
                        SetParameterValueRequest(parameter_name="entity_type", value=entity_type, node_name=self.name)
                    )
                    self.parameter_output_values["entity_type"] = entity_type
                    self.publish_update_to_parameter("entity_type", entity_type)

                # Validate entity type
                if entity_type != "Unknown" and entity_type not in ENTITY_TYPES:
                    logger.warning(f"{self.name}: Unknown entity type '{entity_type}', proceeding anyway")

            yield _validate_and_detect

            # Step 2: Read file data
            def _read_file() -> None:
                self.progress_bar_component.increment()
                self.publish_update_to_parameter("upload_status", "Reading file...")

                logger.info(f"{self.name}: Reading file from {file_path}")
                file_data, original_filename, content_type = self._get_file_data(file_path)

                # Store in instance variables for next steps
                self._file_data = file_data
                self._original_filename = original_filename
                self._content_type = content_type

            yield _read_file

            # Step 3: Prepare upload
            def _prepare_upload() -> None:
                self.progress_bar_component.increment()
                self.publish_update_to_parameter("upload_status", "Preparing upload...")

                # Use custom filename if provided, otherwise use original
                self._final_filename = file_name or self._original_filename

                logger.info(
                    f"{self.name}: Uploading {self._final_filename} ({len(self._file_data)} bytes) to {entity_type} {entity_id}"
                )

            yield _prepare_upload

            # Step 4: Upload file
            def _upload_file() -> None:
                self.progress_bar_component.increment()
                self.publish_update_to_parameter("upload_status", "Uploading file...")

                # Upload file
                if entity_type is None:
                    raise Exception("Entity type is required for upload")
                self._version_data = self._upload_file_to_entity(
                    entity_type, entity_id, self._file_data, self._final_filename, self._content_type, description
                )

            yield _upload_file

            # Step 5: Complete and finalize
            def _finalize() -> None:
                self.progress_bar_component.increment()
                self.publish_update_to_parameter("upload_status", "Completing upload...")

                version_id = self._version_data.get("version_id", "")
                entity_type = self._version_data.get("entity_type", "")
                entity_id = self._version_data.get("entity_id", "")

                try:
                    base_url = self._get_shotgrid_config()["base_url"]
                    # Convert API URL to web UI URL
                    if base_url.endswith("/api/v1/"):
                        web_base = base_url.replace("/api/v1/", "").rstrip("/")
                    elif base_url.endswith("/api/v1"):
                        web_base = base_url.replace("/api/v1", "").rstrip("/")
                    else:
                        web_base = base_url.rstrip("/")

                    # Point to the version detail page (works for all entities including tasks)
                    upload_url = f"{web_base}/detail/Version/{version_id}"
                    entity_url = f"{web_base}/detail/{entity_type}/{entity_id}"
                except Exception:
                    upload_url = f"https://shotgrid.autodesk.com/detail/Version/{version_id}"
                    entity_url = f"https://shotgrid.autodesk.com/detail/{entity_type}/{entity_id}"

                # Update output parameters
                params = {
                    "upload_url": upload_url,
                    "entity_url": entity_url,
                    "version_id": str(version_id),
                    "file_name_output": self._final_filename,
                    "file_size": str(len(self._file_data)),
                    "upload_status": "Success",
                    "version_data": self._version_data.get("version_data", {}),
                }

                for param_name, value in params.items():
                    GriptapeNodes.handle_request(
                        SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
                    )
                    self.parameter_output_values[param_name] = value
                    self.publish_update_to_parameter(param_name, value)

                logger.info(f"{self.name}: Successfully uploaded {self._final_filename} to Version {version_id}")

            yield _finalize

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error uploading file: {e.response.status_code} - {e.response.text}"
            logger.error(f"{self.name}: {error_msg}")
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="upload_status", value=error_msg, node_name=self.name)
            )
            self.parameter_output_values["upload_status"] = error_msg
            self.publish_update_to_parameter("upload_status", error_msg)
        except Exception as e:
            error_msg = f"Error uploading file: {e}"
            logger.error(f"{self.name}: {error_msg}")
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="upload_status", value=error_msg, node_name=self.name)
            )
            self.parameter_output_values["upload_status"] = error_msg
            self.publish_update_to_parameter("upload_status", error_msg)
