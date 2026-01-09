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
SHOT_CHOICES = ["No shots available"]
SHOT_CHOICES_ARGS = []


class FlowListShots(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Get the user's ShotGrid URL for the link
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            shots_url = base_url.rstrip("/")
        except Exception:
            shots_url = "https://shotgrid.autodesk.com/shots"

        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to list shots for.",
                placeholder_text="ID of the selected project",
            )
        )
        self.add_parameter(
            ParameterString(
                name="sequence_id",
                default_value=None,
                tooltip="Filter shots by sequence ID (optional).",
                placeholder_text="ID of the sequence (optional)",
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_id",
                default_value=None,
                tooltip="Filter shots by episode ID (optional).",
                placeholder_text="ID of the episode (optional)",
            )
        )
        self.add_parameter(
            Parameter(
                name="all_shots",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of shots",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="selected_shot",
                type="string",
                default_value="Load shots to see options",
                tooltip="Select a shot from the list. Use refresh button to update selected shot data.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=SHOT_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_shot,
                        label="Refresh Selected",
                        full_width=True,
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterImage(
                name="shot_image",
                default_value="",
                tooltip="Image/thumbnail of the selected shot",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="shot_description",
                default_value="",
                tooltip="Description of the selected shot",
                allowed_modes={ParameterMode.OUTPUT},
                multiline=True,
            )
        )
        self.add_parameter(
            ParameterString(
                name="shot_url",
                default_value="",
                tooltip="URL of the selected shot in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="shot_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected shot",
            )
        )
        self.add_parameter(
            Parameter(
                name="shot_code",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Code of the selected shot",
            )
        )
        self.add_parameter(
            Parameter(
                name="shot_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected shot",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_shot":
            self.publish_update_to_parameter("selected_shot", value)
            if value and value != "Load shots to see options":
                shots = self.get_parameter_value("all_shots") or []
                selected_index = 0

                clean_selection = value.replace("📋 ", "").replace(" (Template)", "")

                for i, shot in enumerate(shots):
                    shot_name = shot.get("name", "")
                    shot_code = shot.get("code", "")
                    if shot_name == clean_selection or shot_code == clean_selection:
                        selected_index = i
                        break

                self._update_selected_shot_data(shots[selected_index] if selected_index < len(shots) else {})
        return super().after_value_set(parameter, value)

    def _update_selected_shot_data(self, shot_data: dict) -> None:
        """Update shot outputs based on selected shot data."""
        if not shot_data:
            return

        shot_id = shot_data.get("id", "")
        shot_name = shot_data.get("name", f"Shot {shot_id}")
        shot_code = shot_data.get("code", "")
        shot_description = shot_data.get("description") or shot_data.get("sg_description") or ""
        shot_image = shot_data.get("sg_thumbnail") or shot_data.get("image", "")

        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            shot_url = f"{base_url.rstrip('/')}/detail/Shot/{shot_id}"
        except Exception:
            shot_url = f"https://shotgrid.autodesk.com/detail/Shot/{shot_id}"

        params = {
            "shot_id": shot_id,
            "shot_code": shot_code,
            "shot_data": shot_data,
            "shot_url": shot_url,
            "shot_description": shot_description,
            "shot_image": shot_image,
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def _refresh_selected_shot(
        self, button: Button, button_details: ButtonDetailsMessagePayload
    ) -> NodeMessageResult | None:
        """Refresh the selected shot when the refresh button is clicked."""
        try:
            current_selection = self.get_parameter_value("selected_shot")
            if not current_selection or current_selection == "Load shots to see options":
                logger.warning(f"{self.name}: No shot selected to refresh")
                return None

            clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")

            shots = self.get_parameter_value("all_shots") or []
            selected_shot_id = None
            selected_index = 0

            for i, shot in enumerate(shots):
                shot_name = shot.get("name", "")
                shot_code = shot.get("code", "")
                if shot_name == clean_selection or shot_code == clean_selection:
                    selected_shot_id = shot.get("id")
                    selected_index = i
                    break

            if not selected_shot_id:
                logger.warning(f"{self.name}: Could not find shot ID for '{clean_selection}'")
                return None

            logger.info(f"{self.name}: Refreshing shot {selected_shot_id} ({clean_selection})")
            fresh_shot_data = self._fetch_single_shot(selected_shot_id)

            if not fresh_shot_data:
                logger.warning(f"{self.name}: Failed to fetch fresh data for shot {selected_shot_id}")
                return None

            shots[selected_index] = fresh_shot_data
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_shots", value=shots, node_name=self.name)
            )
            self.parameter_output_values["all_shots"] = shots
            self.publish_update_to_parameter("all_shots", shots)

            self._update_selected_shot_data(fresh_shot_data)

            logger.info(f"{self.name}: Successfully refreshed shot {selected_shot_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected shot: {e}")
        return None

    def _fetch_single_shot(self, shot_id: int) -> dict | None:
        """Fetch a single shot from ShotGrid API."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/shots/{shot_id}"

            params = {
                "fields": "id,code,name,sg_sequence,project,episode,sg_status_list,image,sg_thumbnail,description,sg_description"
            }
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                shot_data = data.get("data")

                if shot_data:
                    shot_data["url"] = f"{base_url}detail/Shot/{shot_id}"

                    attributes = shot_data.get("attributes", {})
                    shot_data.update(attributes)

                    return shot_data

                return None

        except Exception as e:
            logger.error(f"{self.name}: Failed to fetch shot {shot_id}: {e}")
            return None

    def _fetch_shots_from_api(self) -> list[dict]:
        """Fetch shots from ShotGrid API."""
        project_id = self.get_parameter_value("project_id")
        sequence_id = self.get_parameter_value("sequence_id")
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
        url = f"{base_url}api/v1/entity/shots"

        params = {
            "fields": "id,code,name,sg_sequence,project,episode,sg_status_list,image,sg_thumbnail,description,sg_description"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            all_shots = data.get("data", [])

            shots = []
            for shot in all_shots:
                shot_project = shot.get("relationships", {}).get("project", {}).get("data", {})
                shot_project_id = shot_project.get("id")

                if shot_project_id != project_id:
                    continue

                if sequence_id:
                    try:
                        sequence_id_int = int(sequence_id)
                        shot_sequence = shot.get("relationships", {}).get("sg_sequence", {}).get("data", {})
                        shot_sequence_id = shot_sequence.get("id")
                        if shot_sequence_id != sequence_id_int:
                            continue
                    except (ValueError, TypeError):
                        pass

                if episode_id:
                    try:
                        episode_id_int = int(episode_id)
                        shot_episode = shot.get("relationships", {}).get("episode", {}).get("data", {})
                        shot_episode_id = shot_episode.get("id")
                        if shot_episode_id != episode_id_int:
                            continue
                    except (ValueError, TypeError):
                        pass

                shots.append(shot)

            return shots

    def _process_shots_to_choices(self, shots: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw shots data into choices format."""
        shot_list = []
        choices_args = []
        choices_names = []

        for shot in shots:
            shot_data = {
                "id": shot.get("id"),
                "code": shot.get("attributes", {}).get("code"),
                "name": shot.get("attributes", {}).get("name"),
                "sg_sequence": shot.get("relationships", {}).get("sg_sequence", {}).get("data", {}).get("id"),
                "sg_status_list": shot.get("attributes", {}).get("sg_status_list"),
                "image": shot.get("attributes", {}).get("image"),
                "sg_thumbnail": shot.get("attributes", {}).get("sg_thumbnail"),
                "description": shot.get("attributes", {}).get("description"),
                "sg_description": shot.get("attributes", {}).get("sg_description"),
                "project": shot.get("relationships", {}).get("project", {}).get("data", {}).get("id"),
                "episode": shot.get("relationships", {}).get("episode", {}).get("data", {}).get("id"),
            }
            shot_list.append(shot_data)

            shot_id = shot_data["id"]
            shot_code = shot_data["code"] or ""
            shot_status = shot_data["sg_status_list"] or "Unknown"

            thumbnail_url = shot_data.get("sg_thumbnail") or shot_data.get("image") or ""

            display_name = shot_code if shot_code else f"Shot {shot_id}"
            subtitle = shot_status

            choice = {
                "name": display_name,
                "icon": thumbnail_url,
                "subtitle": subtitle,
                "args": {
                    "shot_id": shot_id,
                    "shot_data": shot_data,
                },
            }
            choices_args.append(choice)
            choices_names.append(display_name)

        return shot_list, choices_names

    def process(self) -> None:
        """Process the node - automatically load shots when run."""
        try:
            current_selection = self.get_parameter_value("selected_shot")

            project_id = self.get_parameter_value("project_id")
            if not project_id:
                logger.warning(f"{self.name}: project_id is required")
                self._update_option_choices("selected_shot", ["No project selected"], "No project selected")
                return

            logger.info(f"{self.name}: Loading shots from ShotGrid for project {project_id}...")
            shots = self._fetch_shots_from_api()

            if not shots:
                logger.warning(f"{self.name}: No shots found for project {project_id}")
                self._update_option_choices("selected_shot", ["No shots available"], "No shots available")
                return

            shot_list, choices_names = self._process_shots_to_choices(shots)

            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_shots", value=shot_list, node_name=self.name)
            )
            self.parameter_output_values["all_shots"] = shot_list
            self.publish_update_to_parameter("all_shots", shot_list)

            selected_value = choices_names[0] if choices_names else "No shots available"
            selected_index = 0

            if (
                current_selection
                and current_selection != "Load shots to see options"
                and current_selection in choices_names
            ):
                selected_index = choices_names.index(current_selection)
                selected_value = current_selection
                logger.info(f"{self.name}: Preserved selection: {current_selection}")
            else:
                selected_value = choices_names[0]
                selected_index = 0
                logger.info(f"{self.name}: Selected first shot: {choices_names[0]}")

            logger.info(f"{self.name}: Updating dropdown with {len(choices_names)} choices: {choices_names[:3]}...")
            self._update_option_choices("selected_shot", choices_names, selected_value)
            logger.info(f"{self.name}: Dropdown updated, selected_value: {selected_value}")

            self._update_selected_shot_data(shots[selected_index] if selected_index < len(shots) else {})

            logger.info(f"{self.name}: Successfully loaded {len(shot_list)} shots")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load shots: {e}")
            self._update_option_choices("selected_shot", ["Error loading shots"], "Error loading shots")







