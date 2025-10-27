from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import (
    NodeMessageResult,
    Parameter,
    ParameterGroup,
    ParameterMessage,
    ParameterMode,
)
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

        self.add_node_element(
            ParameterMessage(
                name="message",
                variant="none",
                value="Go to your shotgrid projects",
                button_link=projects_url,
                button_text="Go to ShotGrid Projects",
            )
        )
        self.add_parameter(
            Parameter(
                name="selected_project",
                type="string",
                default_value=RELOAD_PROJECTS_CHOICE,
                tooltip="Select a project from the list.",
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={
                    "display_name": "Select Project",
                    "icon_size": "medium",
                },
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
        with ParameterGroup(name="Filter Options", ui_options={"collapsed": True}) as options_group:
            Parameter(
                name="show_templates",
                type="boolean",
                default_value=False,
                tooltip="Include project templates in the list.",
            )
            Parameter(
                name="show_only_templates",
                type="boolean",
                default_value=False,
                tooltip="Show only project templates.",
            )
        self.add_node_element(options_group)

        with ParameterGroup(name="Selected Project") as selected_project_group:
            Parameter(
                name="selected_project_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected project",
            )
            Parameter(
                name="selected_project_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected project",
                ui_options={"hide_property": True},
            )

            Parameter(
                name="projects",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The projects to list.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        self.add_node_element(selected_project_group)

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

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_project":
            self.publish_update_to_parameter("selected_project", value)
            if value and value != RELOAD_PROJECTS_CHOICE:
                # Find the index of the selected project
                projects = self.get_parameter_value("projects") or []
                selected_index = next((i for i, project in enumerate(projects) if project["name"] == value), 0)
                self._update_selected_project_data(selected_index)
        return super().after_value_set(parameter, value)

    def _update_selected_project_data(self, selected_index: int) -> None:
        """Update selected_project_id and selected_project_data based on the selected project index."""
        projects = self.get_parameter_value("projects")
        if not projects or selected_index >= len(projects):
            return

        selected_project = projects[selected_index]
        self.parameter_output_values["selected_project_id"] = selected_project["id"]
        self.parameter_output_values["selected_project_data"] = selected_project
        self.publish_update_to_parameter("selected_project_id", selected_project["id"])
        self.publish_update_to_parameter("selected_project_data", selected_project)

    def _reload_projects(self, button: Button, button_details: ButtonDetailsMessagePayload) -> NodeMessageResult | None:  # noqa: ARG002
        """Reload projects when the reload button is clicked."""
        try:
            # Step 1: Get projects from API
            projects = self._fetch_projects_from_api()

            # Step 2: Process projects into choices
            project_list, choices_names = self._process_projects_to_choices(projects)

            # Step 3: Set the projects parameter with the processed data
            self.set_parameter_value("projects", project_list)
            self.parameter_output_values["projects"] = project_list

            # Step 4: Update parameter choices
            # if the currently selected project is in the choices_names, use it, otherwise use the first choice
            current_selection = self.get_parameter_value("selected_project")
            selected_id = choices_names.index(current_selection) if current_selection in choices_names else 0
            selected_value = choices_names[selected_id]
            self._update_option_choices("selected_project", choices_names, selected_value)

            # Step 5: Update the Selected Project Data and ID for the selected
            self._update_selected_project_data(selected_id)

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

        for project in projects:
            project_data = {
                "id": project.get("id"),
                "name": project.get("attributes", {}).get("name"),
                "code": project.get("attributes", {}).get("code"),
                "description": project.get("attributes", {}).get("description"),
                "sg_description": project.get("attributes", {}).get("sg_description"),
                "sg_status_list": project.get("attributes", {}).get("sg_status_list"),
                "image": project.get("attributes", {}).get("image"),
                "sg_thumbnail": project.get("attributes", {}).get("sg_thumbnail"),
                "sg_type": project.get("attributes", {}).get("sg_type"),
                "sg_status": project.get("attributes", {}).get("sg_status"),
                "template": project.get("attributes", {}).get("template"),
                "is_template": project.get("attributes", {}).get("is_template"),
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
        selected_project = self.get_parameter_value("selected_project")
        if selected_project and selected_project != RELOAD_PROJECTS_CHOICE:
            # Find the index of the selected project
            projects = self.get_parameter_value("projects") or []
            selected_index = next((i for i, project in enumerate(projects) if project["name"] == selected_project), 0)
            self._update_selected_project_data(selected_index)
        # Do nothing - projects are only loaded when user clicks the reload button
