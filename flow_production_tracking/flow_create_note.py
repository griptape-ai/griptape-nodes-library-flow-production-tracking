from typing import Any

from base_shotgrid_node import BaseShotGridNode
from flow_utils import create_shotgrid_api
from griptape_nodes.exe_types.core_types import Parameter, ParameterGroup, ParameterMessage, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.traits.options import Options

# Entity types a note can be linked to via the note_links field.
LINKABLE_ENTITY_TYPES = ["None", "Asset", "Shot", "Sequence", "Episode", "Task", "Version", "Project"]


class FlowCreateNote(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Dynamic message that will be updated with the created note link
        self.note_message = ParameterMessage(
            name="note_message",
            title="Note Management",
            value="Create a note to see the link to view it in ShotGrid. Click the button to view all notes.",
            button_link="",
            button_text="View All Notes",
            variant="info",
            full_width=True,
        )
        self.add_node_element(self.note_message)

        # Set the initial link to the main notes page
        self._update_note_message_initial()

        with ParameterGroup(name="note_input") as note_input:
            self.add_parameter(
                Parameter(
                    name="project_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the project to create the note in.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="subject",
                    type="string",
                    default_value=None,
                    tooltip="The subject/title of the note to create.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="content",
                    type="string",
                    default_value=None,
                    tooltip="The body content of the note.",
                    ui_options={"multiline": True},
                )
            )
            self.add_parameter(
                Parameter(
                    name="link_entity_type",
                    type="string",
                    default_value="None",
                    tooltip="The type of entity to link this note to (optional).",
                    traits={Options(choices=LINKABLE_ENTITY_TYPES)},
                )
            )
            self.add_parameter(
                Parameter(
                    name="link_entity_id",
                    type="string",
                    default_value=None,
                    tooltip="The ID of the entity to link this note to (optional). Used with link_entity_type.",
                )
            )
            self.add_parameter(
                Parameter(
                    name="addressed_to_id",
                    type="string",
                    default_value=None,
                    tooltip="The user to address this note to (optional). They will be notified.",
                    traits={Options(choices=["No users available"])},
                )
            )
            self.add_parameter(
                Parameter(
                    name="note_type",
                    type="string",
                    default_value="Internal",
                    tooltip="The classification of this note (optional).",
                    traits={Options(choices=["Internal", "Client", "Vendor", "Direction"])},
                )
            )

        # Output parameters
        self.add_parameter(
            Parameter(
                name="created_note",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The created note data",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="note_id",
                output_type="string",
                type="string",
                default_value=None,
                tooltip="The ID of the created note",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

        self.add_node_element(note_input)

        # Populate user choices after all parameters are added
        self._populate_user_choices()

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "project_id" and value:
            # Repopulate user choices when project changes
            self._populate_user_choices()

    def _update_note_message_initial(self) -> None:
        """Set the initial value of the ParameterMessage to the main ShotGrid instance."""
        try:
            base_url = self._get_shotgrid_config()["base_url"]
            self.note_message.value = (
                "Create a note to see the link to view it in ShotGrid. Click the button to view all notes."
            )
            self.note_message.button_link = base_url
            logger.info(f"{self.name}: Set initial note message to main ShotGrid instance.")
        except Exception as e:
            logger.error(f"{self.name}: Failed to set initial note message: {e}")

    def _update_note_message(self, note_id: int, subject: str) -> None:
        """Update the ParameterMessage with a link to the created note."""
        try:
            # Construct the full ShotGrid URL for the note
            base_url = self._get_shotgrid_config()["base_url"]
            note_url = f"{base_url}detail/Note/{note_id}"

            # Update the button_link and value of the ParameterMessage
            self.note_message.button_link = note_url
            self.note_message.value = (
                f"Note '{subject}' created successfully! Click the button to view it in ShotGrid."
            )
            logger.info(f"{self.name}: Updated note message with link to note {note_id}")
        except Exception as e:
            logger.error(f"{self.name}: Failed to update note message: {e}")

    def _populate_user_choices(self) -> None:
        """Populate the addressed_to_id parameter with available users"""
        try:
            project_id = self.get_parameter_value("project_id")

            # Get access token and create API instance
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Get users
            if project_id:
                try:
                    project_id = int(project_id)
                    users = api.get_users(project_id)
                except (ValueError, TypeError):
                    users = api.get_users()
            else:
                users = api.get_users()

            if users:
                choices = ["None"]
                for user in users:
                    user_id = user.get("id")
                    user_name = user.get("attributes", {}).get("name", f"User {user_id}")
                    user_login = user.get("attributes", {}).get("login", "")

                    if user_login:
                        choice_text = f"{user_name} ({user_login})"
                    else:
                        choice_text = user_name

                    choices.append(choice_text)

                # Update the addressed_to_id parameter with the new choices
                self._update_option_choices("addressed_to_id", choices, "None")
                logger.info(f"{self.name}: Populated {len(choices) - 1} user choices")
            else:
                self._update_option_choices("addressed_to_id", ["No users available"], "No users available")
                logger.info(f"{self.name}: No users found")

        except Exception as e:
            logger.warning(f"{self.name}: Could not populate user choices: {e}")
            self._update_option_choices("addressed_to_id", ["No users available"], "No users available")

    def process(self) -> None:
        try:
            # Get input parameters
            project_id = self.get_parameter_value("project_id")
            subject = self.get_parameter_value("subject")
            content = self.get_parameter_value("content")
            link_entity_type = self.get_parameter_value("link_entity_type")
            link_entity_id = self.get_parameter_value("link_entity_id")
            addressed_to_id = self.get_parameter_value("addressed_to_id")
            note_type = self.get_parameter_value("note_type")

            if not project_id:
                logger.error(f"{self.name}: project_id is required")
                return

            if not subject:
                logger.error(f"{self.name}: subject is required")
                return

            if not content:
                logger.error(f"{self.name}: content is required")
                return

            # Convert project ID to integer
            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: project_id must be a valid integer")
                return

            # Get access token and base URL
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            api = create_shotgrid_api(access_token, base_url)

            # Prepare note data
            note_data = {
                "subject": subject,
                "content": content,
                "project": {"type": "Project", "id": project_id},
            }

            # Add note classification if provided
            if note_type:
                note_data["sg_note_type"] = note_type

            # Link the note to an entity if provided (note_links is a multi-entity field)
            if link_entity_type and link_entity_type != "None" and link_entity_id:
                try:
                    link_id = int(link_entity_id)
                    note_data["note_links"] = [{"type": link_entity_type, "id": link_id}]
                    logger.info(f"{self.name}: Linking note to {link_entity_type} {link_id}")
                except (ValueError, TypeError):
                    logger.warning(f"{self.name}: link_entity_id must be a valid integer; skipping note link")

            # Address the note to a user if provided
            if addressed_to_id and addressed_to_id not in ("None", "No users available"):
                try:
                    users = api.get_users(project_id)
                    user_to_use = None

                    for user in users:
                        user_id_from_api = user.get("id")
                        user_name = user.get("attributes", {}).get("name", "")
                        user_login = user.get("attributes", {}).get("login", "")

                        if user_login:
                            choice_text = f"{user_name} ({user_login})"
                        else:
                            choice_text = user_name

                        if choice_text == addressed_to_id:
                            user_to_use = user_id_from_api
                            break

                    if user_to_use:
                        note_data["addressings_to"] = [{"type": "HumanUser", "id": user_to_use}]
                        logger.info(f"{self.name}: Addressing note to user ID: {user_to_use}")
                    else:
                        logger.warning(f"{self.name}: Could not find user ID for selection: {addressed_to_id}")

                except Exception as e:
                    logger.warning(f"{self.name}: Error parsing user selection: {e}")

            # Create the note
            logger.info(f"{self.name}: Creating note with data: {note_data}")

            created_note = api.create_note(note_data)

            if created_note:
                note_id = created_note.get("id")
                logger.info(f"{self.name}: Note created successfully with ID: {note_id}")

                # Update the ParameterMessage with a link to the created note
                self._update_note_message(note_id, subject)

                # Output the results
                self.parameter_output_values["created_note"] = created_note
                self.parameter_output_values["note_id"] = str(note_id)

                logger.info(f"{self.name}: Successfully created note {note_id}")
            else:
                logger.error(f"{self.name}: Failed to create note")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
