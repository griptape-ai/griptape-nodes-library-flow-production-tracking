import os

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import ParameterMode
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
from griptape_nodes.traits.file_system_picker import FileSystemPicker


class FlowGetFilePath(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="file_input",
                default_value="",
                tooltip="File path or URL (localhost URLs will be resolved to filesystem paths, remote URLs will be downloaded)",
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

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="local_path",
                default_value="",
                tooltip="Absolute filesystem path to the file",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The absolute filesystem path to the file",
            )
        )
        self.add_parameter(
            ParameterString(
                name="filename",
                default_value="",
                tooltip="Name of the file",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The name of the file",
            )
        )
        self.add_parameter(
            ParameterString(
                name="file_size",
                default_value="",
                tooltip="Size of the file in bytes",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The size of the file in bytes",
            )
        )

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

    def _download_remote_file(self, url: str) -> str:
        """Download a remote file to workspace and return the local path."""
        # Strip query parameters for filename
        clean_url = url.split("?")[0]
        filename = os.path.basename(clean_url)

        # Create a temp directory in workspace
        workspace_path = GriptapeNodes.ConfigManager().workspace_path
        temp_dir = os.path.join(workspace_path, "temp_downloads")
        os.makedirs(temp_dir, exist_ok=True)

        # Download file
        local_path = os.path.join(temp_dir, filename)
        logger.info(f"{self.name}: Downloading {url} to {local_path}")

        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

        logger.info(f"{self.name}: Downloaded {len(response.content)} bytes")
        return local_path

    def process(self) -> None:
        """Resolve file path from URL or local path."""
        file_input = self.get_parameter_value("file_input")

        if not file_input:
            logger.warning(f"{self.name}: No file input provided")
            return

        try:
            # First, try to resolve localhost URLs to filesystem paths
            local_path = self._resolve_localhost_url(file_input)

            # Check if it's still a URL (remote, non-localhost)
            if local_path.startswith(("http://", "https://")):
                local_path = self._download_remote_file(local_path)

            # Validate the file exists
            if not os.path.exists(local_path):
                logger.error(f"{self.name}: File not found: {local_path}")
                return

            # Get file info
            filename = os.path.basename(local_path)
            file_size = os.path.getsize(local_path)

            # Update output parameters
            self.parameter_output_values["local_path"] = local_path
            self.parameter_output_values["filename"] = filename
            self.parameter_output_values["file_size"] = str(file_size)

            self.publish_update_to_parameter("local_path", local_path)
            self.publish_update_to_parameter("filename", filename)
            self.publish_update_to_parameter("file_size", str(file_size))

            logger.info(f"{self.name}: Resolved to {local_path} ({file_size} bytes)")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(f"{self.name}: {error_msg}")
        except Exception as e:
            error_msg = f"Error resolving file path: {e}"
            logger.error(f"{self.name}: {error_msg}")
