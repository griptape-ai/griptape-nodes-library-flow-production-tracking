import base64
import io
from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from PIL import Image

from griptape_nodes.exe_types.core_types import (
    NodeMessageResult,
    Parameter,
    ParameterMode,
)
from griptape_nodes.exe_types.param_types.parameter_bool import ParameterBool
from griptape_nodes.exe_types.param_types.parameter_image import ParameterImage
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload
from griptape_nodes.traits.options import Options

# Default choices - will be populated dynamically
RELOAD_PROJECTS_CHOICE = "Reload to see projects"
PROJECT_CHOICES = [RELOAD_PROJECTS_CHOICE]


class FlowListProjects(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Get the user's ShotGrid URL for the link
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            # Remove trailing slash and add project list path
            projects_url = base_url.rstrip("/") + "/projects"
        except Exception:
            # Fallback to generic URL if config is not available
            projects_url = "https://shotgrid.autodesk.com/projects"

        self.add_parameter(
            ParameterString(
                name="projects_url",
                default_value=projects_url,
                allow_input=False,
                tooltip="Load all your Autodesk Flow projects",
                traits={
                    Button(
                        label="Reload Projects",
                        icon="list-restart",
                        size="icon",
                        variant="secondary",
                        full_width=True,
                        on_click=self._reload_projects,
                    ),
                },
            )
        )

        self.add_parameter(
            ParameterBool(
                name="show_templates",
                default_value=False,
                tooltip="Include project templates in the list.",
            )
        )
        self.add_parameter(
            ParameterBool(
                name="show_only_templates",
                default_value=False,
                tooltip="Show only project templates.",
            )
        )
        self.add_parameter(
            Parameter(
                name="all_projects",
                type="json",
                default_value=None,
                tooltip="All projects from ShotGrid.",
                allowed_modes={ParameterMode.PROPERTY, ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="project",
                type="string",
                default_value=RELOAD_PROJECTS_CHOICE,
                tooltip="Select a project from the list.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=PROJECT_CHOICES),
                    Button(
                        icon="list-restart",
                        size="icon",
                        variant="secondary",
                        on_click=self._reload_projects,
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterImage(
                name="project_image",
                default_value=None,
                tooltip="Image of the selected project",
                allow_input=False,
                allow_property=False,
            )
        )
        self.add_parameter(
            ParameterString(
                name="project_description",
                default_value=None,
                allow_input=False,
                allow_property=False,
                tooltip="Name of the selected project",
                placeholder_text="Description of the selected project",
                multiline=True,
            )
        )
        self.add_parameter(
            Parameter(
                name="project_url",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Direct URL to the selected project in ShotGrid",
            )
        )
        self.add_parameter(
            Parameter(
                name="project_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected project",
            )
        )
        self.add_parameter(
            Parameter(
                name="project_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected project",
                ui_options={"hide_property": True},
            )
        )

    def _is_template(self, project_data: dict) -> bool:
        """Determine if a project is a template based on various fields."""
        # Check various fields that might indicate template status
        if project_data.get("template") is True:
            return True
        if project_data.get("is_template") is True:
            return True
        if project_data.get("sg_type") == "Template":
            return True
        if project_data.get("sg_status") == "Template":
            return True

        # Check if name or code contains "template" (case insensitive)
        name = project_data.get("name") or ""
        code = project_data.get("code") or ""
        name_lower = name.lower()
        code_lower = code.lower()
        return "template" in name_lower or "template" in code_lower

    def _create_fallback_image(self, project_name: str) -> str:
        """Create a fallback image with project name when the project image is unavailable."""
        try:
            # Create a placeholder image
            img = Image.new("RGB", (200, 150), color="#2d3748")  # Dark gray background

            # Try to add text using PIL's default font
            try:
                from PIL import ImageDraw, ImageFont

                draw = ImageDraw.Draw(img)

                # Try to use a default font, fall back to basic if not available
                try:
                    # Try to use a system font
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
                except OSError:
                    try:
                        # Try alternative font path
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                    except OSError:
                        # Fall back to default font
                        font = ImageFont.load_default()

                # Truncate project name if too long
                display_name = project_name
                if len(project_name) > 20:
                    display_name = project_name[:17] + "..."

                # Get text size for centering
                bbox = draw.textbbox((0, 0), display_name, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Center the text
                x = (200 - text_width) // 2
                y = (150 - text_height) // 2

                # Draw the text in white
                draw.text((x, y), display_name, fill="white", font=font)

            except ImportError:
                # If ImageDraw is not available, just create a solid color image
                pass
            except Exception as e:
                logger.warning(f"Failed to add text to fallback image: {e}")

            # Convert to base64 data URL
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_data = img_buffer.getvalue()
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            logger.warning(f"Failed to create fallback image: {e}")
            # Return a simple data URL for a 1x1 transparent pixel as last resort
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def _validate_and_get_image(self, image_url: str, project_name: str) -> str:
        """Validate image URL and return a working image or fallback."""
        if not image_url:
            return self._create_fallback_image(project_name)

        try:
            # Try to fetch the image with a timeout
            with httpx.Client(timeout=5.0) as client:
                response = client.get(image_url)
                response.raise_for_status()

                # Check if it's actually an image by trying to open it with PIL
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img.verify()  # Verify it's a valid image

                # If we get here, the image is valid
                logger.info(f"Successfully validated image for project: {project_name}")
                return image_url

        except Exception as e:
            logger.warning(f"Image validation failed for project '{project_name}': {e}")
            return self._create_fallback_image(project_name)

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "project":
            self.publish_update_to_parameter("project", value)
            if value and value != RELOAD_PROJECTS_CHOICE:
                # Find the index of the selected project
                projects = self.get_parameter_value("all_projects") or []
                selected_index = next((i for i, project in enumerate(projects) if project["name"] == value), 0)
                self._update_project_data(selected_index)
        return super().after_value_set(parameter, value)

    def _update_project_data(self, selected_index: int) -> None:
        """Update project_id and project_data based on the selected project index."""
        projects = self.get_parameter_value("all_projects")
        if not projects or selected_index >= len(projects):
            return

        project = projects[selected_index]
        project_name = project.get("name", f"Project {project.get('id', 'Unknown')}")
        project_description = project.get("sg_description", "")
        project_url = project.get("url", "")

        # Validate and get a working image
        validated_image = self._validate_and_get_image(project.get("image"), project_name)

        self.parameter_output_values["project_id"] = project["id"]
        self.parameter_output_values["project_image"] = validated_image
        self.parameter_output_values["project_data"] = project
        self.parameter_output_values["project_description"] = project_description
        self.parameter_output_values["project_url"] = project_url

        self.publish_update_to_parameter("project_id", project["id"])
        self.publish_update_to_parameter("project_data", project)
        self.publish_update_to_parameter("project_image", validated_image)
        self.publish_update_to_parameter("project_description", project_description)
        self.publish_update_to_parameter("project_url", project_url)

    def _reload_projects(self, button: Button, button_details: ButtonDetailsMessagePayload) -> NodeMessageResult | None:  # noqa: ARG002
        """Reload projects when the reload button is clicked."""
        try:
            # Step 1: Get projects from API
            projects = self._fetch_projects_from_api()

            # Step 2: Process projects into choices
            project_list, choices_names = self._process_projects_to_choices(projects)

            # Step 3: Set the projects parameter with the processed data
            self.set_parameter_value("all_projects", project_list)
            self.parameter_output_values["all_projects"] = project_list

            # Step 4: Update parameter choices and preserve current selection
            current_selection = self.get_parameter_value("project")
            selected_id = 0  # Default to first project
            selected_value = choices_names[0] if choices_names else RELOAD_PROJECTS_CHOICE

            # Try to preserve the current selection by matching project names
            if current_selection and current_selection != RELOAD_PROJECTS_CHOICE:
                # Remove template indicators for comparison
                clean_current = current_selection.replace("📋 ", "").replace(" (Template)", "")

                for i, project in enumerate(project_list):
                    project_name = project.get("name", "")
                    if project_name == clean_current:
                        selected_id = i
                        selected_value = choices_names[i]
                        break

            self._update_option_choices("project", choices_names, selected_value)

            # Step 5: Update the Selected Project Data and ID for the selected
            self._update_project_data(selected_id)

        except Exception as e:
            logger.error(f"Failed to reload projects: {e}")
        return None

    def _fetch_projects_from_api(self) -> list[dict]:
        """Fetch projects from ShotGrid API."""
        # Get access token
        access_token = self._get_access_token()

        # Make request to get projects
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        # Get base URL
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/projects"

        # Add fields to get thumbnail URLs and template info
        params = {
            "fields": "id,name,code,description,sg_description,sg_status_list,image,sg_thumbnail,sg_type,sg_status,template,is_template"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("data", [])

    def _process_projects_to_choices(self, projects: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw projects data into choices format."""
        project_list = []
        choices_names = []

        # Get the base URL for constructing project URLs
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            # Remove trailing slash and add project path
            if not base_url.endswith("/"):
                base_url += "/"
        except Exception:
            base_url = "https://shotgrid.autodesk.com/"

        for project in projects:
            project_name = project.get("attributes", {}).get("name") or f"Project {project.get('id', 'Unknown')}"
            raw_image = project.get("attributes", {}).get("image")
            project_id = project.get("id")

            # Construct the project URL
            project_url = f"{base_url}projects/{project_id}" if project_id else None

            project_data = {
                "id": project_id,
                "name": project_name,
                "code": project.get("attributes", {}).get("code"),
                "description": project.get("attributes", {}).get("description"),
                "sg_description": project.get("attributes", {}).get("sg_description"),
                "sg_status_list": project.get("attributes", {}).get("sg_status_list"),
                "image": raw_image,  # Store raw image URL, validate only when selected
                "sg_thumbnail": project.get("attributes", {}).get("sg_thumbnail"),
                "sg_type": project.get("attributes", {}).get("sg_type"),
                "sg_status": project.get("attributes", {}).get("sg_status"),
                "template": project.get("attributes", {}).get("template"),
                "is_template": project.get("attributes", {}).get("is_template"),
                "url": project_url,  # Add the project URL
            }

            # Determine if this is a template
            is_template = self._is_template(project_data)
            project_data["is_template"] = is_template

            # Apply filtering based on parameters
            show_templates = self.get_parameter_value("show_templates")
            show_only_templates = self.get_parameter_value("show_only_templates")

            if show_only_templates and not is_template:
                continue  # Skip non-templates
            if not show_templates and not show_only_templates and is_template:
                continue  # Skip templates when not showing them

            project_list.append(project_data)

            # Create simple display name for dropdown
            project_id = project_data["id"]
            project_name = project_data["name"] or f"Project {project_id}"

            # Add template indicator to display name
            display_name = project_name
            if is_template:
                display_name = f"📋 {project_name} (Template)"

            choices_names.append(display_name)

        return project_list, choices_names

    def process(self) -> None:
        """Process the node - projects are only loaded when user clicks the reload button."""
        project = self.get_parameter_value("project")
        if project and project != RELOAD_PROJECTS_CHOICE:
            # Find the index of the selected project
            projects = self.get_parameter_value("all_projects") or []

            # Clean the current selection to match against project names
            clean_selection = project.replace("📋 ", "").replace(" (Template)", "")

            selected_index = next((i for i, proj in enumerate(projects) if proj["name"] == clean_selection), 0)
            self._update_project_data(selected_index)
        # Do nothing - projects are only loaded when user clicks the reload button
