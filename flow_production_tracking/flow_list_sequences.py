from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import (
    NodeMessageResult,
    Parameter,
    ParameterMode,
)
from griptape_nodes.exe_types.param_types.parameter_image import ParameterImage
from griptape_nodes.exe_types.param_types.parameter_string import ParameterString
from griptape_nodes.retained_mode.events.parameter_events import SetParameterValueRequest
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload
from griptape_nodes.traits.options import Options

# Default choices - will be populated dynamically
SEQUENCE_CHOICES = ["No sequences available"]
SEQUENCE_CHOICES_ARGS = []


class FlowListSequences(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            base_url.rstrip("/")
        except Exception:
            pass

        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to list sequences for.",
                placeholder_text="ID of the selected project",
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_id",
                default_value=None,
                tooltip="Filter sequences by episode ID (optional).",
                placeholder_text="ID of the episode (optional)",
            )
        )
        self.add_parameter(
            Parameter(
                name="all_sequences",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of sequences",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="selected_sequence",
                type="string",
                default_value="Load sequences to see options",
                tooltip="Select a sequence from the list. Use refresh button to update selected sequence data.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=SEQUENCE_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_sequence,
                        label="Refresh Selected",
                        full_width=True,
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterImage(
                name="sequence_image",
                default_value="",
                tooltip="Image/thumbnail of the selected sequence",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_description",
                default_value="",
                tooltip="Description of the selected sequence",
                allowed_modes={ParameterMode.OUTPUT},
                multiline=True,
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_url",
                default_value="",
                tooltip="URL of the selected sequence in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected sequence",
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_code",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Code of the selected sequence",
            )
        )
        self.add_parameter(
            Parameter(
                name="sequence_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected sequence",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_sequence":
            self.publish_update_to_parameter("selected_sequence", value)
            if value and value != "Load sequences to see options":
                sequences = self.get_parameter_value("all_sequences") or []
                selected_index = 0

                clean_selection = value.replace("📋 ", "").replace(" (Template)", "")

                for i, sequence in enumerate(sequences):
                    sequence_name = sequence.get("name", "")
                    sequence_code = sequence.get("code", "")
                    if sequence_name == clean_selection or sequence_code == clean_selection:
                        selected_index = i
                        break

                self._update_selected_sequence_data(
                    sequences[selected_index] if selected_index < len(sequences) else {}
                )
        return super().after_value_set(parameter, value)

    def _update_selected_sequence_data(self, sequence_data: dict) -> None:
        """Update sequence outputs based on selected sequence data."""
        if not sequence_data:
            return

        sequence_id = sequence_data.get("id", "")
        sequence_data.get("name", f"Sequence {sequence_id}")
        sequence_code = sequence_data.get("code", "")
        sequence_description = sequence_data.get("description") or sequence_data.get("sg_description") or ""
        sequence_image = sequence_data.get("sg_thumbnail") or sequence_data.get("image", "")

        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            sequence_url = f"{base_url.rstrip('/')}/detail/Sequence/{sequence_id}"
        except Exception:
            sequence_url = f"https://shotgrid.autodesk.com/detail/Sequence/{sequence_id}"

        params = {
            "sequence_id": sequence_id,
            "sequence_code": sequence_code,
            "sequence_data": sequence_data,
            "sequence_url": sequence_url,
            "sequence_description": sequence_description,
            "sequence_image": sequence_image,
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def _refresh_selected_sequence(
        self, button: Button, button_details: ButtonDetailsMessagePayload
    ) -> NodeMessageResult | None:
        """Refresh the selected sequence when the refresh button is clicked."""
        try:
            current_selection = self.get_parameter_value("selected_sequence")
            if not current_selection or current_selection == "Load sequences to see options":
                logger.warning(f"{self.name}: No sequence selected to refresh")
                return None

            clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")

            sequences = self.get_parameter_value("all_sequences") or []
            selected_sequence_id = None
            selected_index = 0

            for i, sequence in enumerate(sequences):
                sequence_name = sequence.get("name", "")
                sequence_code = sequence.get("code", "")
                if sequence_name == clean_selection or sequence_code == clean_selection:
                    selected_sequence_id = sequence.get("id")
                    selected_index = i
                    break

            if not selected_sequence_id:
                logger.warning(f"{self.name}: Could not find sequence ID for '{clean_selection}'")
                return None

            logger.info(f"{self.name}: Refreshing sequence {selected_sequence_id} ({clean_selection})")
            fresh_sequence_data = self._fetch_single_sequence(selected_sequence_id)

            if not fresh_sequence_data:
                logger.warning(f"{self.name}: Failed to fetch fresh data for sequence {selected_sequence_id}")
                return None

            sequences[selected_index] = fresh_sequence_data
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_sequences", value=sequences, node_name=self.name)
            )
            self.parameter_output_values["all_sequences"] = sequences
            self.publish_update_to_parameter("all_sequences", sequences)

            self._update_selected_sequence_data(fresh_sequence_data)

            logger.info(f"{self.name}: Successfully refreshed sequence {selected_sequence_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected sequence: {e}")
        return None

    def _fetch_single_sequence(self, sequence_id: int) -> dict | None:
        """Fetch a single sequence from ShotGrid API."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/sequences/{sequence_id}"

            params = {
                "fields": "id,code,name,episode,project,sg_status_list,image,sg_thumbnail,description,sg_description"
            }
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                sequence_data = data.get("data")

                if sequence_data:
                    sequence_data["url"] = f"{base_url}detail/Sequence/{sequence_id}"

                    attributes = sequence_data.get("attributes", {})
                    sequence_data.update(attributes)

                    return sequence_data

                return None

        except Exception as e:
            logger.error(f"{self.name}: Failed to fetch sequence {sequence_id}: {e}")
            return None

    def _fetch_sequences_from_api(self) -> list[dict]:
        """Fetch sequences from ShotGrid API."""
        project_id = self.get_parameter_value("project_id")
        episode_id = self.get_parameter_value("episode_id")

        if not project_id:
            msg = "project_id is required"
            raise ValueError(msg)

        try:
            project_id = int(project_id)
        except (ValueError, TypeError) as e:
            msg = "project_id must be a valid integer"
            raise ValueError(msg) from e

        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/sequences"

        params = {"fields": "id,code,name,episode,project,sg_status_list,image,sg_thumbnail,description,sg_description"}

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            all_sequences = data.get("data", [])

            sequences = []
            for sequence in all_sequences:
                sequence_project = sequence.get("relationships", {}).get("project", {}).get("data", {})
                sequence_project_id = sequence_project.get("id")

                if sequence_project_id != project_id:
                    continue

                if episode_id:
                    try:
                        episode_id_int = int(episode_id)
                        sequence_episode = sequence.get("relationships", {}).get("episode", {}).get("data", {})
                        sequence_episode_id = sequence_episode.get("id")
                        if sequence_episode_id != episode_id_int:
                            continue
                    except (ValueError, TypeError):
                        pass

                sequences.append(sequence)

            return sequences

    def _process_sequences_to_choices(self, sequences: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw sequences data into choices format."""
        sequence_list = []
        choices_args = []
        choices_names = []

        for sequence in sequences:
            sequence_data = {
                "id": sequence.get("id"),
                "code": sequence.get("attributes", {}).get("code"),
                "name": sequence.get("attributes", {}).get("name"),
                "episode": sequence.get("relationships", {}).get("episode", {}).get("data", {}).get("id"),
                "sg_status_list": sequence.get("attributes", {}).get("sg_status_list"),
                "image": sequence.get("attributes", {}).get("image"),
                "sg_thumbnail": sequence.get("attributes", {}).get("sg_thumbnail"),
                "description": sequence.get("attributes", {}).get("description"),
                "sg_description": sequence.get("attributes", {}).get("sg_description"),
                "project": sequence.get("relationships", {}).get("project", {}).get("data", {}).get("id"),
            }
            sequence_list.append(sequence_data)

            sequence_id = sequence_data["id"]
            sequence_code = sequence_data["code"] or ""
            sequence_status = sequence_data["sg_status_list"] or "Unknown"

            thumbnail_url = sequence_data.get("sg_thumbnail") or sequence_data.get("image") or ""

            display_name = sequence_code if sequence_code else f"Sequence {sequence_id}"
            subtitle = sequence_status

            choice = {
                "name": display_name,
                "icon": thumbnail_url,
                "subtitle": subtitle,
                "args": {
                    "sequence_id": sequence_id,
                    "sequence_data": sequence_data,
                },
            }
            choices_args.append(choice)
            choices_names.append(display_name)

        return sequence_list, choices_names

    def process(self) -> None:
        """Process the node - automatically load sequences when run."""
        try:
            current_selection = self.get_parameter_value("selected_sequence")

            project_id = self.get_parameter_value("project_id")
            if not project_id:
                logger.warning(f"{self.name}: project_id is required")
                self._update_option_choices("selected_sequence", ["No project selected"], "No project selected")
                return

            logger.info(f"{self.name}: Loading sequences from ShotGrid for project {project_id}...")
            sequences = self._fetch_sequences_from_api()

            if not sequences:
                logger.warning(f"{self.name}: No sequences found for project {project_id}")
                self._update_option_choices("selected_sequence", ["No sequences available"], "No sequences available")
                return

            sequence_list, choices_names = self._process_sequences_to_choices(sequences)

            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_sequences", value=sequence_list, node_name=self.name)
            )
            self.parameter_output_values["all_sequences"] = sequence_list
            self.publish_update_to_parameter("all_sequences", sequence_list)

            selected_value = choices_names[0] if choices_names else "No sequences available"
            selected_index = 0

            if (
                current_selection
                and current_selection != "Load sequences to see options"
                and current_selection in choices_names
            ):
                selected_index = choices_names.index(current_selection)
                selected_value = current_selection
                logger.info(f"{self.name}: Preserved selection: {current_selection}")
            else:
                selected_value = choices_names[0]
                selected_index = 0
                logger.info(f"{self.name}: Selected first sequence: {choices_names[0]}")

            logger.info(f"{self.name}: Updating dropdown with {len(choices_names)} choices: {choices_names[:3]}...")
            self._update_option_choices("selected_sequence", choices_names, selected_value)
            logger.info(f"{self.name}: Dropdown updated, selected_value: {selected_value}")

            self._update_selected_sequence_data(sequences[selected_index] if selected_index < len(sequences) else {})

            logger.info(f"{self.name}: Successfully loaded {len(sequence_list)} sequences")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load sequences: {e}")
            self._update_option_choices("selected_sequence", ["Error loading sequences"], "Error loading sequences")
