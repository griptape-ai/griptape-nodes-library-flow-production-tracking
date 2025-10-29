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

# Constants
HTTP_OK = 200


class FlowUpdateTask(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameters
        self.add_parameter(
            ParameterString(
                name="task_id",
                default_value=None,
                tooltip="The ID of the task to update.",
                placeholder_text="Enter task ID (e.g., 6817)",
            )
        )
        self.add_parameter(
            ParameterString(
                name="task_name",
                default_value=None,
                tooltip="The new name/content for the task (optional).",
                placeholder_text="Enter new task name/content",
            )
        )
        self.add_parameter(
            ParameterString(
                name="status",
                default_value=None,
                tooltip="The new status for the task (optional).",
                placeholder_text="Enter new status",
            )
        )
        self.add_parameter(
            ParameterString(
                name="assigned_to",
                default_value=None,
                tooltip="The new assignee for the task (optional). Use user ID or login name.",
                placeholder_text="Enter user ID or login name",
            )
        )
        self.add_parameter(
            ParameterString(
                name="priority",
                default_value=None,
                tooltip="The new priority for the task (optional).",
                placeholder_text="Enter new priority",
            )
        )
        self.add_parameter(
            ParameterString(
                name="start_date",
                default_value=None,
                tooltip="The new start date for the task (optional). Format: YYYY-MM-DD",
                placeholder_text="YYYY-MM-DD",
            )
        )
        self.add_parameter(
            ParameterString(
                name="due_date",
                default_value=None,
                tooltip="The new due date for the task (optional). Format: YYYY-MM-DD",
                placeholder_text="YYYY-MM-DD",
            )
        )
        self.add_parameter(
            ParameterString(
                name="description",
                default_value=None,
                tooltip="The new description for the task (optional).",
                placeholder_text="Enter new description",
            )
        )

        # Output parameters
        self.add_parameter(
            ParameterString(
                name="task_url",
                default_value="",
                tooltip="The URL to view the task in ShotGrid.",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="updated_task_id",
                type="str",
                default_value="",
                tooltip="ID of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_task_name",
                default_value="",
                tooltip="Name/content of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_status",
                default_value="",
                tooltip="Status of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_assigned_to",
                default_value="",
                tooltip="Who the updated task is assigned to",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_priority",
                default_value="",
                tooltip="Priority of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_start_date",
                default_value="",
                tooltip="Start date of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_due_date",
                default_value="",
                tooltip="Due date of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_description",
                default_value="",
                tooltip="Description of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the updated task",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "task_id" and value:
            # Update task URL when task_id changes
            self._update_task_url()
        return super().after_value_set(parameter, value)

    def _update_task_url(self) -> None:
        """Update the task URL based on the current task_id."""
        task_id = self.get_parameter_value("task_id")
        if not task_id:
            return

        try:
            base_url = self._get_shotgrid_config()["base_url"]
            task_url = f"{base_url.rstrip('/')}/detail/Task/{task_id}"
        except Exception:
            task_url = f"https://shotgrid.autodesk.com/detail/Task/{task_id}"

        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name="task_url", value=task_url, node_name=self.name)
        )
        self.parameter_output_values["task_url"] = task_url
        self.publish_update_to_parameter("task_url", task_url)

    def _resolve_user_id(self, assigned_to: str) -> str | None:
        """Resolve user ID from login name or return the ID if already provided."""
        if not assigned_to:
            return None

        # If it's already a numeric ID, return it
        try:
            int(assigned_to)
        except ValueError:
            # Otherwise, try to resolve by login name
            try:
                access_token = self._get_access_token()
                base_url = self._get_shotgrid_config()["base_url"]
                url = f"{base_url}api/v1/entity/human_users"

                params = {"fields": "id,login", "filter[login]": assigned_to}
                headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

                with httpx.Client() as client:
                    response = client.get(url, headers=headers, params=params)
                    if response.status_code == HTTP_OK:
                        data = response.json()
                        users = data.get("data", [])
                        if users:
                            return str(users[0]["id"])
                    logger.warning(f"{self.name}: Could not find user with login '{assigned_to}'")
                    return None

            except Exception as e:
                logger.error(f"{self.name}: Error resolving user '{assigned_to}': {e}")
                return None
        else:
            return assigned_to

    def _prepare_update_data(self) -> dict:
        """Prepare the update data from input parameters."""
        task_name = self.get_parameter_value("task_name")
        status = self.get_parameter_value("status")
        assigned_to = self.get_parameter_value("assigned_to")
        priority = self.get_parameter_value("priority")
        start_date = self.get_parameter_value("start_date")
        due_date = self.get_parameter_value("due_date")
        description = self.get_parameter_value("description")

        update_data = {}

        if task_name is not None:
            update_data["content"] = task_name
        if status is not None:
            update_data["sg_status_list"] = status
        if priority is not None:
            update_data["sg_priority"] = priority
        if start_date is not None:
            update_data["sg_start_date"] = start_date
        if due_date is not None:
            update_data["sg_due_date"] = due_date
        if description is not None:
            update_data["sg_description"] = description

        # Handle assigned_to separately as it requires relationship update
        if assigned_to is not None:
            user_id = self._resolve_user_id(assigned_to)
            if user_id:
                update_data["task_assignees"] = [{"type": "HumanUser", "id": int(user_id)}]
            else:
                logger.warning(f"{self.name}: Could not resolve user '{assigned_to}', skipping assignment")

        return update_data

    def _extract_task_data(self, task_data: dict) -> dict:
        """Extract and process task data from API response."""
        attributes = task_data.get("attributes", {})
        relationships = task_data.get("relationships", {})

        # Safely extract nested data
        step_data = relationships.get("step", {}) or {}
        step_name = step_data.get("data", {}) or {}

        task_assignees_data = relationships.get("task_assignees", {}) or {}

        entity_data = relationships.get("entity", {}) or {}
        project_data = relationships.get("project", {}) or {}

        # Extract assignee information
        assigned_to_name = ""
        if task_assignees_data.get("data"):
            assignee_data = task_assignees_data["data"][0] if task_assignees_data["data"] else {}
            assigned_to_name = assignee_data.get("name", "")

        return {
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
            "assigned_to_name": assigned_to_name,
        }

    def _update_output_parameters(self, processed_data: dict) -> None:
        """Update all output parameters with the processed task data."""
        params = {
            "updated_task_id": str(processed_data.get("id", "")),
            "updated_task_name": processed_data.get("content", ""),
            "updated_status": processed_data.get("sg_status_list", ""),
            "updated_assigned_to": processed_data.get("assigned_to_name", ""),
            "updated_priority": processed_data.get("sg_priority", ""),
            "updated_start_date": processed_data.get("sg_start_date", ""),
            "updated_due_date": processed_data.get("sg_due_date", ""),
            "updated_description": processed_data.get("sg_description", ""),
            "task_data": {
                "id": processed_data.get("id"),
                "content": processed_data.get("content"),
                "sg_status_list": processed_data.get("sg_status_list"),
                "step": processed_data.get("step"),
                "task_assignees": processed_data.get("task_assignees"),
                "sg_priority": processed_data.get("sg_priority"),
                "sg_start_date": processed_data.get("sg_start_date"),
                "sg_due_date": processed_data.get("sg_due_date"),
                "sg_description": processed_data.get("sg_description"),
                "entity": processed_data.get("entity"),
                "project": processed_data.get("project"),
            },
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def process(self) -> None:
        """Update the task with the provided information."""
        try:
            # Get and validate task ID
            task_id = self.get_parameter_value("task_id")
            if not task_id:
                logger.error(f"{self.name}: Task ID is required")
                return

            # Prepare update data
            update_data = self._prepare_update_data()
            if not update_data:
                logger.warning(f"{self.name}: No fields to update")
                return

            # Make the update request
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/tasks/{task_id}"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            with httpx.Client() as client:
                response = client.patch(url, headers=headers, json={"data": update_data})
                response.raise_for_status()

                # Process the response
                updated_data = response.json()
                task_data = updated_data.get("data", {})

                if not task_data:
                    logger.error(f"{self.name}: No task data returned from update")
                    return

                # Extract and process task data
                processed_data = self._extract_task_data(task_data)

                # Update output parameters
                self._update_output_parameters(processed_data)

                # Update task URL
                self._update_task_url()

                logger.info(f"{self.name}: Successfully updated task {task_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.name}: HTTP error updating task: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"{self.name}: Error updating task: {e}")
