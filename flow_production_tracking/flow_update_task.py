from typing import Any

from base_shotgrid_node import BaseShotGridNode
from flow_utils import create_shotgrid_api

from griptape_nodes.exe_types.core_types import Parameter, ParameterGroup, ParameterMessage, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.traits.options import Options


class FlowUpdateTask(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Dynamic message that will be updated with the updated task link
        self.task_message = ParameterMessage(
            name="task_message",
            title="Task Management",
            value="Update a task to see the link to view it in ShotGrid. Click the button to view all tasks.",
            button_link="",
            button_text="View All Tasks",
            variant="info",
            full_width=True,
        )
        self.add_node_element(self.task_message)

        # Set the initial link to the main tasks page
        self._update_task_message_initial()

        with ParameterGroup(name="task_input") as task_input:
            self.add_parameter(
                Parameter(
                    name="task_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the task to update.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="task_content",
                    type="string",
                    default_value=None,
                    tooltip="The new content/name for the task (optional).",
                )
            )
            self.add_parameter(
                Parameter(
                    name="task_status",
                    type="string",
                    default_value=None,
                    tooltip="The new status for this task (optional).",
                    traits={Options(choices=["wtg", "ip", "fin", "rev", "hld", "na"])},
                )
            )
            self.add_parameter(
                Parameter(
                    name="assignee_id",
                    type="string",
                    default_value=None,
                    tooltip="The user ID to assign this task to (optional).",
                    traits={Options(choices=["No users available"])},
                )
            )
            self.add_parameter(
                Parameter(
                    name="step_id",
                    type="string",
                    default_value=None,
                    tooltip="The step ID for this task (optional).",
                    traits={Options(choices=["No steps available"])},
                )
            )

        # Output parameters
        self.add_parameter(
            Parameter(
                name="updated_task",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The updated task data",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="task_id",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The ID of the updated task",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

        self.add_node_element(task_input)

        # Populate step and user choices after all parameters are added
        self._populate_step_choices()
        self._populate_user_choices()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "task_id" and value:
            # Load task data when task ID is provided
            self._load_task_data(value)

    def _update_task_message_initial(self) -> None:
        """Set the initial value of the ParameterMessage to the main ShotGrid instance."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            self.task_message.value = (
                "Update a task to see the link to view it in ShotGrid. Click the button to view all tasks."
            )
            self.task_message.button_link = base_url
            logger.info(f"{self.name}: Set initial task message to main ShotGrid instance.")
        except Exception as e:
            logger.error(f"{self.name}: Failed to set initial task message: {e}")

    def _update_task_message(self, task_id: int, task_content: str) -> None:
        """Update the ParameterMessage with a link to the updated task."""
        try:
            # Construct the full ShotGrid URL for the task
            base_url = self._get_shotgrid_config()["base_url"]
            task_url = f"{base_url}page/task_default?entity_type=Task&task_id={task_id}"

            # Update the button_link and value of the ParameterMessage
            self.task_message.button_link = task_url
            self.task_message.value = (
                f"Task '{task_content}' updated successfully! Click the button to view it in ShotGrid."
            )
            logger.info(f"{self.name}: Updated task message with link to task {task_id}")
        except Exception as e:
            logger.error(f"{self.name}: Failed to update task message: {e}")

    def _load_task_data(self, task_id: str) -> None:
        """Load task data when task ID is provided"""
        try:
            # Get access token and create API instance
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Get task data
            task_data = api.get_entity_data("tasks", int(task_id))

            if task_data:
                attrs = task_data.get("attributes", {})

                # Set current values as defaults
                current_content = attrs.get("content", "")
                current_status = attrs.get("sg_status_list", "")

                # Update parameter values with current task data
                self.parameter_values["task_content"] = current_content
                self.parameter_values["task_status"] = current_status

                logger.info(f"{self.name}: Loaded task data for task {task_id}")
            else:
                logger.warning(f"{self.name}: Could not load task data for task {task_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load task data: {e}")

    def _populate_step_choices(self) -> None:
        """Populate the step_id parameter with available steps"""
        try:
            # Get access token and create API instance
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Get steps
            steps = api.get_steps()

            if steps:
                choices = []
                for step in steps:
                    step_id = step.get("id")
                    step_name = step.get("attributes", {}).get("short_name", f"Step {step_id}")
                    step_code = step.get("attributes", {}).get("code", "")

                    if step_code:
                        choice_text = f"{step_name} ({step_code})"
                    else:
                        choice_text = step_name

                    choices.append(choice_text)

                # Update the step_id parameter with the new choices
                self._update_option_choices("step_id", choices, choices[0] if choices else "No steps available")
                logger.info(f"{self.name}: Populated {len(choices)} step choices")
            else:
                self._update_option_choices("step_id", ["No steps available"], "No steps available")
                logger.info(f"{self.name}: No steps found")

        except Exception as e:
            logger.warning(f"{self.name}: Could not populate step choices: {e}")
            self._update_option_choices("step_id", ["No steps available"], "No steps available")

    def _populate_user_choices(self) -> None:
        """Populate the assignee_id parameter with available users"""
        try:
            # Get access token and create API instance
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Get users
            users = api.get_users()

            if users:
                choices = []
                for user in users:
                    user_id = user.get("id")
                    user_name = user.get("attributes", {}).get("name", f"User {user_id}")
                    user_login = user.get("attributes", {}).get("login", "")

                    if user_login:
                        choice_text = f"{user_name} ({user_login})"
                    else:
                        choice_text = user_name

                    choices.append(choice_text)

                # Update the assignee_id parameter with the new choices
                self._update_option_choices("assignee_id", choices, choices[0] if choices else "No users available")
                logger.info(f"{self.name}: Populated {len(choices)} user choices")
            else:
                self._update_option_choices("assignee_id", ["No users available"], "No users available")
                logger.info(f"{self.name}: No users found")

        except Exception as e:
            logger.warning(f"{self.name}: Could not populate user choices: {e}")
            self._update_option_choices("assignee_id", ["No users available"], "No users available")

    def process(self) -> None:
        try:
            # Get input parameters
            task_id = self.get_parameter_value("task_id")
            task_content = self.get_parameter_value("task_content")
            task_status = self.get_parameter_value("task_status")
            assignee_id = self.get_parameter_value("assignee_id")
            step_id = self.get_parameter_value("step_id")

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

            # Prepare update data
            update_data = {}
            has_updates = False

            if task_content is not None:
                update_data["content"] = task_content
                has_updates = True

            if task_status is not None:
                update_data["sg_status_list"] = task_status
                has_updates = True

            # Add step if provided
            if step_id and step_id != "No steps available":
                # Extract step ID from the selected choice
                try:
                    steps = api.get_steps()
                    step_to_use = None

                    for step in steps:
                        step_id_from_api = step.get("id")
                        step_name = step.get("attributes", {}).get("short_name", "")
                        step_code = step.get("attributes", {}).get("code", "")

                        if step_code:
                            choice_text = f"{step_name} ({step_code})"
                        else:
                            choice_text = step_name

                        if choice_text == step_id:
                            step_to_use = step_id_from_api
                            break

                    if step_to_use:
                        update_data["step"] = {"type": "Step", "id": step_to_use}
                        has_updates = True
                        logger.info(f"{self.name}: Using step ID: {step_to_use}")
                    else:
                        logger.warning(f"{self.name}: Could not find step ID for selection: {step_id}")

                except Exception as e:
                    logger.warning(f"{self.name}: Error parsing step selection: {e}")

            # Add assignee if provided
            if assignee_id and assignee_id != "No users available":
                # Extract user ID from the selected choice
                try:
                    users = api.get_users()
                    user_to_use = None

                    for user in users:
                        user_id_from_api = user.get("id")
                        user_name = user.get("attributes", {}).get("name", "")
                        user_login = user.get("attributes", {}).get("login", "")

                        if user_login:
                            choice_text = f"{user_name} ({user_login})"
                        else:
                            choice_text = user_name

                        if choice_text == assignee_id:
                            user_to_use = user_id_from_api
                            break

                    if user_to_use:
                        update_data["task_assignees"] = [{"type": "HumanUser", "id": user_to_use}]
                        has_updates = True
                        logger.info(f"{self.name}: Using user ID: {user_to_use}")
                    else:
                        logger.warning(f"{self.name}: Could not find user ID for selection: {assignee_id}")

                except Exception as e:
                    logger.warning(f"{self.name}: Error parsing user selection: {e}")

            if not has_updates:
                logger.warning(f"{self.name}: No updates provided")
                return

            # Update the task
            logger.info(f"{self.name}: Updating task {task_id} with data: {update_data}")

            updated_task = api.update_task(task_id, update_data)

            if updated_task:
                logger.info(f"{self.name}: Task updated successfully")

                # Update the ParameterMessage with a link to the updated task
                task_content_display = task_content or updated_task.get("attributes", {}).get(
                    "content", f"Task {task_id}"
                )
                self._update_task_message(task_id, task_content_display)

                # Output the results
                self.parameter_output_values["updated_task"] = updated_task
                self.parameter_output_values["task_id"] = str(task_id)

                logger.info(f"{self.name}: Successfully updated task {task_id}")
            else:
                logger.error(f"{self.name}: Failed to update task")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
