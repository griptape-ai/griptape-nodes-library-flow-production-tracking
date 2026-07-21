import httpx
from base_shotgrid_node import BaseShotGridNode
from flow_utils import create_shotgrid_api
from griptape_nodes.exe_types.core_types import Parameter, ParameterGroup, ParameterMessage, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.traits.options import Options


class FlowCreateProject(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Dynamic message that will be updated with the created project link - placed at top for prominence
        self.project_message = ParameterMessage(
            name="project_message",
            title="Project Management",
            value="Create a project to see the link to view it in ShotGrid. Click the button to view all projects.",
            button_link="",
            button_text="View All Projects",
            variant="info",
            full_width=True,
        )
        self.add_node_element(self.project_message)

        with ParameterGroup(name="project_input") as project_input:
            self.add_parameter(
                Parameter(
                    name="project_name",
                    type="string",
                    default_value=None,
                    tooltip="The name of the project to create.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="project_code",
                    type="string",
                    default_value=None,
                    tooltip="The code for the project to create. If not provided, will be auto-generated from the project name.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="project_description",
                    type="string",
                    default_value=None,
                    tooltip="The description for the project to create.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="use_template",
                    type="boolean",
                    default_value=True,
                    tooltip="Whether to use a template for project creation. Templates provide predefined structure and tasks.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="template_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the project template to use. If not specified, will use the default project template.",
                    traits={Options(choices=["No templates available"])},
                )
            )

            self.add_parameter(
                Parameter(
                    name="thumbnail_image",
                    type="ImageUrlArtifact",
                    default_value=None,
                    tooltip="The thumbnail image for the project (optional).",
                    ui_options={
                        "clickable_file_browser": True,
                        "expander": True,
                    },
                )
            )
            self.add_parameter(
                Parameter(
                    name="created_project",
                    output_type="json",
                    type="json",
                    default_value=None,
                    tooltip="The created project data.",
                    allowed_modes={ParameterMode.OUTPUT},
                    ui_options={"hide_property": True},
                )
            )
            self.add_parameter(
                Parameter(
                    name="project_id",
                    output_type="string",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the newly created project.",
                    allowed_modes={ParameterMode.OUTPUT},
                    ui_options={"hide_property": True},
                )
            )

        self.add_node_element(project_input)

        # Set the initial link to the main projects page
        self._update_project_message_initial()

        # Populate template choices after all parameters are added
        self._populate_template_choices()

        self._create_status_parameters()

    def _update_project_message(self, project_id: int, project_name: str) -> None:
        """Update the ParameterMessage with a link to the created project."""
        try:
            # Construct the full ShotGrid URL for the project using the correct format
            base_url = self._get_shotgrid_config()["base_url"]
            # Use the correct URL format: /page/project_default?entity_type=Project&project_id={id}
            project_url = f"{base_url}page/project_default?entity_type=Project&project_id={project_id}"

            # Update the button_link and value of the ParameterMessage
            self.project_message.button_link = project_url
            self.project_message.value = (
                f"Project '{project_name}' created successfully! Click the button to view it in ShotGrid."
            )
            logger.info(f"{self.name}: Updated project message with link to project {project_id}")
        except Exception as e:
            logger.error(f"{self.name}: Failed to update project message: {e}")

    def _update_project_message_initial(self) -> None:
        """Set the initial value of the ParameterMessage to the main ShotGrid instance."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            self.project_message.value = (
                "Create a project to see the link to view it in ShotGrid. Click the button to view all projects."
            )
            self.project_message.button_link = base_url
            logger.info(f"{self.name}: Set initial project message to main ShotGrid instance.")
        except Exception as e:
            logger.error(f"{self.name}: Failed to set initial project message: {e}")

    def _populate_template_choices(self) -> None:
        """Populate the template_id parameter with available project templates"""
        try:
            # Get access token and create API instance
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Get project templates using the utility (this already filters for templates only)
            templates = api.get_project_templates()

            if templates:
                # Create choices list with template names and IDs
                choices = []
                for template in templates:
                    template_id = template.get("id")
                    template_name = template.get("attributes", {}).get("name", f"Template {template_id}")
                    template_type = template.get("attributes", {}).get("sg_type", "")

                    # Create a descriptive choice
                    if template_type:
                        choice_text = f"{template_name} ({template_type})"
                    else:
                        choice_text = template_name

                    choices.append(choice_text)

                # Update the template_id parameter with the new choices
                self._update_option_choices("template_id", choices, choices[0] if choices else "No templates available")
                logger.info(f"{self.name}: Populated {len(choices)} template choices")
            else:
                self._update_option_choices("template_id", ["No templates available"], "No templates available")
                logger.info(f"{self.name}: No templates found")

        except Exception as e:
            logger.warning(f"{self.name}: Could not populate template choices: {e}")
            self._update_option_choices("template_id", ["No templates available"], "No templates available")

    def _get_default_project_template(self, access_token: str, base_url: str) -> dict:
        """Get the default project template"""
        try:
            api = create_shotgrid_api(access_token, base_url)
            templates = api.get_project_templates()

            if templates:
                # Return the first template found
                return templates[0]

            logger.info(f"{self.name}: No project templates found")
            return None

        except Exception as e:
            logger.warning(f"{self.name}: Could not get default project template: {e}")
            return None

    def _create_project_from_template(
        self,
        template_id: int,
        project_name: str,
        project_code: str,
        project_description: str,
        access_token: str,
        base_url: str,
    ) -> dict:
        """Create a project using a template"""
        try:
            # First, get the template data
            template_url = f"{base_url}api/v1/entity/projects/{template_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Getting template data for template {template_id}")

            with httpx.Client() as client:
                response = client.get(template_url, headers=headers)
                response.raise_for_status()

                template_data = response.json()
                template_attributes = template_data.get("data", {}).get("attributes", {})

                logger.info(f"{self.name}: Template attributes: {template_attributes}")

                # Create project data based on template
                project_data = {
                    "name": project_name,
                    "code": project_code,
                    "layout_project": {"type": "Project", "id": template_id},
                }

                # Copy only the description field from template (other fields might cause issues)
                if template_attributes.get("sg_description"):
                    project_data["sg_description"] = template_attributes.get("sg_description")

                # Override description if provided
                if project_description:
                    project_data["sg_description"] = project_description

                logger.info(f"{self.name}: Creating project from template with data: {project_data}")

                # Create the project
                create_url = f"{base_url}api/v1/entity/projects"
                create_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                create_response = client.post(create_url, headers=create_headers, json=project_data)

                # Log detailed error information if creation fails
                if create_response.status_code != 201:
                    logger.error(f"{self.name}: Project creation failed with status {create_response.status_code}")
                    try:
                        error_data = create_response.json()
                        logger.error(f"{self.name}: Error response: {error_data}")
                        # Log each error individually for better debugging
                        if "errors" in error_data:
                            for error in error_data["errors"]:
                                logger.error(
                                    f"{self.name}: Error - {error.get('title', 'Unknown error')}: {error.get('detail', 'No details')}"
                                )
                    except:
                        logger.error(f"{self.name}: Error response text: {create_response.text}")
                    create_response.raise_for_status()

                created_data = create_response.json()
                logger.info(f"{self.name}: Project created from template successfully")
                return created_data

        except Exception as e:
            logger.error(f"{self.name}: Failed to create project from template: {e}")
            raise

    def process(self) -> None:
        self._clear_execution_status()
        try:
            # Get input parameters
            project_name = self.get_parameter_value("project_name")
            project_code = self.get_parameter_value("project_code")
            project_description = self.get_parameter_value("project_description")
            thumbnail_image = self.get_parameter_value("thumbnail_image")
            use_template = self.get_parameter_value("use_template")
            template_id = self.get_parameter_value("template_id")

            if not project_name:
                logger.error(f"{self.name}: project_name is required")
                return

            # Auto-generate project code from name if not provided
            if not project_code:
                # Convert project name to a valid code format
                # Remove special characters, convert to lowercase, replace spaces with underscores
                import re

                project_code = re.sub(r"[^a-zA-Z0-9\s]", "", project_name)  # Remove special chars
                project_code = re.sub(r"\s+", "_", project_code)  # Replace spaces with underscores
                project_code = project_code.lower()  # Convert to lowercase
                project_code = project_code[:20]  # Limit length to 20 characters

                # Ensure it's not empty after processing
                if not project_code:
                    project_code = "project"

                logger.info(f"{self.name}: Auto-generated project code: {project_code}")
            else:
                logger.info(f"{self.name}: Using provided project code: {project_code}")

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Create the project (with or without template)
            if use_template:
                logger.info(f"{self.name}: Creating project using template")

                # Determine which template to use
                if template_id and template_id != "No templates available":
                    # Extract template ID from the selected choice
                    try:
                        # Get the templates to find the ID using the utility
                        api = create_shotgrid_api(access_token, base_url)
                        templates = api.get_project_templates()
                        template_to_use = None

                        for template in templates:
                            template_id_from_api = template.get("id")
                            template_name = template.get("attributes", {}).get(
                                "name", f"Template {template_id_from_api}"
                            )
                            template_type = template.get("attributes", {}).get("sg_type", "")

                            # Create the same choice text format as in _populate_template_choices
                            if template_type:
                                choice_text = f"{template_name} ({template_type})"
                            else:
                                choice_text = template_name

                            if choice_text == template_id:  # template_id parameter contains the choice text
                                template_to_use = template_id_from_api
                                break

                        if template_to_use:
                            logger.info(f"{self.name}: Using selected template ID: {template_to_use}")
                        else:
                            logger.warning(f"{self.name}: Could not find template ID for selection: {template_id}")
                            template_to_use = None

                    except Exception as e:
                        logger.warning(f"{self.name}: Error parsing template selection: {e}")
                        template_to_use = None
                else:
                    # Get the default template
                    default_template = self._get_default_project_template(access_token, base_url)
                    if default_template:
                        template_to_use = default_template.get("id")
                        logger.info(f"{self.name}: Using default template ID: {template_to_use}")
                    else:
                        logger.warning(f"{self.name}: No template found, creating project without template")
                        template_to_use = None

                if template_to_use:
                    # Create project from template
                    try:
                        data = self._create_project_from_template(
                            template_to_use, project_name, project_code, project_description, access_token, base_url
                        )
                        created_project = data.get("data", {})
                        project_id = created_project.get("id")
                        logger.info(f"{self.name}: Project created from template successfully with ID: {project_id}")
                    except Exception as e:
                        logger.warning(f"{self.name}: Template creation failed, falling back to regular creation: {e}")
                        # Fallback to regular creation
                        project_data = {
                            "name": project_name,
                            "code": project_code,
                        }
                        if project_description:
                            project_data["sg_description"] = project_description

                        url = f"{base_url}api/v1/entity/projects"
                        headers = {
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        }

                        logger.info(f"{self.name}: Creating project without template with data: {project_data}")

                        with httpx.Client() as client:
                            response = client.post(url, headers=headers, json=project_data)

                            # Log detailed error information if creation fails
                            if response.status_code != 201:
                                logger.error(
                                    f"{self.name}: Fallback project creation failed with status {response.status_code}"
                                )
                                try:
                                    error_data = response.json()
                                    logger.error(f"{self.name}: Error response: {error_data}")
                                    if "errors" in error_data:
                                        for error in error_data["errors"]:
                                            logger.error(
                                                f"{self.name}: Error - {error.get('title', 'Unknown error')}: {error.get('detail', 'No details')}"
                                            )
                                except:
                                    logger.error(f"{self.name}: Error response text: {response.text}")
                                response.raise_for_status()

                            data = response.json()
                            created_project = data.get("data", {})
                            project_id = created_project.get("id")
                            logger.info(f"{self.name}: Project created successfully with ID: {project_id}")
                else:
                    # Fallback to regular creation
                    project_data = {
                        "name": project_name,
                        "code": project_code,
                    }
                    if project_description:
                        project_data["sg_description"] = project_description

                    url = f"{base_url}api/v1/entity/projects"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }

                    logger.info(f"{self.name}: Creating project without template with data: {project_data}")

                    with httpx.Client() as client:
                        response = client.post(url, headers=headers, json=project_data)

                        # Log detailed error information if creation fails
                        if response.status_code != 201:
                            logger.error(f"{self.name}: Project creation failed with status {response.status_code}")
                            try:
                                error_data = response.json()
                                logger.error(f"{self.name}: Error response: {error_data}")
                                if "errors" in error_data:
                                    for error in error_data["errors"]:
                                        logger.error(
                                            f"{self.name}: Error - {error.get('title', 'Unknown error')}: {error.get('detail', 'No details')}"
                                        )
                            except:
                                logger.error(f"{self.name}: Error response text: {response.text}")
                            response.raise_for_status()

                        data = response.json()
                        created_project = data.get("data", {})
                        project_id = created_project.get("id")
                        logger.info(f"{self.name}: Project created successfully with ID: {project_id}")
            else:
                # Create project without template
                project_data = {
                    "name": project_name,
                    "code": project_code,
                }
                if project_description:
                    project_data["sg_description"] = project_description

                url = f"{base_url}api/v1/entity/projects"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                logger.info(f"{self.name}: Creating project without template with data: {project_data}")

                with httpx.Client() as client:
                    response = client.post(url, headers=headers, json=project_data)

                    # Log detailed error information if creation fails
                    if response.status_code != 201:
                        logger.error(f"{self.name}: Project creation failed with status {response.status_code}")
                        try:
                            error_data = response.json()
                            logger.error(f"{self.name}: Error response: {error_data}")
                            if "errors" in error_data:
                                for error in error_data["errors"]:
                                    logger.error(
                                        f"{self.name}: Error - {error.get('title', 'Unknown error')}: {error.get('detail', 'No details')}"
                                    )
                        except:
                            logger.error(f"{self.name}: Error response text: {response.text}")
                        response.raise_for_status()

                    data = response.json()
                    created_project = data.get("data", {})
                    project_id = created_project.get("id")
                    logger.info(f"{self.name}: Project created successfully with ID: {project_id}")

            # Update the ParameterMessage with a link to the created project
            self._update_project_message(project_id, project_name)

            # Upload thumbnail if provided
            if thumbnail_image and project_id:
                logger.info(f"{self.name}: Uploading thumbnail for newly created project")
                try:
                    self._update_entity_thumbnail("projects", project_id, thumbnail_image, access_token, base_url)
                    logger.info(f"{self.name}: Thumbnail uploaded successfully")
                except Exception as e:
                    logger.error(f"{self.name}: Failed to upload thumbnail: {e}")
                    # Don't fail the entire operation if thumbnail upload fails
                    # The project was still created successfully

            # Get final project data
            try:
                project_url = f"{base_url}api/v1/entity/projects/{project_id}"
                with httpx.Client() as client:
                    resp = client.get(
                        project_url, headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
                    )
                    resp.raise_for_status()
                    final_project_data = resp.json().get("data", {})
                    logger.info(f"{self.name}: Retrieved final project data")
            except Exception as e:
                logger.warning(f"{self.name}: Could not get final project data: {e}")
                final_project_data = created_project

            # Output the results
            self.parameter_output_values["created_project"] = final_project_data
            self.parameter_output_values["project_id"] = project_id

            self._set_status_results(was_successful=True, result_details=f"Successfully created project {project_id}")

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)
