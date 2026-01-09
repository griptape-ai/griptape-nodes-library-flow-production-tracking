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
EPISODE_CHOICES = ["No episodes available"]
EPISODE_CHOICES_ARGS = []


class FlowListEpisodes(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Get the user's ShotGrid URL for the link
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            # Remove trailing slash and add episodes path
            episodes_url = base_url.rstrip("/")
        except Exception:
            # Fallback to generic URL if config is not available
            episodes_url = "https://shotgrid.autodesk.com/episodes"

        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to list episodes for.",
                placeholder_text="ID of the selected project",
            )
        )
        self.add_parameter(
            Parameter(
                name="all_episodes",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of episodes",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            Parameter(
                name="selected_episode",
                type="string",
                default_value="Load episodes to see options",
                tooltip="Select an episode from the list. Use refresh button to update selected episode data.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=EPISODE_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_episode,
                        label="Refresh Selected",
                        full_width=True,
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterImage(
                name="episode_image",
                default_value="",
                tooltip="Image/thumbnail of the selected episode",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_description",
                default_value="",
                tooltip="Description of the selected episode",
                allowed_modes={ParameterMode.OUTPUT},
                multiline=True,
            )
        )
        self.add_parameter(
            ParameterString(
                name="episode_url",
                default_value="",
                tooltip="URL of the selected episode in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="episode_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected episode",
            )
        )
        self.add_parameter(
            Parameter(
                name="episode_code",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Code of the selected episode",
            )
        )
        self.add_parameter(
            Parameter(
                name="episode_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected episode",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_episode":
            self.publish_update_to_parameter("selected_episode", value)
            if value and value != "Load episodes to see options":
                # Find the index of the selected episode by matching display names
                episodes = self.get_parameter_value("all_episodes") or []
                selected_index = 0

                # Clean the selection to match against episode names/codes
                clean_selection = value.replace("📋 ", "").replace(" (Template)", "")

                for i, episode in enumerate(episodes):
                    episode_name = episode.get("name", "")
                    episode_code = episode.get("code", "")
                    if episode_name == clean_selection or episode_code == clean_selection:
                        selected_index = i
                        break

                self._update_selected_episode_data(episodes[selected_index] if selected_index < len(episodes) else {})
        return super().after_value_set(parameter, value)

    def _update_selected_episode_data(self, episode_data: dict) -> None:
        """Update episode outputs based on selected episode data."""
        if not episode_data:
            return

        # Extract basic episode info (from processed data structure)
        episode_id = episode_data.get("id", "")
        episode_name = episode_data.get("name", f"Episode {episode_id}")
        episode_code = episode_data.get("code", "")
        # Try multiple description fields
        episode_description = episode_data.get("description") or episode_data.get("sg_description") or ""
        episode_image = episode_data.get("sg_thumbnail") or episode_data.get("image", "")

        # Generate web UI URL
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            episode_url = f"{base_url.rstrip('/')}/detail/Episode/{episode_id}"
        except Exception:
            episode_url = f"https://shotgrid.autodesk.com/detail/Episode/{episode_id}"

        # Update all episode parameters using SetParameterValueRequest
        params = {
            "episode_id": episode_id,
            "episode_code": episode_code,
            "episode_data": episode_data,
            "episode_url": episode_url,
            "episode_description": episode_description,
            "episode_image": episode_image,
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def _refresh_selected_episode(
        self, button: Button, button_details: ButtonDetailsMessagePayload
    ) -> NodeMessageResult | None:
        """Refresh the selected episode when the refresh button is clicked."""
        try:
            current_selection = self.get_parameter_value("selected_episode")
            if not current_selection or current_selection == "Load episodes to see options":
                logger.warning(f"{self.name}: No episode selected to refresh")
                return None

            # Clean the selection to get the actual episode name/code
            clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")

            # Get the current episode ID from all_episodes
            episodes = self.get_parameter_value("all_episodes") or []
            selected_episode_id = None
            selected_index = 0

            for i, episode in enumerate(episodes):
                episode_name = episode.get("name", "")
                episode_code = episode.get("code", "")
                if episode_name == clean_selection or episode_code == clean_selection:
                    selected_episode_id = episode.get("id")
                    selected_index = i
                    break

            if not selected_episode_id:
                logger.warning(f"{self.name}: Could not find episode ID for '{clean_selection}'")
                return None

            # Fetch fresh data for this specific episode
            logger.info(f"{self.name}: Refreshing episode {selected_episode_id} ({clean_selection})")
            fresh_episode_data = self._fetch_single_episode(selected_episode_id)

            if not fresh_episode_data:
                logger.warning(f"{self.name}: Failed to fetch fresh data for episode {selected_episode_id}")
                return None

            # Update the episode in all_episodes using SetParameterValueRequest
            episodes[selected_index] = fresh_episode_data
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_episodes", value=episodes, node_name=self.name)
            )
            self.parameter_output_values["all_episodes"] = episodes
            self.publish_update_to_parameter("all_episodes", episodes)

            # Update the episode data display
            self._update_selected_episode_data(fresh_episode_data)

            logger.info(f"{self.name}: Successfully refreshed episode {selected_episode_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected episode: {e}")
        return None

    def _fetch_single_episode(self, episode_id: int) -> dict | None:
        """Fetch a single episode from ShotGrid API."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/episodes/{episode_id}"

            params = {
                "fields": "id,code,name,sg_status_list,image,sg_thumbnail,project,links,description,sg_description"
            }
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                episode_data = data.get("data")

                if episode_data:
                    # Add URL field for consistency
                    episode_data["url"] = f"{base_url}detail/Episode/{episode_id}"

                    # Process the episode data
                    attributes = episode_data.get("attributes", {})
                    episode_data.update(attributes)

                    return episode_data

                return None

        except Exception as e:
            logger.error(f"{self.name}: Failed to fetch episode {episode_id}: {e}")
            return None

    def _fetch_episodes_from_api(self) -> list[dict]:
        """Fetch episodes from ShotGrid API."""
        # Get input parameters
        project_id = self.get_parameter_value("project_id")

        if not project_id:
            msg = "project_id is required"
            raise ValueError(msg)

        # Convert project_id to integer if it's a string
        try:
            project_id = int(project_id)
        except (ValueError, TypeError) as e:
            msg = "project_id must be a valid integer"
            raise ValueError(msg) from e

        # Get access token
        access_token = self._get_access_token()

        # Make request to get episodes
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        # Get base URL
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/episodes"

        # Add fields to get thumbnail URLs
        params = {
            "fields": "id,code,name,sg_status_list,image,sg_thumbnail,project,links,description,sg_description"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            all_episodes = data.get("data", [])

            # Filter episodes by project
            episodes = []
            for episode in all_episodes:
                # Check if episode belongs to the specified project
                episode_project = episode.get("relationships", {}).get("project", {}).get("data", {})
                episode_project_id = episode_project.get("id")

                if episode_project_id != project_id:
                    continue

                episodes.append(episode)

            return episodes

    def _process_episodes_to_choices(self, episodes: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw episodes data into choices format."""
        episode_list = []
        choices_args = []
        choices_names = []

        for episode in episodes:
            episode_data = {
                "id": episode.get("id"),
                "code": episode.get("attributes", {}).get("code"),
                "name": episode.get("attributes", {}).get("name"),
                "sg_status_list": episode.get("attributes", {}).get("sg_status_list"),
                "image": episode.get("attributes", {}).get("image"),
                "sg_thumbnail": episode.get("attributes", {}).get("sg_thumbnail"),
                "description": episode.get("attributes", {}).get("description"),
                "sg_description": episode.get("attributes", {}).get("sg_description"),
                "project": episode.get("relationships", {}).get("project", {}).get("data", {}).get("id"),
            }
            episode_list.append(episode_data)

            # Create choice for the dropdown
            episode_id = episode_data["id"]
            episode_code = episode_data["code"] or ""
            episode_status = episode_data["sg_status_list"] or "Unknown"

            # Get thumbnail URL
            thumbnail_url = episode_data.get("sg_thumbnail") or episode_data.get("image") or ""

            # Create display name with episode code as main text and status as subtitle
            display_name = episode_code if episode_code else f"Episode {episode_id}"
            subtitle = episode_status

            choice = {
                "name": display_name,
                "icon": thumbnail_url,
                "subtitle": subtitle,
                "args": {
                    "episode_id": episode_id,
                    "episode_data": episode_data,
                },
            }
            choices_args.append(choice)
            choices_names.append(display_name)

        return episode_list, choices_names

    def process(self) -> None:
        """Process the node - automatically load episodes when run."""
        try:
            # Get current selection to preserve it
            current_selection = self.get_parameter_value("selected_episode")

            # Get input parameters
            project_id = self.get_parameter_value("project_id")
            if not project_id:
                logger.warning(f"{self.name}: project_id is required")
                self._update_option_choices("selected_episode", ["No project selected"], "No project selected")
                return

            # Load episodes from ShotGrid
            logger.info(f"{self.name}: Loading episodes from ShotGrid for project {project_id}...")
            episodes = self._fetch_episodes_from_api()

            if not episodes:
                logger.warning(f"{self.name}: No episodes found for project {project_id}")
                self._update_option_choices("selected_episode", ["No episodes available"], "No episodes available")
                return

            # Process episodes to choices
            episode_list, choices_names = self._process_episodes_to_choices(episodes)

            # Store all episodes data first using SetParameterValueRequest
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_episodes", value=episode_list, node_name=self.name)
            )
            self.parameter_output_values["all_episodes"] = episode_list
            self.publish_update_to_parameter("all_episodes", episode_list)

            # Determine what to select
            selected_value = choices_names[0] if choices_names else "No episodes available"
            selected_index = 0

            # Try to preserve the current selection
            if (
                current_selection
                and current_selection != "Load episodes to see options"
                and current_selection in choices_names
            ):
                selected_index = choices_names.index(current_selection)
                selected_value = current_selection
                logger.info(f"{self.name}: Preserved selection: {current_selection}")
            else:
                selected_value = choices_names[0]
                selected_index = 0
                logger.info(f"{self.name}: Selected first episode: {choices_names[0]}")

            # Update the dropdown choices
            logger.info(f"{self.name}: Updating dropdown with {len(choices_names)} choices: {choices_names[:3]}...")
            self._update_option_choices("selected_episode", choices_names, selected_value)
            logger.info(f"{self.name}: Dropdown updated, selected_value: {selected_value}")

            # Update the selected episode data
            self._update_selected_episode_data(episodes[selected_index] if selected_index < len(episodes) else {})

            logger.info(f"{self.name}: Successfully loaded {len(episode_list)} episodes")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load episodes: {e}")
            self._update_option_choices("selected_episode", ["Error loading episodes"], "Error loading episodes")







