from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import (
    Parameter,
    ParameterMode,
)
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.events.parameter_events import SetParameterValueRequest
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload
from griptape_nodes.traits.options import Options

# Default choices - will be populated dynamically
TASK_CHOICES = ["No tasks available"]
TASK_CHOICES_ARGS = []

# Standard ShotGrid entity types that can have tasks
ENTITY_TYPES = [
    "Project",
    "Asset",
    "Shot",
    "Sequence",
    "Episode",
    "Level",
    "Scene",
    "Product",
    "Script",
]


class FlowListTasks(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Get the user's ShotGrid URL for the link
        self.base_url = self._get_shotgrid_config()["base_url"]

        self.add_parameter(
            ParameterString(
                name="entity_id",
                default_value=None,
                tooltip="The ID of the entity to list tasks for (Project, Asset, Shot, etc.). For projects, this will list all tasks in the project.",
                placeholder_text="The ID of the entity to list tasks for (Project, Asset, Shot, etc.). For projects, this will list all tasks in the project.",
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_type",
                default_value=ENTITY_TYPES[0],  # Default to Project
                tooltip="The type of the entity to list tasks for (Project, Asset, Shot, etc.). For projects, this will list all tasks in the project.",
                placeholder_text="The type of the entity to list tasks for (Project, Asset, Shot, etc.). For projects, this will list all tasks in the project.",
                traits={
                    Options(choices=ENTITY_TYPES),
                    Button(
                        icon="list-restart",
                        size="icon",
                        variant="secondary",
                        on_click=self._reload_tasks,
                        full_width=True,
                        label="Reload Tasks",
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="entity_url",
                default_value="",
                allow_input=False,
                tooltip="The URL to view the entity in ShotGrid.",
                placeholder_text="The URL to view the entity in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )

        self.add_parameter(
            Parameter(
                name="all_tasks",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of tasks",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        # Task selection parameter with Options and Button traits
        self.add_parameter(
            Parameter(
                name="selected_task",
                type="string",
                default_value="No tasks available",
                tooltip="Select a task from the list.",
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={
                    "display_name": "Select Task",
                    "icon_size": "medium",
                },
                traits={
                    Options(choices=TASK_CHOICES),
                    Button(
                        icon="refresh-cw",
                        size="icon",
                        variant="secondary",
                        on_click=self._refresh_selected_task,
                    ),
                },
            )
        )

        self.add_parameter(
            Parameter(
                name="selected_task_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected task",
                ui_options={"hide_property": True},
            )
        )

        # Detailed task information parameters
        self.add_parameter(
            ParameterString(
                name="task_url",
                default_value="",
                tooltip="URL to view the task in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_id",
                type="str",
                default_value="",
                tooltip="ID of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="task_name",
                default_value="",
                tooltip="Name/content of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="pipeline_step",
                default_value="",
                tooltip="Pipeline step for the selected task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="status",
                default_value="",
                tooltip="Status of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="assigned_to",
                default_value="",
                tooltip="Who the task is assigned to",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Who the task is assigned to",
            )
        )
        self.add_parameter(
            ParameterString(
                name="priority",
                default_value="",
                tooltip="Priority of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Priority of the selected task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="start_date",
                default_value="",
                tooltip="Start date of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Start date of the selected task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="due_date",
                default_value="",
                tooltip="Due date of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Due date of the selected task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="description",
                default_value="",
                tooltip="Description of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
                multiline=True,
                placeholder_text="Description of the selected task",
            )
        )

        # Set initial values
        self.parameter_values["selected_task"] = ""
        self.parameter_values["selected_task_data"] = {}
        self.parameter_values["all_tasks"] = []

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "entity_id" and value:
            # Update entity URL when entity_id changes
            try:
                entity_id = int(value)
                entity_type = self.get_parameter_value("entity_type")
                self._update_entity_url(entity_id, entity_type)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid entity_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update entity_url for entity {value}: {e}")
        elif parameter.name == "entity_type" and value:
            # Update entity URL when entity_type changes
            try:
                entity_id = self.get_parameter_value("entity_id")
                if entity_id:
                    entity_id = int(entity_id)
                    self._update_entity_url(entity_id, value)
            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid entity_id value: {e}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update entity_url for entity type {value}: {e}")
        elif parameter.name == "selected_task" and value and value != "No tasks available":
            # Update selected task data when a task is selected
            self._update_selected_task_data(value)

    def _reload_tasks(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:  # noqa: ARG002
        """Reload all tasks when button is clicked."""
        self._load_tasks()

    def _refresh_selected_task(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:  # noqa: ARG002
        """Refresh the currently selected task information."""
        self._load_selected_task()

    def _load_tasks(self) -> None:
        """Load tasks based on current parameters."""
        try:
            entity_id = self.get_parameter_value("entity_id")
            entity_type = self.get_parameter_value("entity_type")

            if not entity_id:
                logger.warning(f"{self.name}: No entity ID provided")
                self._update_option_choices("selected_task", ["No tasks available"], "No tasks available")
                return

            if not entity_type:
                logger.warning(f"{self.name}: No entity type selected")
                self._update_option_choices("selected_task", ["No tasks available"], "No tasks available")
                return

            # Convert entity_id to integer
            try:
                entity_id = int(entity_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: entity_id must be a valid integer")
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Verify the entity exists and get project info
            entity_info = self._get_entity_info(entity_id, access_token, base_url)
            if not entity_info:
                logger.error(f"{self.name}: Could not find entity with ID {entity_id}")
                self._update_option_choices("selected_task", ["No tasks available"], "No tasks available")
                return

            # Verify the entity type matches what was found
            discovered_type = entity_info["type"]
            if discovered_type != entity_type:
                logger.warning(
                    f"{self.name}: Entity type mismatch. Expected {entity_type}, but found {discovered_type}"
                )
                # Use the discovered type instead of the selected one
                entity_type = discovered_type

            project_id = entity_info["project_id"]

            # Update the entity URL
            self._update_entity_url(entity_id, entity_type)

            # Get tasks for the entity
            tasks = self._get_tasks_for_entity(entity_type, entity_id, access_token, base_url)

            if tasks:
                self._populate_task_choices(tasks)
            else:
                self._update_option_choices("selected_task", ["No tasks available"], "No tasks available")
                self.parameter_values["all_tasks"] = []
                self.parameter_values["selected_task"] = "No tasks available"
                self.parameter_values["selected_task_data"] = {}

        except Exception as e:
            logger.error(f"{self.name}: Failed to load tasks: {e}")
            self._update_option_choices("selected_task", ["No tasks available"], "No tasks available")

    def _load_selected_task(self) -> None:
        """Load/refresh the currently selected task information."""
        try:
            selected_task_name = self.get_parameter_value("selected_task")
            if not selected_task_name or selected_task_name == "No tasks available":
                logger.warning(f"{self.name}: No task selected to refresh")
                return

            entity_id = self.get_parameter_value("entity_id")
            entity_type = self.get_parameter_value("entity_type")

            if not entity_id or not entity_type:
                logger.warning(f"{self.name}: Missing entity_id or entity_type for task refresh")
                return

            # Convert entity_id to integer
            try:
                entity_id = int(entity_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: entity_id must be a valid integer")
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Find the task ID for the selected task display name
            # selected_task_name is in format "task_id: task_name"
            task_id = None
            for choice in TASK_CHOICES_ARGS:
                expected_display = f"{choice['task_id']}: {choice['content']}"
                if expected_display == selected_task_name:
                    task_id = choice["task_id"]
                    break

            if not task_id:
                logger.warning(f"{self.name}: Could not find task ID for selected task: {selected_task_name}")
                return

            # Fetch the updated task data
            updated_task_data = self._fetch_single_task(task_id, access_token, base_url)
            if not updated_task_data:
                logger.warning(f"{self.name}: Could not fetch updated data for task {task_id}")
                return

            # Update the task in all_tasks
            self._update_task_in_all_tasks(task_id, updated_task_data)

            # Update the selected task data and all parameters
            self.parameter_values["selected_task_data"] = updated_task_data
            self.parameter_output_values["selected_task_data"] = updated_task_data
            self._populate_task_details(updated_task_data)

            logger.info(f"{self.name}: Refreshed task {selected_task_name} (ID: {task_id})")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected task: {e}")

    def _fetch_single_task(self, task_id: int, access_token: str, base_url: str) -> dict | None:
        """Fetch a single task by ID."""
        try:
            url = f"{base_url}api/v1/entity/tasks/{task_id}"
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            params = {
                "fields": "id,content,entity,project,step,task_assignees,sg_status_list,created_at,updated_at,sg_start_date,sg_due_date,sg_priority,sg_description,start_date,due_date,priority,description"
            }

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data")

                logger.warning(f"{self.name}: Failed to fetch task {task_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"{self.name}: Error fetching task {task_id}: {e}")
            return None

    def _update_task_in_all_tasks(self, task_id: int, updated_task_data: dict) -> None:
        """Update a specific task in the all_tasks list and refresh dropdown choices."""
        try:
            all_tasks = self.get_parameter_value("all_tasks") or []
            for i, task in enumerate(all_tasks):
                if task.get("id") == task_id:
                    all_tasks[i] = updated_task_data
                    break

            # Update the parameter values
            self.parameter_values["all_tasks"] = all_tasks
            self.parameter_output_values["all_tasks"] = all_tasks

            # Update the global TASK_CHOICES_ARGS and TASK_CHOICES
            global TASK_CHOICES, TASK_CHOICES_ARGS
            for i, choice in enumerate(TASK_CHOICES_ARGS):
                if choice["task_id"] == task_id:
                    # Update the choice data
                    choice["full_task_data"] = updated_task_data
                    choice["content"] = updated_task_data.get("attributes", {}).get("content", choice["content"])

                    # Update the display name in TASK_CHOICES (task_id: task_name format)
                    if i < len(TASK_CHOICES):
                        TASK_CHOICES[i] = f"{choice['task_id']}: {choice['content']}"
                    break

            # Refresh the dropdown choices to reflect the updated data
            self._refresh_dropdown_choices()

            logger.info(f"{self.name}: Updated task {task_id} in all_tasks list and refreshed dropdown")

        except Exception as e:
            logger.error(f"{self.name}: Failed to update task in all_tasks: {e}")

    def _refresh_dropdown_choices(self) -> None:
        """Refresh the dropdown choices with current TASK_CHOICES data."""
        try:
            # Get the current selection to preserve it
            current_selection = self.get_parameter_value("selected_task")

            # Update the dropdown choices
            self._update_option_choices("selected_task", TASK_CHOICES, current_selection)

            # Update the UI options data
            task_param = self.get_parameter_by_name("selected_task")
            if task_param:
                task_ui_options = task_param.ui_options
                task_ui_options["data"] = TASK_CHOICES_ARGS
                task_param.ui_options = task_ui_options

            logger.info(f"{self.name}: Refreshed dropdown choices")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh dropdown choices: {e}")

    def _populate_task_choices(self, tasks: list[dict]) -> None:
        """Populate the task choices based on the loaded tasks."""
        global TASK_CHOICES, TASK_CHOICES_ARGS

        choices_args = []
        choices_names = []

        for task in tasks:
            task_id = task.get("id")
            attrs = task.get("attributes", {})
            content = attrs.get("content", f"Task {task_id}")

            # Create display name - task_id: task_name format
            display_name = f"{task_id}: {content}"

            # Create choice data
            choice = {
                "task_id": task_id,
                "content": content,
                "full_task_data": task,
            }

            choices_args.append(choice)
            choices_names.append(display_name)

        # Update global choices
        TASK_CHOICES = choices_names
        TASK_CHOICES_ARGS = choices_args

        # Update the parameter choices
        self._update_option_choices(
            "selected_task", choices_names, choices_names[0] if choices_names else "No tasks available"
        )

        # Output the tasks
        self.parameter_output_values["all_tasks"] = tasks

        # If we have tasks, automatically select the first one and set its data
        if choices_args:
            first_task_display = choices_args[0]["content"]  # This is just the task name
            first_task_id = choices_args[0]["task_id"]
            first_display_name = f"{first_task_id}: {first_task_display}"

            self.parameter_values["selected_task"] = first_display_name
            self.parameter_output_values["selected_task_data"] = choices_args[0]["full_task_data"]
            # Update all task detail parameters
            self._update_selected_task_data(first_display_name)
            logger.info(f"{self.name}: Auto-selected first task {first_display_name}")

        logger.info(f"{self.name}: Retrieved {len(tasks)} tasks")

        # Return None since this is a void method

    def _update_global_choices(self, choices_args: list[dict], choices_names: list[str]) -> None:
        """Update global choice variables."""
        global TASK_CHOICES, TASK_CHOICES_ARGS
        TASK_CHOICES = choices_names
        TASK_CHOICES_ARGS = choices_args

    def _update_selected_task_data(self, selected_task_display: str) -> None:
        """Update the selected task data when a task is selected."""
        try:
            # Find the task data for the selected task
            # selected_task_display is in format "task_id: task_name"
            task_data = {}
            for choice in TASK_CHOICES_ARGS:
                # Check if the display name matches (task_id: task_name format)
                expected_display = f"{choice['task_id']}: {choice['content']}"
                if expected_display == selected_task_display:
                    task_data = choice["full_task_data"]
                    break

            if task_data:
                # Set both parameter_values and parameter_output_values
                self.parameter_values["selected_task_data"] = task_data
                self.parameter_output_values["selected_task_data"] = task_data

                # Extract task details from the task data
                self._populate_task_details(task_data)

                logger.info(f"{self.name}: Updated selected task data for task {selected_task_display}")
            else:
                logger.warning(f"{self.name}: Could not find task data for selected task {selected_task_display}")
                # Clear the output if no task data found
                self.parameter_output_values["selected_task_data"] = {}
                self._clear_task_details()

        except Exception as e:
            logger.error(f"{self.name}: Failed to update selected task data: {e}")
            # Clear the output on error
            self.parameter_output_values["selected_task_data"] = {}
            self._clear_task_details()

    def _populate_task_details(self, task_data: dict) -> None:
        """Populate all task detail parameters from task data."""
        try:
            # Extract basic task info
            task_id = task_data.get("id", "")
            attributes = task_data.get("attributes", {})
            relationships = task_data.get("relationships", {})
            links = task_data.get("links", {})

            # Extract individual task details
            task_url = self._extract_task_url(links)
            task_name = attributes.get("content", "")
            pipeline_step = self._extract_pipeline_step(relationships)
            status = attributes.get("sg_status_list", "")
            assigned_to = self._extract_assigned_to(relationships)

            # Try different field names for priority, dates, and description
            priority = self._extract_field_value(attributes, ["sg_priority", "priority", "sg_priority_list"])
            start_date = self._extract_field_value(attributes, ["sg_start_date", "start_date", "sg_start"])
            due_date = self._extract_field_value(attributes, ["sg_due_date", "due_date", "sg_due"])
            description = self._extract_field_value(attributes, ["sg_description", "description", "sg_desc"])

            # Update all parameters
            self._update_task_parameters(
                task_url,
                str(task_id),
                task_name,
                pipeline_step,
                status,
                assigned_to,
                priority,
                start_date,
                due_date,
                description,
            )

        except Exception as e:
            logger.error(f"{self.name}: Failed to populate task details: {e}")

    def _extract_task_url(self, links: dict) -> str:
        """Extract task URL from links."""
        if "self" in links:
            api_url = links["self"]
            if "/api/v1/entity/tasks/" in api_url:
                task_id_from_url = api_url.split("/api/v1/entity/tasks/")[1].split("/")[0]
                base_url = self._get_shotgrid_config()["base_url"]
                return f"{base_url}detail/Task/{task_id_from_url}"
        return ""

    def _extract_pipeline_step(self, relationships: dict) -> str:
        """Extract pipeline step from relationships."""
        step_data = relationships.get("step", {}).get("data", {})
        return step_data.get("name", "") if step_data else ""

    def _extract_assigned_to(self, relationships: dict) -> str:
        """Extract assigned to from relationships."""
        assignees_data = relationships.get("task_assignees", {}).get("data", [])
        return ", ".join([assignee.get("name", "") for assignee in assignees_data if assignee.get("name")])

    def _extract_field_value(self, attributes: dict, field_names: list[str]) -> str:
        """Try to extract a field value using multiple possible field names."""
        for field_name in field_names:
            value = attributes.get(field_name)
            if value is not None and value != "":
                return str(value)
        return ""

    def _update_task_parameters(
        self,
        task_url: str,
        task_id: str,
        task_name: str,
        pipeline_step: str,
        status: str,
        assigned_to: str,
        priority: str,
        start_date: str,
        due_date: str,
        description: str,
    ) -> None:
        """Update all task parameters using SetParameterValueRequest for proper UI updates."""
        params = {
            "task_url": task_url,
            "task_id": task_id,
            "task_name": task_name,
            "pipeline_step": pipeline_step,
            "status": status,
            "assigned_to": assigned_to,
            "priority": priority,
            "start_date": start_date,
            "due_date": due_date,
            "description": description,
        }

        # Use SetParameterValueRequest for each parameter to ensure proper UI updates
        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            # Also update parameter_output_values for downstream nodes
            self.parameter_output_values[param_name] = value
            # Publish updates to trigger UI updates
            self.publish_update_to_parameter(param_name, value)

    def _clear_task_details(self) -> None:
        """Clear all task detail parameters using SetParameterValueRequest for proper UI updates."""
        empty_params = [
            "task_url",
            "task_id",
            "task_name",
            "pipeline_step",
            "status",
            "assigned_to",
            "priority",
            "start_date",
            "due_date",
            "description",
        ]

        for param_name in empty_params:
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value="", node_name=self.name)
            )
            self.parameter_output_values[param_name] = ""
            self.publish_update_to_parameter(param_name, "")

    def _get_entity_info(self, entity_id: int, access_token: str, base_url: str) -> dict | None:
        """Get entity information by querying entity endpoints directly."""
        try:
            # Use the standard entity types that can have tasks
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            # Try entity types in order of likelihood (most common first)
            prioritized_types = [
                "Asset",
                "Shot",
                "Project",
                "Sequence",
                "Episode",
                "Level",
                "Scene",
                "Product",
                "Script",
            ]

            for entity_type in prioritized_types:
                url = f"{base_url}api/v1/entity/{entity_type.lower()}s"
                params = {"fields": "id,project", "filter[id]": str(entity_id)}

                with httpx.Client() as client:
                    response = client.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        entities = data.get("data", [])
                        if entities:
                            entity = entities[0]

                            # For projects, the entity_id IS the project_id
                            if entity_type == "Project":
                                return {"type": entity_type, "project_id": entity_id}

                            # For other entities, get project info from relationships
                            project_data = entity.get("relationships", {}).get("project", {}).get("data")
                            if project_data:
                                project_id = project_data.get("id")
                                if project_id:
                                    return {"type": entity_type, "project_id": project_id}

            return None

        except Exception as e:
            logger.error(f"Failed to get entity info for ID {entity_id}: {e}")
            return None

    def _update_entity_url(self, entity_id: int, entity_type: str | None = None) -> None:
        """Update the entity_url output parameter with the ShotGrid URL."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            if entity_type:
                entity_url = f"{base_url}detail/{entity_type}/{entity_id}"
            else:
                # Fallback to generic entity URL if type is unknown
                entity_url = f"{base_url}detail/Entity/{entity_id}"

            self.set_parameter_value("entity_url", entity_url)
            self.parameter_output_values["entity_url"] = entity_url
            self.publish_update_to_parameter("entity_url", entity_url)
            logger.info(f"{self.name}: Updated entity_url to: {entity_url}")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update entity_url: {e}")

    def _update_entity_types(self) -> None:
        """Update entity types with standard ShotGrid entity types that can have tasks."""
        # This method is here for future use if we want to make entity types dynamic
        # For now, we use the static ENTITY_TYPES list
        # Future implementation could query ShotGrid for available entity types

    def _get_tasks_for_entity(self, entity_type: str, entity_id: int, access_token: str, base_url: str) -> list[dict]:
        """Get all tasks for a specific entity (Project, Asset, Shot, etc.)."""
        try:
            url = f"{base_url}api/v1/entity/tasks"

            # For projects, use project filter; for other entities, use entity filter
            if entity_type == "Project":
                params = {
                    "fields": "id,content,entity,project,step,task_assignees,sg_status_list,created_at,updated_at,sg_start_date,sg_due_date,sg_priority,sg_description,start_date,due_date,priority,description",
                    "filter[project.Project.id]": str(entity_id),
                }
            else:
                params = {
                    "fields": "id,content,entity,project,step,task_assignees,sg_status_list,created_at,updated_at,sg_start_date,sg_due_date,sg_priority,sg_description,start_date,due_date,priority,description",
                    f"filter[entity.{entity_type}.id]": str(entity_id),
                }

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                tasks = data.get("data", [])

                if entity_type == "Project":
                    logger.info(f"Found {len(tasks)} tasks for project {entity_id}")
                else:
                    logger.info(f"Found {len(tasks)} tasks for {entity_type} {entity_id}")
                return tasks

        except Exception as e:
            if entity_type == "Project":
                logger.error(f"Failed to get tasks for project {entity_id}: {e}")
            else:
                logger.error(f"Failed to get tasks for {entity_type} {entity_id}: {e}")
            return []

    def process(self) -> None:
        """Process the node - tasks are only loaded when user clicks the reload button."""

        # Do nothing - tasks are only loaded when user clicks the reload button
