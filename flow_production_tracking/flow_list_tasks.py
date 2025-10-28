from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import (
    Parameter,
    ParameterGroup,
    ParameterMessage,
    ParameterMode,
)
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload
from griptape_nodes.traits.options import Options

# Default choices - will be populated dynamically
TASK_CHOICES = ["No tasks available"]
TASK_CHOICES_ARGS = []


class FlowListTasks(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Get the user's ShotGrid URL for the link
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            # Remove trailing slash and add tasks path
            tasks_url = base_url.rstrip("/") + "/tasks"
        except Exception:
            # Fallback to generic URL if config is not available
            tasks_url = "https://shotgrid.autodesk.com/tasks"

        self.add_node_element(
            ParameterMessage(
                name="message",
                variant="none",
                value="Go to your ShotGrid tasks",
                button_link=tasks_url,
                button_text="Go to ShotGrid Tasks",
            )
        )

        with ParameterGroup(name="task_input"):
            self.add_parameter(
                Parameter(
                    name="entity_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the entity to list tasks for (Asset, Shot, etc.). The entity type and project will be determined automatically.",
                )
            )

        # Task selection parameter with Options and Button traits
        self.add_parameter(
            Parameter(
                name="selected_task_id",
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
                        icon="list-restart",
                        size="icon",
                        variant="secondary",
                        on_click=self._reload_tasks,
                    ),
                },
            )
        )

        with ParameterGroup(name="Selected Task") as selected_task_group:
            Parameter(
                name="selected_task_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected task",
                ui_options={"hide_property": True},
            )
            Parameter(
                name="tasks",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of tasks",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )

        self.add_node_element(selected_task_group)

        # Set initial values
        self.parameter_values["selected_task_id"] = ""
        self.parameter_values["selected_task_data"] = {}
        self.parameter_values["tasks"] = []

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_task_id" and value and value != "No tasks available":
            # Update selected task data when a task is selected
            self._update_selected_task_data(value)

    def _reload_tasks(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:  # noqa: ARG002
        """Reload tasks when button is clicked."""
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks based on current parameters."""
        try:
            entity_id = self.get_parameter_value("entity_id")

            if not entity_id:
                logger.warning(f"{self.name}: No entity ID provided")
                self._update_option_choices("selected_task_id", ["No tasks available"], "No tasks available")
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

            # First, get the entity details to determine type and project
            entity_info = self._get_entity_info(entity_id, access_token, base_url)
            if not entity_info:
                logger.error(f"{self.name}: Could not find entity with ID {entity_id}")
                self._update_option_choices("selected_task_id", ["No tasks available"], "No tasks available")
                return

            entity_type = entity_info["type"]
            project_id = entity_info["project_id"]

            # Get tasks for the entity
            tasks = self._get_tasks_for_entity(entity_type, entity_id, access_token, base_url)

            if tasks:
                self._populate_task_choices(tasks)
            else:
                self._update_option_choices("selected_task_id", ["No tasks available"], "No tasks available")
                self.parameter_values["tasks"] = []
                self.parameter_values["selected_task_id"] = "No tasks available"
                self.parameter_values["selected_task_data"] = {}

        except Exception as e:
            logger.error(f"{self.name}: Failed to load tasks: {e}")
            self._update_option_choices("selected_task_id", ["No tasks available"], "No tasks available")

    def _populate_task_choices(self, tasks: list[dict]) -> None:
        """Populate the task choices based on the loaded tasks."""
        global TASK_CHOICES, TASK_CHOICES_ARGS

        choices_args = []
        choices_names = []

        for task in tasks:
            task_id = task.get("id")
            attrs = task.get("attributes", {})
            content = attrs.get("content", f"Task {task_id}")
            status = attrs.get("sg_status_list", "Unknown")

            # Get step information
            step_data = task.get("relationships", {}).get("step", {}).get("data", {})
            step_name = step_data.get("name", "Unknown Step") if step_data else "Unknown Step"

            # Get assignee information
            assignees_data = task.get("relationships", {}).get("task_assignees", {}).get("data", [])
            assignee_names = []
            if assignees_data:
                for assignee in assignees_data:
                    assignee_name = assignee.get("name", "Unknown")
                    assignee_names.append(assignee_name)

            assignee_text = ", ".join(assignee_names) if assignee_names else "Unassigned"

            # Create display name
            display_name = f"{content} ({step_name}) - {status} - {assignee_text}"

            # Create choice data
            choice = {
                "task_id": task_id,
                "content": content,
                "status": status,
                "step_name": step_name,
                "assignees": assignee_names,
                "full_task_data": task,
            }

            choices_args.append(choice)
            choices_names.append(display_name)

        # Update global choices
        TASK_CHOICES = choices_names
        TASK_CHOICES_ARGS = choices_args

        # Update the parameter choices
        self._update_option_choices(
            "selected_task_id", choices_names, choices_names[0] if choices_names else "No tasks available"
        )

        # Output the tasks
        self.parameter_output_values["tasks"] = tasks

        # If we have tasks, automatically select the first one and set its data
        if choices_args:
            first_task_id = str(choices_args[0]["task_id"])
            self.parameter_values["selected_task_id"] = first_task_id
            self.parameter_output_values["selected_task_data"] = choices_args[0]["full_task_data"]
            logger.info(f"{self.name}: Auto-selected first task {first_task_id}")

        logger.info(f"{self.name}: Retrieved {len(tasks)} tasks")

        # Return None since this is a void method

    def _update_global_choices(self, choices_args: list[dict], choices_names: list[str]) -> None:
        """Update global choice variables."""
        global TASK_CHOICES, TASK_CHOICES_ARGS
        TASK_CHOICES = choices_names
        TASK_CHOICES_ARGS = choices_args

    def _update_selected_task_data(self, selected_task_id: str) -> None:
        """Update the selected task data when a task is selected."""
        try:
            # Find the task data for the selected task
            task_data = {}
            for choice in TASK_CHOICES_ARGS:
                if str(choice["task_id"]) == selected_task_id:
                    task_data = choice["full_task_data"]
                    break

            if task_data:
                # Set both parameter_values and parameter_output_values
                self.parameter_values["selected_task_data"] = task_data
                self.parameter_output_values["selected_task_data"] = task_data
                logger.info(f"{self.name}: Updated selected task data for task {selected_task_id}")
            else:
                logger.warning(f"{self.name}: Could not find task data for selected task {selected_task_id}")
                # Clear the output if no task data found
                self.parameter_output_values["selected_task_data"] = {}

        except Exception as e:
            logger.error(f"{self.name}: Failed to update selected task data: {e}")
            # Clear the output on error
            self.parameter_output_values["selected_task_data"] = {}

    def _get_entity_info(self, entity_id: int, access_token: str, base_url: str) -> dict | None:
        """Get entity information by querying entity endpoints directly."""
        try:
            # Try the most common entity types first
            entity_types = ["Asset", "Shot", "Sequence", "Episode", "Project"]
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            for entity_type in entity_types:
                url = f"{base_url}api/v1/entity/{entity_type.lower()}s"
                params = {"fields": "id,project", "filter[id]": str(entity_id)}

                with httpx.Client() as client:
                    response = client.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        entities = data.get("data", [])
                        if entities:
                            entity = entities[0]
                            # Project info is in relationships, not attributes
                            project_data = entity.get("relationships", {}).get("project", {}).get("data")
                            if project_data:
                                project_id = project_data.get("id")
                                if project_id:
                                    return {"type": entity_type, "project_id": project_id}

            return None

        except Exception as e:
            logger.error(f"Failed to get entity info for ID {entity_id}: {e}")
            return None

    def _get_tasks_for_entity(self, entity_type: str, entity_id: int, access_token: str, base_url: str) -> list[dict]:
        """Get all tasks for a specific entity (Asset, Shot, etc.)."""
        try:
            url = f"{base_url}api/v1/entity/tasks"
            params = {
                "fields": "id,content,entity,project,step,task_assignees,sg_status_list,created_at,updated_at",
                f"filter[entity.{entity_type}.id]": str(entity_id),
            }

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                tasks = data.get("data", [])

                logger.info(f"Found {len(tasks)} tasks for {entity_type} {entity_id}")
                return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks for {entity_type} {entity_id}: {e}")
            return []

    def process(self) -> None:
        """Process the node - tasks are only loaded when user clicks the reload button."""

        # Do nothing - tasks are only loaded when user clicks the reload button
