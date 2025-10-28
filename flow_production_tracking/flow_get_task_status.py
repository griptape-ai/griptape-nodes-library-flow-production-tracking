from base_shotgrid_node import BaseShotGridNode
from flow_utils import create_shotgrid_api

from griptape_nodes.exe_types.core_types import Parameter, ParameterGroup, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowGetTaskStatus(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        with ParameterGroup(name="task_input") as task_input:
            self.add_parameter(
                Parameter(
                    name="task_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the task to get status for.",
                )
            )

        # Output parameters
        self.add_parameter(
            Parameter(
                name="task_status",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The current status of the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_content",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The content/name of the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_assignees",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The assignees of the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_step",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The step of the task",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_entity",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The entity this task belongs to",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_project",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The project this task belongs to",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_data",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="Complete task data",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

        self.add_node_element(task_input)

    def process(self) -> None:
        try:
            # Get input parameters
            task_id = self.get_parameter_value("task_id")

            if not task_id:
                logger.error(f"{self.name}: task_id is required")
                return

            # Convert task_id to integer
            try:
                task_id = int(task_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: task_id must be a valid integer")
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Get task data
            logger.info(f"{self.name}: Getting task data for task {task_id}")

            task_data = api.get_entity_data("tasks", task_id)

            if task_data:
                attrs = task_data.get("attributes", {})
                relationships = task_data.get("relationships", {})

                # Extract task information
                task_status = attrs.get("sg_status_list", "Unknown")
                task_content = attrs.get("content", "Unknown")

                # Get assignees
                assignees_data = relationships.get("task_assignees", {}).get("data", [])
                task_assignees = []
                for assignee in assignees_data:
                    assignee_info = {
                        "id": assignee.get("id"),
                        "name": assignee.get("name", "Unknown"),
                        "type": assignee.get("type", "HumanUser"),
                    }
                    task_assignees.append(assignee_info)

                # Get step information
                step_data = relationships.get("step", {}).get("data", {})
                task_step = step_data.get("name", "Unknown") if step_data else "Unknown"

                # Get entity information
                entity_data = relationships.get("entity", {}).get("data", {})
                task_entity = (
                    {
                        "id": entity_data.get("id"),
                        "name": entity_data.get("name", "Unknown"),
                        "type": entity_data.get("type", "Unknown"),
                    }
                    if entity_data
                    else {"id": None, "name": "Unknown", "type": "Unknown"}
                )

                # Get project information
                project_data = relationships.get("project", {}).get("data", {})
                task_project = (
                    {
                        "id": project_data.get("id"),
                        "name": project_data.get("name", "Unknown"),
                        "type": project_data.get("type", "Project"),
                    }
                    if project_data
                    else {"id": None, "name": "Unknown", "type": "Project"}
                )

                # Output the results
                self.parameter_output_values["task_status"] = task_status
                self.parameter_output_values["task_content"] = task_content
                self.parameter_output_values["task_assignees"] = task_assignees
                self.parameter_output_values["task_step"] = task_step
                self.parameter_output_values["task_entity"] = task_entity
                self.parameter_output_values["task_project"] = task_project
                self.parameter_output_values["task_data"] = task_data

                logger.info(f"{self.name}: Successfully retrieved task status for task {task_id}")
                logger.info(f"{self.name}: Task status: {task_status}, Content: {task_content}, Step: {task_step}")
            else:
                logger.error(f"{self.name}: Could not retrieve task data for task {task_id}")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
