import time
from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from flow_utils import create_shotgrid_api
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.exe_types.node_types import AsyncResult
from griptape_nodes.traits.options import Options


class FlowCreateAsset(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to create the asset in.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_code",
                default_value=None,
                tooltip="The name for the asset to create.",
                placeholder_text="Enter the name for the asset to create.",
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_type",
                type="string",
                default_value="Character",
                tooltip="The type of asset to create (e.g., Character, Prop, Environment).",
                traits={
                    Options(
                        choices=[
                            "Character",
                            "Prop",
                            "Environment",
                            "Vehicle",
                            "FX",
                            "Camera",
                            "Light",
                            "Audio",
                            "Prompt",
                        ]
                    )
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_description",
                type="string",
                default_value=None,
                tooltip="The description for the asset to create.",
                multiline=True,
                placeholder_text="Enter the description for the asset to create.",
            )
        )
        self.add_parameter(
            Parameter(
                name="use_template",
                type="boolean",
                default_value=True,
                tooltip="Whether to use a template for asset creation. Templates provide predefined structure and tasks.",
            )
        )
        self.add_parameter(
            Parameter(
                name="task_template_id",
                type="string",
                default_value=None,
                tooltip="The task template to apply to the asset. This will create the appropriate workflow structure.",
                traits={Options(choices=["No task templates available"])},
            )
        )

        self.add_parameter(
            Parameter(
                name="thumbnail_image",
                type="ImageUrlArtifact",
                default_value=None,
                tooltip="The thumbnail image for the asset (optional).",
                ui_options={
                    "clickable_file_browser": True,
                    "expander": True,
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_id",
                default_value=None,
                tooltip="The ID of the newly created asset.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The ID of the newly created asset.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_url",
                default_value="",
                tooltip="The URL of the newly created asset.",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="The URL of the newly created asset.",
            )
        )
        self.add_parameter(
            Parameter(
                name="created_asset",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The created asset data.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

        # Populate task template choices after all parameters are added
        self._populate_task_template_choices()
        self._create_status_parameters()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "project_id" and value:
            # When project_id changes, fetch and update asset types
            try:
                # Get access token
                access_token = self._get_access_token()
                base_url = self._get_shotgrid_config()["base_url"]

                # Use utility function to get asset types for the project
                api = create_shotgrid_api(access_token, base_url)
                asset_types = api.get_asset_types_for_project(int(value))

                # Update the asset_type parameter with the new choices
                if asset_types:
                    # Always ensure "Prompt" is in the list, even if not configured in the project
                    if "Prompt" not in asset_types:
                        asset_types.append("Prompt")

                    # Preserve current selection if it's still valid, otherwise use first item
                    current_selection = self.get_parameter_value("asset_type")
                    if current_selection and current_selection in asset_types:
                        selected_value = current_selection
                    else:
                        selected_value = asset_types[0]

                    self._update_option_choices("asset_type", asset_types, selected_value)
                    logger.info(f"{self.name}: Updated asset_type choices: {asset_types}, selected: {selected_value}")
                else:
                    self._update_option_choices("asset_type", ["No asset types available"], "No asset types available")

            except Exception as e:
                logger.warning(f"{self.name}: Could not get asset types for project {value}: {e}")
                # Fallback to common asset types
                fallback_types = [
                    "Character",
                    "Prop",
                    "Environment",
                    "Vehicle",
                    "FX",
                    "Camera",
                    "Light",
                    "Audio",
                    "Prompt",
                ]

                # Preserve current selection if it's still valid, otherwise use first item
                current_selection = self.get_parameter_value("asset_type")
                if current_selection and current_selection in fallback_types:
                    selected_value = current_selection
                else:
                    selected_value = fallback_types[0]

                self._update_option_choices("asset_type", fallback_types, selected_value)

        elif parameter.name == "asset_type" and value:
            # When asset_type changes, update task template choices for that specific type
            logger.info(f"{self.name}: Asset type changed to: {value}")

            # Only repopulate if we don't have templates for this asset type yet
            current_asset_type = getattr(self, "current_asset_type", None)
            if current_asset_type != value:
                self.current_asset_type = value
                project_id = self.get_parameter_value("project_id")
                if project_id:
                    self._populate_task_template_choices_for_asset_type(project_id, value)
                else:
                    # If no project_id is set, populate with all task templates for Asset entity type
                    self._populate_task_template_choices()
            else:
                logger.info(f"{self.name}: Asset type {value} already has templates populated, skipping")

        return super().after_value_set(parameter, value)

    def _populate_task_template_choices(self) -> None:
        """Populate the task_template_id parameter with available task templates for Asset entity type"""
        logger.info(f"{self.name}: _populate_task_template_choices called")
        self.populating_templates = True
        try:
            # Get access token
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Use utility function to get task templates
            api = create_shotgrid_api(access_token, base_url)
            task_templates = api.get_task_templates(entity_type="Asset")

            if task_templates:
                # Create choices list with data for UI display
                choices = []
                choices_data = []

                for template in task_templates:
                    template_id = template.get("id")
                    template_name = template.get("attributes", {}).get("name", "")
                    template_code = template.get("attributes", {}).get("code", "")
                    template_description = template.get("attributes", {}).get("description", "")

                    # Use the template code for the choice (more descriptive than name)
                    # Fallback to name if code is empty, then to description, then to ID
                    if template_code:
                        choice_text = template_code
                    elif template_name:
                        choice_text = template_name
                    elif template_description:
                        choice_text = template_description
                    else:
                        choice_text = f"Task Template {template_id}"

                    choices.append(choice_text)

                    # Store the template data in the proper UI options format
                    choice_data = {
                        "name": choice_text,  # Main display text
                        "subtitle": template_description if template_description else template_name,  # Secondary text
                        "args": {
                            "template_id": template_id,
                            "template_name": template_name,
                            "template_code": template_code,
                            "template_description": template_description,
                        },
                    }
                    choices_data.append(choice_data)

                # Update the task_template_id parameter with the new choices
                logger.info(f"{self.name}: Updating task template choices: {choices}")
                self._update_option_choices(
                    "task_template_id", choices, choices[0] if choices else "No task templates available"
                )

                # Update the UI options with the data AFTER updating choices
                task_template_param = self.get_parameter_by_name("task_template_id")
                if task_template_param:
                    # Ensure ui_options exists and add our data
                    if not hasattr(task_template_param, "ui_options") or task_template_param.ui_options is None:
                        task_template_param.ui_options = {}
                    task_template_param.ui_options["data"] = choices_data
                else:
                    logger.warning(f"{self.name}: Could not find task_template_id parameter")
                logger.info(f"{self.name}: Populated {len(choices)} task template choices for Asset entity type")
            else:
                self._update_option_choices(
                    "task_template_id", ["No task templates available"], "No task templates available"
                )
                logger.info(f"{self.name}: No task templates found for Asset entity type")

        except Exception as e:
            logger.warning(f"{self.name}: Could not populate task template choices: {e}")
            self._update_option_choices(
                "task_template_id", ["No task templates available"], "No task templates available"
            )
        finally:
            self.populating_templates = False

    def _populate_task_template_choices_for_asset_type(self, project_id: int, asset_type: str) -> None:
        """Populate the task_template_id parameter with task templates for Asset entity type, filtered by asset type"""
        logger.info(
            f"{self.name}: _populate_task_template_choices_for_asset_type called for project {project_id}, asset_type {asset_type}"
        )
        self.populating_templates = True
        try:
            # Get access token
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Use utility function to get task templates filtered by asset type
            api = create_shotgrid_api(access_token, base_url)
            task_templates = api.get_task_templates(entity_type="Asset", asset_type=asset_type)

            if task_templates:
                # Create choices list with data for UI display
                choices = []
                choices_data = []

                for template in task_templates:
                    template_id = template.get("id")
                    template_name = template.get("attributes", {}).get("name", "")
                    template_code = template.get("attributes", {}).get("code", "")
                    template_description = template.get("attributes", {}).get("description", "")

                    # Use the template code for the choice (more descriptive than name)
                    # Fallback to name if code is empty, then to description, then to ID
                    if template_code:
                        choice_text = template_code
                    elif template_name:
                        choice_text = template_name
                    elif template_description:
                        choice_text = template_description
                    else:
                        choice_text = f"Task Template {template_id}"

                    choices.append(choice_text)

                    # Store the template data in the proper UI options format
                    choice_data = {
                        "name": choice_text,  # Main display text
                        "subtitle": template_description if template_description else template_name,  # Secondary text
                        "args": {
                            "template_id": template_id,
                            "template_name": template_name,
                            "template_code": template_code,
                            "template_description": template_description,
                        },
                    }
                    choices_data.append(choice_data)

                # Update the task_template_id parameter with the filtered choices
                self._update_option_choices(
                    "task_template_id", choices, choices[0] if choices else "No task templates available"
                )

                # Update the UI options with the data AFTER updating choices
                task_template_param = self.get_parameter_by_name("task_template_id")
                if task_template_param:
                    # Ensure ui_options exists and add our data
                    if not hasattr(task_template_param, "ui_options") or task_template_param.ui_options is None:
                        task_template_param.ui_options = {}
                    task_template_param.ui_options["data"] = choices_data

                else:
                    logger.warning(f"{self.name}: Could not find task_template_id parameter")
                logger.info(
                    f"{self.name}: Populated {len(choices)} task template choices for asset type '{asset_type}' in project {project_id}"
                )
            else:
                self._update_option_choices(
                    "task_template_id", ["No task templates available"], "No task templates available"
                )
                logger.info(f"{self.name}: No task templates found for Asset entity type")

        except Exception as e:
            logger.warning(f"{self.name}: Could not populate task template choices for asset type '{asset_type}': {e}")
            self._update_option_choices(
                "task_template_id", ["No task templates available"], "No task templates available"
            )
        finally:
            self.populating_templates = False

    def _create_asset_from_template(
        self,
        template_id: int,
        asset_code: str,
        project_id: int,
        asset_description: str,
        access_token: str,
        base_url: str,
    ) -> dict:
        """Create an asset using a template"""
        try:
            # First, get the template data
            template_url = f"{base_url}api/v1/entity/assets/{template_id}"
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

                # Create asset data based on template
                asset_data = {
                    "code": asset_code,
                    "project": {"type": "Project", "id": int(project_id)},
                    "sg_asset_type": template_attributes.get("sg_asset_type"),
                    "template": False,  # Ensure the new asset is not a template
                }

                # Copy relevant fields from template (only safe fields that we know work)
                safe_fields = ["description", "sg_asset_type"]

                for field in safe_fields:
                    if template_attributes.get(field) is not None:
                        asset_data[field] = template_attributes.get(field)

                # Override description if provided
                if asset_description:
                    asset_data["description"] = asset_description

                logger.info(f"{self.name}: Creating asset from template with data: {asset_data}")

                # Create the asset
                create_url = f"{base_url}api/v1/entity/assets"
                create_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                create_response = client.post(create_url, headers=create_headers, json=asset_data)

                # Log detailed error information if creation fails
                if create_response.status_code != 201:
                    logger.error(f"{self.name}: Asset creation failed with status {create_response.status_code}")
                    try:
                        error_data = create_response.json()
                        logger.error(f"{self.name}: Error response: {error_data}")
                    except:
                        logger.error(f"{self.name}: Error response text: {create_response.text}")
                    create_response.raise_for_status()

                created_data = create_response.json()
                logger.info(f"{self.name}: Asset created from template successfully")
                return created_data

        except Exception as e:
            logger.error(f"{self.name}: Failed to create asset from template: {e}")
            raise

    def process(self) -> AsyncResult[None]:
        yield lambda: self._do_process()

    def _do_process(self) -> None:
        self._clear_execution_status()
        try:
            # Get input parameters
            project_id = self.get_parameter_value("project_id")
            asset_code = self.get_parameter_value("asset_code")
            asset_type = self.get_parameter_value("asset_type")
            asset_description = self.get_parameter_value("asset_description")
            use_template = self.get_parameter_value("use_template")
            task_template_id = self.get_parameter_value("task_template_id")

            thumbnail_image = self.get_parameter_value("thumbnail_image")

            logger.info(f"{self.name}: Creating asset with type: '{asset_type}'")

            if not project_id:
                self._set_status_results(was_successful=False, result_details="project_id is required")
                logger.error(f"{self.name}: project_id is required")
                return

            if not asset_code:
                self._set_status_results(was_successful=False, result_details="asset_code is required")
                logger.error(f"{self.name}: asset_code is required")
                return

            if not asset_type:
                self._set_status_results(was_successful=False, result_details="asset_type is required")
                logger.error(f"{self.name}: asset_type is required")
                return

            # Get access token
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Try password authentication first for better permissions
            try:
                access_token = self._get_access_token_with_password()
                logger.info(f"{self.name}: Using password authentication")
            except Exception as e:
                logger.warning(f"{self.name}: Password authentication failed, falling back to client credentials: {e}")
                access_token = self._get_access_token()

            # Create the asset (with or without task template)
            if use_template:
                # Determine which task template to use
                if task_template_id and task_template_id != "No task templates available":
                    # Extract task template ID from the selected choice
                    try:
                        # Since ui_options["data"] is being overwritten, let's fetch the task templates again
                        # and find the one that matches the selected name

                        # Get access token and fetch task templates
                        access_token = self._get_access_token()
                        base_url = self._get_shotgrid_config()["base_url"]
                        api = create_shotgrid_api(access_token, base_url)
                        task_templates = api.get_task_templates(entity_type="Asset", asset_type=asset_type)

                        template_to_use = None
                        for template in task_templates:
                            template_id = template.get("id")
                            template_name = template.get("attributes", {}).get("name", "")
                            template_code = template.get("attributes", {}).get("code", "")

                            # Check if this template matches the selected one
                            if template_code == task_template_id or template_name == task_template_id:
                                template_to_use = template_id
                                break

                        if template_to_use is None:
                            logger.warning(
                                f"{self.name}: Could not find task template ID for selection: {task_template_id}"
                            )

                    except Exception as e:
                        logger.warning(f"{self.name}: Error parsing task template selection: {e}")
                        template_to_use = None
                else:
                    logger.warning(f"{self.name}: No task template selected, creating asset without task template")
                    template_to_use = None

                # Create the asset with task template attached (if selected)
                asset_data = {
                    "code": asset_code,
                    "sg_asset_type": asset_type,
                    "project": {"type": "Project", "id": int(project_id)},
                }

                logger.info(f"{self.name}: Creating asset with data: {asset_data}")
                if asset_description:
                    asset_data["description"] = asset_description

                # Attach task template if selected
                if template_to_use:
                    asset_data["task_template"] = {"type": "TaskTemplate", "id": template_to_use}

                url = f"{base_url}api/v1/entity/assets"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                with httpx.Client() as client:
                    response = client.post(url, headers=headers, json=asset_data)
                    response.raise_for_status()

                    data = response.json()
                    created_asset = data.get("data", {})
                    asset_id = created_asset.get("id")
                    logger.info(f"{self.name}: Asset created successfully with ID: {asset_id}")

            else:
                # Create asset without template
                asset_data = {
                    "code": asset_code,
                    "sg_asset_type": asset_type,
                    "project": {"type": "Project", "id": int(project_id)},
                }
                if asset_description:
                    asset_data["description"] = asset_description

                url = f"{base_url}api/v1/entity/assets"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                with httpx.Client() as client:
                    response = client.post(url, headers=headers, json=asset_data)
                    response.raise_for_status()

                    data = response.json()
                    created_asset = data.get("data", {})
                    asset_id = created_asset.get("id")
                    logger.info(f"{self.name}: Asset created successfully with ID: {asset_id}")

            # Upload thumbnail if provided
            if thumbnail_image and asset_id:
                logger.info(f"{self.name}: Uploading thumbnail for newly created asset {asset_id}")

                # Handle both ImageUrlArtifact and dictionary formats
                if hasattr(thumbnail_image, "value"):
                    # It's an ImageUrlArtifact
                    thumbnail_url = thumbnail_image.value
                    logger.info(f"{self.name}: Thumbnail image value: {thumbnail_url}")
                elif isinstance(thumbnail_image, dict) and "value" in thumbnail_image:
                    # It's a dictionary with a value field
                    thumbnail_url = thumbnail_image["value"]
                    logger.info(f"{self.name}: Thumbnail image value from dict: {thumbnail_url}")
                elif isinstance(thumbnail_image, str):
                    # It's a direct string URL
                    thumbnail_url = thumbnail_image
                    logger.info(f"{self.name}: Thumbnail image value from string: {thumbnail_url}")
                else:
                    logger.error(f"{self.name}: Invalid thumbnail_image format: {type(thumbnail_image)}")
                    thumbnail_url = None

                if thumbnail_url:
                    # Create a simple object to pass to _update_entity_thumbnail
                    class ThumbnailWrapper:
                        def __init__(self, url):
                            self.value = url

                    thumbnail_wrapper = ThumbnailWrapper(thumbnail_url)

                    # Add a longer delay to ensure asset is fully created
                    logger.info(f"{self.name}: Waiting 5 seconds for asset to be fully available...")
                    time.sleep(5)

                    # Try thumbnail upload with retries
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            logger.info(
                                f"{self.name}: Attempting thumbnail upload (attempt {attempt + 1}/{max_retries})"
                            )
                            upload_id = self._update_entity_thumbnail(
                                "assets", asset_id, thumbnail_wrapper, access_token, base_url
                            )
                            logger.info(f"{self.name}: Thumbnail uploaded successfully with upload_id: {upload_id}")
                            break  # Success, exit retry loop
                        except Exception as e:
                            logger.warning(f"{self.name}: Thumbnail upload attempt {attempt + 1} failed: {e}")
                            if attempt < max_retries - 1:
                                logger.info(f"{self.name}: Waiting 3 seconds before retry...")
                                time.sleep(3)
                            else:
                                logger.error(f"{self.name}: All thumbnail upload attempts failed")
                                logger.error(
                                    f"{self.name}: Thumbnail upload exception details: {type(e).__name__}: {e!s}"
                                )
                                # Don't fail the entire operation if thumbnail upload fails
                                # The asset was still created successfully
            elif thumbnail_image and not asset_id:
                logger.error(f"{self.name}: Cannot upload thumbnail - asset_id is None")
            elif not thumbnail_image:
                logger.info(f"{self.name}: No thumbnail provided, skipping thumbnail upload")

            # Get final asset data
            try:
                asset_url = f"{base_url}api/v1/entity/assets/{asset_id}"
                with httpx.Client() as client:
                    resp = client.get(
                        asset_url, headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
                    )
                    resp.raise_for_status()
                    final_asset_data = resp.json().get("data", {})
                    logger.info(f"{self.name}: Retrieved final asset data")
            except Exception as e:
                logger.warning(f"{self.name}: Could not get final asset data: {e}")
                final_asset_data = created_asset

            # Output the results
            self.parameter_output_values["created_asset"] = final_asset_data
            self.parameter_output_values["asset_id"] = asset_id

            # Publish updates to ensure UI refreshes
            self.publish_update_to_parameter("created_asset", final_asset_data)
            self.publish_update_to_parameter("asset_id", asset_id)

            # Update the asset_url output
            if asset_id:
                self._update_asset_url(asset_id)

            self._set_status_results(was_successful=True, result_details=f"Successfully created asset {asset_id}")

        except Exception as e:
            self._set_status_results(was_successful=False, result_details=str(e))
            self._handle_failure_exception(e)

    def _update_asset_url(self, asset_id: int) -> None:
        """Update the asset_url output parameter with the ShotGrid URL."""
        try:
            # Get the base URL from config
            base_url = self._get_shotgrid_config()["base_url"]

            # Create the ShotGrid URL for the asset
            asset_url = f"{base_url}detail/Asset/{asset_id}"

            # Set the output parameter
            self.set_parameter_value("asset_url", asset_url)
            self.parameter_output_values["asset_url"] = asset_url
            self.publish_update_to_parameter("asset_url", asset_url)

            logger.info(f"{self.name}: Updated asset_url to: {asset_url}")

        except Exception as e:
            logger.warning(f"{self.name}: Failed to update asset_url: {e}")

    def _create_tasks_from_template(
        self, asset_id: int, task_template_id: int, access_token: str, base_url: str
    ) -> None:
        """Create tasks for an asset based on a task template"""
        try:
            # First, get the task template data
            template_url = f"{base_url}api/v1/entity/task_templates/{task_template_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.info(f"{self.name}: Getting task template data for template {task_template_id}")

            with httpx.Client() as client:
                response = client.get(template_url, headers=headers)
                response.raise_for_status()

                template_data = response.json()
                template_attributes = template_data.get("data", {}).get("attributes", {})

                logger.info(f"{self.name}: Task template attributes: {template_attributes}")

                # Get the step information from the template
                step_data = template_attributes.get("step")

                # Create a task based on the template
                task_data = {
                    "content": template_attributes.get("name", "Task from Template"),
                    "project": {"type": "Project", "id": int(self.get_parameter_value("project_id"))},
                    "entity": {"type": "Asset", "id": asset_id},
                }

                # Add step data if available
                if step_data:
                    task_data["step"] = step_data
                    logger.info(f"{self.name}: Using step data from template: {step_data}")
                else:
                    logger.info(f"{self.name}: No step data in template, creating task without step")

                # Add description if available
                if template_attributes.get("description"):
                    task_data["description"] = template_attributes.get("description")

                logger.info(f"{self.name}: Creating task from template with data: {task_data}")

                # Create the task
                create_url = f"{base_url}api/v1/entity/tasks"
                create_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                create_response = client.post(create_url, headers=create_headers, json=task_data)

                if create_response.status_code == 201:
                    created_task = create_response.json()
                    task_id = created_task.get("data", {}).get("id")
                    logger.info(f"{self.name}: Successfully created task {task_id} from template")
                else:
                    logger.warning(f"{self.name}: Failed to create task from template: {create_response.status_code}")
                    try:
                        error_data = create_response.json()
                        logger.warning(f"{self.name}: Error response: {error_data}")
                    except:
                        logger.warning(f"{self.name}: Error response text: {create_response.text}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to create tasks from template: {e}")
            raise
