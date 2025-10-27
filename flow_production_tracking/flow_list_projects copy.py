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
PROJECT_CHOICES_ARGS = [
    {
        "name": "No projects available",
    },
]
PROJECT_CHOICES = [project["name"] for project in PROJECT_CHOICES_ARGS]


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
                default_value="No projects available",
                tooltip="Select a project from the list.",
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={
                    "display_name": "Select Project",
                    "data": [],
                    "icon_size": "medium",
                },
                traits={
                    Options(choices=PROJECT_CHOICES),
                    Button(
                        full_width=True,
                        label="Reload Projects",
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
            if value and value != "No projects available":
                # Find the selected choice and update outputs
                # Get the choices for the parameter
                options_trait = parameter.find_elements_by_type(Options)
                if options_trait:
                    data_list = parameter.ui_options.get("data", [])
                    for idx, choice in enumerate(options_trait[0].choices):
                        if choice == value:
                            # Check bounds to prevent index out of range error
                            if idx < len(data_list):
                                data_item = data_list[idx]
                                args = data_item.get("args", {})
                                if isinstance(args, dict):
                                    self.set_parameter_value("selected_project_id", args.get("project_id"))
                                    self.parameter_output_values["selected_project_id"] = args.get("project_id")
                                    self.parameter_output_values["selected_project_data"] = args.get("project_data")
                                    self.publish_update_to_parameter("selected_project_id", args.get("project_id"))
                                    self.publish_update_to_parameter("selected_project_data", args.get("project_data"))
                            break
        return super().after_value_set(parameter, value)

    def _reload_projects(self, button: Button, button_details: ButtonDetailsMessagePayload) -> NodeMessageResult | None:  # noqa: ARG002
        """Reload projects when the reload button is clicked."""
        try:
            # Step 1: Get projects from API
            projects = self._fetch_projects_from_api()

            # Step 2: Process projects into choices
            choices_args, choices_names = self._process_projects_to_choices(projects)

            # Step 3: Update global variables
            self._update_global_choices(choices_args, choices_names)

            # Step 4: Update parameter choices
            self._update_parameter_choices(choices_args, choices_names)

            # Step 5: Trigger UI refresh
            if choices_names and len(choices_names) > 0:
                current_selection = self.get_parameter_value("selected_project")
                if current_selection and current_selection in choices_names:
                    selected_value = current_selection
                else:
                    selected_value = choices_names[0]
                self.publish_update_to_parameter("selected_project", selected_value)
                self.set_parameter_value("selected_project", selected_value, emit_change=True)

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
        choices_args = []
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

            # Create choice for the dropdown
            project_id = project_data["id"]
            project_name = project_data["name"] or f"Project {project_id}"
            project_code = project_data["code"] or ""

            # Get thumbnail URL
            thumbnail_url = project_data.get("sg_thumbnail") or project_data.get("image") or ""

            # Add template indicator to display name
            display_name = project_name
            subtitle = (
                project_data.get("description") or project_data.get("sg_description") or project_code
            )  # Try description, sg_description, then code

            if is_template:
                display_name = f"📋 {project_name} (Template)"
                if not subtitle:
                    subtitle = "Template"
                else:
                    subtitle = f"{subtitle} (Template)"

            choice = {
                "name": display_name,
                "icon": thumbnail_url,
                "subtitle": subtitle,
                "args": {
                    "project_id": project_id,
                    "project_data": project_data,
                },
            }
            choices_args.append(choice)
            choices_names.append(display_name)

        return choices_args, choices_names

    def _update_global_choices(self, choices_args: list[dict], choices_names: list[str]) -> None:
        """Update global choice variables."""
        global PROJECT_CHOICES_ARGS, PROJECT_CHOICES
        PROJECT_CHOICES_ARGS = choices_args
        PROJECT_CHOICES = choices_names

    def _update_parameter_choices(self, choices_args: list[dict], choices_names: list[str]) -> None:
        """Update the parameter's choices without UI messaging."""
        if choices_names and len(choices_names) > 0:
            # Get the current selected value to preserve it
            current_selection = self.get_parameter_value("selected_project")

            # If current selection is still valid, keep it; otherwise use first choice
            if current_selection and current_selection in choices_names:
                selected_value = current_selection
            else:
                selected_value = choices_names[0]

            # Use the proper method to update choices (this should persist)
            try:
                # Update choices using the built-in method
                self._update_option_choices("selected_project", choices_names, selected_value)

                # Update UI options data
                project_param = self.get_parameter_by_name("selected_project")
                if project_param:
                    project_ui_options = project_param.ui_options
                    project_ui_options["data"] = choices_args
                    project_param.ui_options = project_ui_options

                # Set parameter value without emitting change events
                self.set_parameter_value("selected_project", selected_value, emit_change=True)
                self.publish_update_to_parameter("selected_project", selected_value)
            except Exception as e:
                logger.error(f"Failed to update parameter choices: {e}")
                # Fallback to direct assignment
                self.parameter_values["selected_project"] = selected_value
        else:
            # Handle no projects case
            try:
                project_param = self.get_parameter_by_name("selected_project")
                if project_param:
                    traits = project_param.find_elements_by_type(Options)
                    if traits:
                        traits[0].choices = ["No projects available"]
                    project_param.ui_options["data"] = []

                self.set_parameter_value("selected_project", "No projects available", emit_change=False)
            except Exception as e:
                logger.error(f"Failed to update parameter choices (no projects): {e}")
                self.parameter_values["selected_project"] = "No projects available"

    def _load_projects_data_only(self) -> None:
        """Load projects from ShotGrid API and update global choices without UI updates."""
        try:
            # Get access token
            access_token = self._get_access_token()

            # Make request to get projects
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Get base URL
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/projects"

            # Add fields to get thumbnail URLs and template info
            params = {
                "fields": "id,name,code,description,sg_status_list,image,sg_thumbnail,sg_type,sg_status,template,is_template"
            }

            logger.info(f"{self.name}: Getting projects via REST API")

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                projects = data.get("data", [])

                # Convert to list of dictionaries for output
                project_list = []
                choices_args = []
                choices_names = []

                for project in projects:
                    project_data = {
                        "id": project.get("id"),
                        "name": project.get("attributes", {}).get("name"),
                        "code": project.get("attributes", {}).get("code"),
                        "description": project.get("attributes", {}).get("description"),
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

                    # Add the computed is_template field to the project data
                    project_data["is_template"] = is_template

                    # Apply filtering based on parameters
                    show_templates = self.get_parameter_value("show_templates")
                    show_only_templates = self.get_parameter_value("show_only_templates")

                    if show_only_templates and not is_template:
                        continue  # Skip non-templates
                    if not show_templates and not show_only_templates and is_template:
                        continue  # Skip templates when not showing them

                    project_list.append(project_data)

                    # Create choice for the dropdown
                    project_id = project_data["id"]
                    project_name = project_data["name"] or f"Project {project_id}"
                    project_code = project_data["code"] or ""

                    # Get thumbnail URL
                    thumbnail_url = project_data.get("sg_thumbnail") or project_data.get("image") or ""

                    # Add template indicator to display name
                    display_name = project_name
                    subtitle = project_code

                    if is_template:
                        display_name = f"📋 {project_name} (Template)"
                        if not subtitle:
                            subtitle = "Template"
                        else:
                            subtitle = f"{subtitle} (Template)"

                    choice = {
                        "name": display_name,
                        "icon": thumbnail_url,
                        "subtitle": subtitle,
                        "args": {
                            "project_id": project_id,
                            "project_data": project_data,
                        },
                    }
                    choices_args.append(choice)
                    choices_names.append(display_name)

                # Update global choices
                global PROJECT_CHOICES_ARGS, PROJECT_CHOICES
                PROJECT_CHOICES_ARGS = choices_args
                PROJECT_CHOICES = choices_names

                # Update the dropdown parameter with new choices (same as process method)
                if PROJECT_CHOICES and len(PROJECT_CHOICES) > 0:
                    # Get the current selected value to preserve it
                    current_selection = self.get_parameter_value("selected_project")

                    # If current selection is still valid, keep it; otherwise use first choice
                    if current_selection and current_selection in PROJECT_CHOICES:
                        selected_value = current_selection
                    else:
                        selected_value = PROJECT_CHOICES[0]

                    # Update choices without emitting UI messages
                    self._update_option_choices("selected_project", PROJECT_CHOICES, selected_value)
                    project_param = self.get_parameter_by_name("selected_project")
                    if project_param:
                        project_ui_options = project_param.ui_options
                        project_ui_options["data"] = PROJECT_CHOICES_ARGS
                        project_param.ui_options = project_ui_options
                    # Set parameter value without emitting change events
                    self.set_parameter_value("selected_project", selected_value, emit_change=False)
                else:
                    self._update_option_choices("selected_project", ["No projects available"], "No projects available")
                    project_param = self.get_parameter_by_name("selected_project")
                    if project_param:
                        project_param.ui_options["data"] = []
                    self.set_parameter_value("selected_project", "No projects available", emit_change=False)

                # Output the projects
                self.parameter_output_values["projects"] = project_list
                logger.info(f"{self.name}: Retrieved {len(project_list)} projects via REST API")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")

    def _load_projects(self) -> None:
        """Load projects from ShotGrid API and update the dropdown choices."""
        try:
            # Get access token
            access_token = self._get_access_token()

            # Make request to get projects
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Get base URL
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/projects"

            # Add fields to get thumbnail URLs and template info
            params = {
                "fields": "id,name,code,description,sg_status_list,image,sg_thumbnail,sg_type,sg_status,template,is_template"
            }

            logger.info(f"{self.name}: Getting projects via REST API")

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                projects = data.get("data", [])

                # Convert to list of dictionaries for output
                project_list = []
                choices_args = []
                choices_names = []

                for project in projects:
                    project_data = {
                        "id": project.get("id"),
                        "name": project.get("attributes", {}).get("name"),
                        "code": project.get("attributes", {}).get("code"),
                        "description": project.get("attributes", {}).get("description"),
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

                    # Add the computed is_template field to the project data
                    project_data["is_template"] = is_template

                    # Apply filtering based on parameters
                    show_templates = self.get_parameter_value("show_templates")
                    show_only_templates = self.get_parameter_value("show_only_templates")

                    if show_only_templates and not is_template:
                        continue  # Skip non-templates
                    if not show_templates and not show_only_templates and is_template:
                        continue  # Skip templates when not showing them

                    project_list.append(project_data)

                    # Create choice for the dropdown
                    project_id = project_data["id"]
                    project_name = project_data["name"] or f"Project {project_id}"
                    project_code = project_data["code"] or ""

                    # Get thumbnail URL
                    thumbnail_url = project_data.get("sg_thumbnail") or project_data.get("image") or ""

                    # Add template indicator to display name
                    display_name = project_name
                    subtitle = project_code

                    if is_template:
                        display_name = f"📋 {project_name} (Template)"
                        if not subtitle:
                            subtitle = "Template"
                        else:
                            subtitle = f"{subtitle} (Template)"

                    choice = {
                        "name": display_name,
                        "icon": thumbnail_url,
                        "subtitle": subtitle,
                        "args": {
                            "project_id": project_id,
                            "project_data": project_data,
                        },
                    }
                    choices_args.append(choice)
                    choices_names.append(display_name)

                # Update global choices
                global PROJECT_CHOICES_ARGS, PROJECT_CHOICES
                PROJECT_CHOICES_ARGS = choices_args
                PROJECT_CHOICES = choices_names

                # Update the dropdown parameter with new choices
                if PROJECT_CHOICES and len(PROJECT_CHOICES) > 0:
                    # Get the current selected value to preserve it
                    current_selection = self.get_parameter_value("selected_project")

                    # If current selection is still valid, keep it; otherwise use first choice
                    if current_selection and current_selection in PROJECT_CHOICES:
                        selected_value = current_selection
                    else:
                        selected_value = PROJECT_CHOICES[0]

                    self._update_option_choices("selected_project", PROJECT_CHOICES, selected_value)
                    project_param = self.get_parameter_by_name("selected_project")
                    if project_param:
                        project_ui_options = project_param.ui_options
                        project_ui_options["data"] = PROJECT_CHOICES_ARGS
                        project_param.ui_options = project_ui_options
                    self.publish_update_to_parameter("selected_project", selected_value)
                else:
                    self._update_option_choices("selected_project", ["No projects available"], "No projects available")
                    project_param = self.get_parameter_by_name("selected_project")
                    if project_param:
                        project_param.ui_options["data"] = []

                # Output the projects
                self.parameter_output_values["projects"] = project_list
                logger.info(f"{self.name}: Retrieved {len(project_list)} projects via REST API")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")

    def process(self) -> None:
        """Process the node - projects are only loaded when user clicks the reload button."""

        # Do nothing - projects are only loaded when user clicks the reload button
