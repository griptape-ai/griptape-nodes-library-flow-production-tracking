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


class FlowGetTaskStatus(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Input parameter
        self.add_parameter(
            ParameterString(
                name="task_id",
                default_value=None,
                tooltip="The ID of the task to get information for.",
                placeholder_text="Enter task ID (e.g., 6817)",
            )
        )

        # Output parameters - comprehensive task information
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
                name="task_id_output",
                type="str",
                default_value="",
                tooltip="ID of the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="task_name",
                default_value="",
                tooltip="Name/content of the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="pipeline_step",
                default_value="",
                tooltip="Pipeline step for the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="status",
                default_value="",
                tooltip="Status of the task",
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
                tooltip="Priority of the task",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Priority of the task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="start_date",
                default_value="",
                tooltip="Start date of the task",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Start date of the task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="due_date",
                default_value="",
                tooltip="Due date of the task",
                allowed_modes={ParameterMode.OUTPUT},
                placeholder_text="Due date of the task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="description",
                default_value="",
                tooltip="Description of the task",
                allowed_modes={ParameterMode.OUTPUT},
                multiline=True,
                placeholder_text="Description of the task",
            )
        )
        self.add_parameter(
            ParameterString(
                name="created_at",
                default_value="",
                tooltip="When the task was created",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="updated_at",
                default_value="",
                tooltip="When the task was last updated",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_data",
                type="json",
                default_value={},
                tooltip="Complete task data from ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update task_url when task_id changes."""
        if parameter.name == "task_id" and value:
            try:
                task_id = int(value)
                self._update_task_url(task_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid task_id value: {value}")
            except Exception as e:
                logger.warning(f"{self.name}: Failed to update task_url for task {value}: {e}")
        return super().after_value_set(parameter, value)

    def _update_task_url(self, task_id: int) -> None:
        """Update the task_url output parameter with the ShotGrid URL."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            task_url = f"{base_url}detail/Task/{task_id}"

            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="task_url", value=task_url, node_name=self.name)
            )
            self.parameter_output_values["task_url"] = task_url
            self.publish_update_to_parameter("task_url", task_url)
            logger.info(f"{self.name}: Updated task_url to: {task_url}")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to update task_url: {e}")

    def process(self) -> None:
        """Get comprehensive task information when process is run."""
        try:
            # Get input parameters
            task_id = self.get_parameter_value("task_id")

            if not task_id:
                logger.error(f"{self.name}: task_id is required")
                self._clear_all_outputs()
                return

            # Convert task_id to integer
            try:
                task_id = int(task_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: task_id must be a valid integer")
                self._clear_all_outputs()
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]

            # Fetch task data
            task_data = self._fetch_task_data(task_id, access_token, base_url)
            if not task_data:
                logger.error(f"{self.name}: Could not retrieve task data for task {task_id}")
                self._clear_all_outputs()
                return

            # Extract and populate all task information
            self._populate_task_information(task_data)

            logger.info(f"{self.name}: Successfully retrieved comprehensive task information for task {task_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error getting task information: {e}")
            self._clear_all_outputs()

    def _fetch_task_data(self, task_id: int, access_token: str, base_url: str) -> dict | None:
        """Fetch task data from ShotGrid API."""
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

    def _populate_task_information(self, task_data: dict) -> None:
        """Populate all task information parameters."""
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

            created_at = attributes.get("created_at", "")
            updated_at = attributes.get("updated_at", "")

            # Update all parameters using SetParameterValueRequest
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
                created_at,
                updated_at,
                task_data,
            )

        except Exception as e:
            logger.error(f"{self.name}: Failed to populate task information: {e}")

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
        created_at: str,
        updated_at: str,
        task_data: dict,
    ) -> None:
        """Update all task parameters using SetParameterValueRequest for proper UI updates."""
        params = {
            "task_url": task_url,
            "task_id_output": task_id,
            "task_name": task_name,
            "pipeline_step": pipeline_step,
            "status": status,
            "assigned_to": assigned_to,
            "priority": priority,
            "start_date": start_date,
            "due_date": due_date,
            "description": description,
            "created_at": created_at,
            "updated_at": updated_at,
            "task_data": task_data,
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

    def _clear_all_outputs(self) -> None:
        """Clear all output parameters."""
        empty_params = [
            "task_url",
            "task_id_output",
            "task_name",
            "pipeline_step",
            "status",
            "assigned_to",
            "priority",
            "start_date",
            "due_date",
            "description",
            "created_at",
            "updated_at",
            "task_data",
        ]

        for param_name in empty_params:
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value="", node_name=self.name)
            )
            self.parameter_output_values[param_name] = ""
            self.publish_update_to_parameter(param_name, "")
