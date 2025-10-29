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
                },
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
                default_value="Load tasks to see options",
                tooltip="Select a task from the list. Use refresh button to update selected task data.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=TASK_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_task,
                        label="Refresh Selected",
                        full_width=True,
                    ),
                },
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
                placeholder_text="Pipeline step for the selected task",
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
                name="task_id",
                type="str",
                default_value="",
                tooltip="ID of the selected task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected task",
                ui_options={"hide_property": True},
            )
        )

        # Set initial values
        self.parameter_values["selected_task"] = ""
        self.parameter_values["task_data"] = {}
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
        elif parameter.name == "selected_task" and value and value != "Load tasks to see options":
            # Update selected task data when a task is selected
            self.publish_update_to_parameter("selected_task", value)
            if value and value != "Load tasks to see options":
                # Find the index of the selected task by matching display names
                tasks = self.get_parameter_value("all_tasks") or []
                selected_index = 0

                # Clean the selection to match against task names
                clean_selection = value.replace("📋 ", "").replace(" (Template)", "")

                for i, task in enumerate(tasks):
                    task_name = task.get("content", "")
                    if task_name == clean_selection:
                        selected_index = i
                        break

                self._update_selected_task_data_from_processed(
                    tasks[selected_index] if selected_index < len(tasks) else {}
                )
        return super().after_value_set(parameter, value)

    def _reload_tasks(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:  # noqa: ARG002
        """Reload all tasks when button is clicked."""
        self._load_tasks()

    def _refresh_selected_task(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:  # noqa: ARG002
        """Refresh the currently selected task information."""
        try:
            current_selection = self.get_parameter_value("selected_task")
            if not current_selection or current_selection == "Load tasks to see options":
                logger.warning(f"{self.name}: No task selected to refresh")
                return

            # Clean the selection to get the actual task name
            clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")

            # Get the current task ID from all_tasks
            tasks = self.get_parameter_value("all_tasks") or []
            selected_task_id = None
            selected_index = 0

            for i, task in enumerate(tasks):
                task_name = task.get("content", "")
                if task_name == clean_selection:
                    selected_task_id = task.get("id")
                    selected_index = i
                    break

            if not selected_task_id:
                logger.warning(f"{self.name}: Could not find task ID for '{clean_selection}'")
                return

            # Fetch fresh data for this specific task
            logger.info(f"{self.name}: Refreshing task {selected_task_id} ({clean_selection})")
            fresh_task_data = self._fetch_single_task(
                selected_task_id, self._get_access_token(), self._get_shotgrid_config()["base_url"]
            )

            if not fresh_task_data:
                logger.warning(f"{self.name}: Failed to fetch fresh data for task {selected_task_id}")
                return

            # Update the task in all_tasks using SetParameterValueRequest
            tasks[selected_index] = fresh_task_data
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_tasks", value=tasks, node_name=self.name)
            )
            self.parameter_output_values["all_tasks"] = tasks
            self.publish_update_to_parameter("all_tasks", tasks)

            # Update the task data display
            self._update_selected_task_data_from_processed(fresh_task_data)

            logger.info(f"{self.name}: Successfully refreshed task {selected_task_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected task: {e}")
        return

    def _process_tasks_to_choices(self, tasks: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw tasks data into choices format."""
        task_list = []
        choices_names = []

        for task in tasks:
            # Safely extract attributes and relationships with null checks
            attributes = task.get("attributes") or {}
            relationships = task.get("relationships") or {}

            # Safely extract nested data
            step_data = relationships.get("step", {}) or {}
            step_name = step_data.get("data", {}) or {}

            task_assignees_data = relationships.get("task_assignees", {}) or {}

            entity_data = relationships.get("entity", {}) or {}
            project_data = relationships.get("project", {}) or {}

            task_data = {
                "id": task.get("id"),
                "content": attributes.get("content"),
                "sg_status_list": attributes.get("sg_status_list"),
                "step": step_name.get("name"),
                "task_assignees": task_assignees_data.get("data", []),
                "sg_priority": attributes.get("sg_priority"),
                "sg_start_date": attributes.get("sg_start_date"),
                "sg_due_date": attributes.get("sg_due_date"),
                "sg_description": attributes.get("sg_description"),
                "entity": entity_data.get("data", {}),
                "project": project_data.get("data", {}),
            }
            task_list.append(task_data)

            # Create choice for the dropdown - just use task content
            task_content = task_data["content"] or f"Task {task_data['id']}"
            choices_names.append(task_content)

        return task_list, choices_names

    def _update_selected_task_data_from_processed(self, task_data: dict) -> None:
        """Update task outputs based on selected task data (processed structure)."""
        if not task_data:
            return

        # Extract basic task info (from processed data structure)
        task_id = task_data.get("id", "")
        task_content = task_data.get("content", f"Task {task_id}")
        step_name = task_data.get("step", "")
        status = task_data.get("sg_status_list", "")
        assignees = task_data.get("task_assignees", [])
        assigned_to = ", ".join([assignee.get("name", "") for assignee in assignees if assignee.get("name")])
        priority = task_data.get("sg_priority", "")
        start_date = task_data.get("sg_start_date", "")
        due_date = task_data.get("sg_due_date", "")
        description = task_data.get("sg_description", "")

        # Generate web UI URL
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            task_url = f"{base_url.rstrip('/')}/detail/Task/{task_id}"
        except Exception:
            task_url = f"https://shotgrid.autodesk.com/detail/Task/{task_id}"

        # Update all task parameters using SetParameterValueRequest
        params = {
            "task_url": task_url,
            "task_id": str(task_id),
            "task_name": task_content,
            "pipeline_step": step_name,
            "status": status,
            "assigned_to": assigned_to,
            "priority": priority,
            "start_date": start_date,
            "due_date": due_date,
            "description": description,
            "task_data": task_data,
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

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
                    task_data = data.get("data")

                    if task_data:
                        # Safely extract attributes and relationships with null checks
                        attributes = task_data.get("attributes") or {}
                        relationships = task_data.get("relationships") or {}

                        # Safely extract nested data
                        step_data = relationships.get("step", {}) or {}
                        step_name = step_data.get("data", {}) or {}

                        task_assignees_data = relationships.get("task_assignees", {}) or {}

                        entity_data = relationships.get("entity", {}) or {}
                        project_data = relationships.get("project", {}) or {}

                        # Process the task data to match our processed structure
                        processed_task = {
                            "id": task_data.get("id"),
                            "content": attributes.get("content"),
                            "sg_status_list": attributes.get("sg_status_list"),
                            "step": step_name.get("name"),
                            "task_assignees": task_assignees_data.get("data", []),
                            "sg_priority": attributes.get("sg_priority"),
                            "sg_start_date": attributes.get("sg_start_date"),
                            "sg_due_date": attributes.get("sg_due_date"),
                            "sg_description": attributes.get("sg_description"),
                            "entity": entity_data.get("data", {}),
                            "project": project_data.get("data", {}),
                        }
                        return processed_task

                logger.warning(f"{self.name}: Failed to fetch task {task_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"{self.name}: Error fetching task {task_id}: {e}")
            return None

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
        """Process the node - automatically load tasks when run."""
        try:
            # Get current selection to preserve it
            current_selection = self.get_parameter_value("selected_task")

            # Get input parameters
            entity_id = self.get_parameter_value("entity_id")
            entity_type = self.get_parameter_value("entity_type")

            if not entity_id:
                logger.warning(f"{self.name}: entity_id is required")
                self._update_option_choices("selected_task", ["No entity selected"], "No entity selected")
                return

            if not entity_type:
                logger.warning(f"{self.name}: entity_type is required")
                self._update_option_choices("selected_task", ["No entity type selected"], "No entity type selected")
                return

            # Convert entity_id to integer
            try:
                entity_id = int(entity_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: entity_id must be a valid integer")
                self._update_option_choices("selected_task", ["Invalid entity ID"], "Invalid entity ID")
                return

            # Load tasks from ShotGrid
            logger.info(f"{self.name}: Loading tasks from ShotGrid for {entity_type} {entity_id}...")
            tasks = self._get_tasks_for_entity(
                entity_type, entity_id, self._get_access_token(), self._get_shotgrid_config()["base_url"]
            )

            if not tasks:
                logger.warning(f"{self.name}: No tasks found for {entity_type} {entity_id}")
                self._update_option_choices("selected_task", ["No tasks available"], "No tasks available")
                return

            # Process tasks to choices
            task_list, choices_names = self._process_tasks_to_choices(tasks)

            # Store all tasks data first using SetParameterValueRequest
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_tasks", value=task_list, node_name=self.name)
            )
            self.parameter_output_values["all_tasks"] = task_list
            self.publish_update_to_parameter("all_tasks", task_list)

            # Determine what to select
            selected_value = choices_names[0] if choices_names else "No tasks available"
            selected_index = 0

            # Try to preserve the current selection
            if (
                current_selection
                and current_selection != "Load tasks to see options"
                and current_selection in choices_names
            ):
                selected_index = choices_names.index(current_selection)
                selected_value = current_selection
                logger.info(f"{self.name}: Preserved selection: {current_selection}")
            else:
                selected_value = choices_names[0]
                selected_index = 0
                logger.info(f"{self.name}: Selected first task: {choices_names[0]}")

            # Update the dropdown choices
            logger.info(f"{self.name}: Updating dropdown with {len(choices_names)} choices: {choices_names[:3]}...")
            self._update_option_choices("selected_task", choices_names, selected_value)
            logger.info(f"{self.name}: Dropdown updated, selected_value: {selected_value}")

            # Update the selected task data
            self._update_selected_task_data_from_processed(
                task_list[selected_index] if selected_index < len(task_list) else {}
            )

            logger.info(f"{self.name}: Successfully loaded {len(task_list)} tasks")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load tasks: {e}")
            self._update_option_choices("selected_task", ["Error loading tasks"], "Error loading tasks")
