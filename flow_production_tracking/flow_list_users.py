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
USER_CHOICES = ["No users available"]


class FlowListUsers(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to filter users by (optional). If not provided, all users will be listed.",
                placeholder_text="ID of the project to filter users by",
            )
        )
        self.add_parameter(
            Parameter(
                name="all_users",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of users",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="selected_user",
                type="string",
                default_value="Load users to see options",
                tooltip="Select a user from the list. Use refresh button to update selected user data.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=USER_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_user,
                        label="Refresh Selected",
                        full_width=True,
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterString(
                name="user_url",
                default_value="",
                tooltip="URL to view the user in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="user_id",
                type="str",
                default_value="",
                tooltip="ID of the selected user",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="user_name",
                default_value="",
                tooltip="Name of the selected user",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="user_email",
                default_value="",
                tooltip="Email address of the selected user",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="user_login",
                default_value="",
                tooltip="Login name of the selected user",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="user_status",
                default_value="",
                tooltip="Status of the selected user (active, inactive, etc.)",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="user_role",
                default_value="",
                tooltip="Role of the selected user",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="user_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected user",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_user" and value and value != "Load users to see options":
            # Update selected user data when a user is selected
            self.publish_update_to_parameter("selected_user", value)
            if value and value != "Load users to see options":
                # Find the index of the selected user by matching display names
                users = self.get_parameter_value("all_users") or []
                selected_index = 0

                # Clean the selection to match against user names
                clean_selection = value.replace("📋 ", "").replace(" (Template)", "")

                for i, user in enumerate(users):
                    user_name = user.get("name", "")
                    if user_name == clean_selection:
                        selected_index = i
                        break

                self._update_selected_user_data_from_processed(
                    users[selected_index] if selected_index < len(users) else {}
                )
        return super().after_value_set(parameter, value)

    def _refresh_selected_user(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:  # noqa: ARG002
        """Refresh the currently selected user information."""
        try:
            current_selection = self.get_parameter_value("selected_user")
            if not current_selection or current_selection == "Load users to see options":
                logger.warning(f"{self.name}: No user selected to refresh")
                return

            # Clean the selection to get the actual user name
            clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")

            # Get the current user ID from all_users
            users = self.get_parameter_value("all_users") or []
            selected_user_id = None
            selected_index = 0

            for i, user in enumerate(users):
                user_name = user.get("name", "")
                if user_name == clean_selection:
                    selected_user_id = user.get("id")
                    selected_index = i
                    break

            if not selected_user_id:
                logger.warning(f"{self.name}: Could not find user ID for '{clean_selection}'")
                return

            # Fetch fresh data for this specific user
            logger.info(f"{self.name}: Refreshing user {selected_user_id} ({clean_selection})")
            fresh_user_data = self._fetch_single_user(selected_user_id)

            if not fresh_user_data:
                logger.warning(f"{self.name}: Failed to fetch fresh data for user {selected_user_id}")
                return

            # Update the user in all_users using SetParameterValueRequest
            users[selected_index] = fresh_user_data
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_users", value=users, node_name=self.name)
            )
            self.parameter_output_values["all_users"] = users
            self.publish_update_to_parameter("all_users", users)

            # Update the user data display
            self._update_selected_user_data_from_processed(fresh_user_data)

            logger.info(f"{self.name}: Successfully refreshed user {selected_user_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected user: {e}")
        return

    def _process_users_to_choices(self, users: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw users data into choices format."""
        user_list = []
        choices_names = []

        for user in users:
            # Safely extract attributes with null checks
            attributes = user.get("attributes") or {}

            user_data = {
                "id": user.get("id"),
                "name": attributes.get("name"),
                "email": attributes.get("email"),
                "login": attributes.get("login"),
                "status": attributes.get("sg_status_list"),
                "role": attributes.get("role"),
                "first_name": attributes.get("firstname"),
                "last_name": attributes.get("lastname"),
                "phone": attributes.get("phone"),
                "department": attributes.get("department"),
                "title": attributes.get("title"),
            }
            user_list.append(user_data)

            # Create choice for the dropdown - use name or login as fallback
            user_name = user_data["name"] or user_data["login"] or f"User {user_data['id']}"
            choices_names.append(user_name)

        return user_list, choices_names

    def _update_selected_user_data_from_processed(self, user_data: dict) -> None:
        """Update user outputs based on selected user data (processed structure)."""
        if not user_data:
            return

        # Extract basic user info (from processed data structure)
        user_id = user_data.get("id", "")
        user_name = user_data.get("name", f"User {user_id}")
        user_email = user_data.get("email", "")
        user_login = user_data.get("login", "")
        user_status = user_data.get("status", "")
        user_role = user_data.get("role", "")

        # Generate web UI URL
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            user_url = f"{base_url.rstrip('/')}/detail/HumanUser/{user_id}"
        except Exception:
            user_url = f"https://shotgrid.autodesk.com/detail/HumanUser/{user_id}"

        # Update all user parameters using SetParameterValueRequest
        params = {
            "user_url": user_url,
            "user_id": str(user_id),
            "user_name": user_name,
            "user_email": user_email,
            "user_login": user_login,
            "user_status": user_status,
            "user_role": user_role,
            "user_data": user_data,
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def _fetch_single_user(self, user_id: int) -> dict | None:
        """Fetch a single user by ID."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/human_users/{user_id}"

            params = {"fields": "id,name,email,login,sg_status_list,role,firstname,lastname,phone,department,title"}
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    user_data = data.get("data")

                    if user_data:
                        # Safely extract attributes with null checks
                        attributes = user_data.get("attributes") or {}

                        # Process the user data to match our processed structure
                        processed_user = {
                            "id": user_data.get("id"),
                            "name": attributes.get("name"),
                            "email": attributes.get("email"),
                            "login": attributes.get("login"),
                            "status": attributes.get("sg_status_list"),
                            "role": attributes.get("role"),
                            "first_name": attributes.get("firstname"),
                            "last_name": attributes.get("lastname"),
                            "phone": attributes.get("phone"),
                            "department": attributes.get("department"),
                            "title": attributes.get("title"),
                        }
                        return processed_user

                logger.warning(f"{self.name}: Failed to fetch user {user_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"{self.name}: Error fetching user {user_id}: {e}")
            return None

    def _fetch_users_from_api(self) -> list[dict]:
        """Fetch users from ShotGrid API."""
        # Get input parameters
        project_id = self.get_parameter_value("project_id")

        # Get access token
        access_token = self._get_access_token()

        # Make request to get users
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        # Get base URL
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/human_users"

        # Add fields to get user information
        params = {"fields": "id,name,email,login,sg_status_list,role,firstname,lastname,phone,department,title"}

        # Add project filter if project_id is provided
        if project_id:
            try:
                project_id = int(project_id)
                params["filter[projects.Project.id]"] = str(project_id)
            except (ValueError, TypeError):
                logger.warning(f"{self.name}: Invalid project_id, ignoring filter")

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            users = data.get("data", [])

            return users

    def process(self) -> None:
        """Process the node - automatically load users when run."""
        try:
            # Get current selection to preserve it
            current_selection = self.get_parameter_value("selected_user")

            # Load users from ShotGrid
            logger.info(f"{self.name}: Loading users from ShotGrid...")
            users = self._fetch_users_from_api()

            if not users:
                logger.warning(f"{self.name}: No users found")
                self._update_option_choices("selected_user", ["No users available"], "No users available")
                return

            # Process users to choices
            user_list, choices_names = self._process_users_to_choices(users)

            # Store all users data first using SetParameterValueRequest
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_users", value=user_list, node_name=self.name)
            )
            self.parameter_output_values["all_users"] = user_list
            self.publish_update_to_parameter("all_users", user_list)

            # Determine what to select
            selected_value = choices_names[0] if choices_names else "No users available"
            selected_index = 0

            # Try to preserve the current selection
            if (
                current_selection
                and current_selection != "Load users to see options"
                and current_selection in choices_names
            ):
                selected_index = choices_names.index(current_selection)
                selected_value = current_selection
                logger.info(f"{self.name}: Preserved selection: {current_selection}")
            else:
                selected_value = choices_names[0]
                selected_index = 0
                logger.info(f"{self.name}: Selected first user: {choices_names[0]}")

            # Update the dropdown choices
            logger.info(f"{self.name}: Updating dropdown with {len(choices_names)} choices: {choices_names[:3]}...")
            self._update_option_choices("selected_user", choices_names, selected_value)
            logger.info(f"{self.name}: Dropdown updated, selected_value: {selected_value}")

            # Update the selected user data
            self._update_selected_user_data_from_processed(
                user_list[selected_index] if selected_index < len(user_list) else {}
            )

            logger.info(f"{self.name}: Successfully loaded {len(user_list)} users")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load users: {e}")
            self._update_option_choices("selected_user", ["Error loading users"], "Error loading users")
