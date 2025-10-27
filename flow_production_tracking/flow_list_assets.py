from typing import Any

import httpx
from base_shotgrid_node import BaseShotGridNode

from griptape_nodes.exe_types.core_types import (
    NodeMessageResult,
    Parameter,
    ParameterGroup,
    ParameterMessage,
    ParameterMode,
)
from griptape_nodes.retained_mode.griptape_nodes import logger
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload
from griptape_nodes.traits.options import Options

# Default choices - will be populated dynamically
ASSET_CHOICES = ["No assets available"]
ASSET_CHOICES_ARGS = []


class FlowListAssets(BaseShotGridNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Get the user's ShotGrid URL for the link
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            # Remove trailing slash and add assets path
            assets_url = base_url.rstrip("/") + "/assets"
        except Exception:
            # Fallback to generic URL if config is not available
            assets_url = "https://shotgrid.autodesk.com/assets"

        self.add_node_element(
            ParameterMessage(
                name="message",
                variant="none",
                value="Go to your shotgrid assets",
                button_link=assets_url,
                button_text="Go to ShotGrid Assets",
            )
        )
        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to list assets for.",
            )
        )
        with ParameterGroup(name="Filter Options", ui_options={"collapsed": True}) as options_group:
            Parameter(
                name="asset_type",
                type="string",
                default_value="All Types",
                tooltip="Filter assets by type (optional).",
                traits={
                    Options(
                        choices=[
                            "All Types",
                            "Character",
                            "Prop",
                            "Environment",
                            "Vehicle",
                            "FX",
                            "Camera",
                            "Light",
                            "Audio",
                        ]
                    )
                },
            )
        self.add_node_element(options_group)
        self.add_parameter(
            Parameter(
                name="selected_asset",
                type="string",
                default_value="No assets available",
                tooltip="Select an asset from the list.",
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={
                    "display_name": "Select Asset",
                    "data": ASSET_CHOICES_ARGS,
                    "icon_size": "medium",
                },
                traits={
                    Options(choices=ASSET_CHOICES),
                    Button(
                        icon="list-restart",
                        size="icon",
                        variant="secondary",
                        on_click=self._reload_assets,
                    ),
                },
            )
        )
        with ParameterGroup(name="Selected Asset") as selected_asset_group:
            Parameter(
                name="selected_asset_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected asset",
            )
            Parameter(
                name="selected_asset_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected asset",
                ui_options={"hide_property": True},
            )
            Parameter(
                name="assets",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of assets",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        self.add_node_element(selected_asset_group)

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_asset" and value and value != "No assets available":
            # Find the selected choice and update outputs
            # Get the choices for the parameter
            options_trait = parameter.find_elements_by_type(Options)
            if options_trait:
                data_list = parameter.ui_options.get("data", [])
                for idx, choice in enumerate(options_trait[0].choices):
                    if choice == value:
                        # Check bounds to prevent index out of range error
                        if idx < len(data_list):
                            data_item = data_list[idx]
                            args = data_item.get("args", {})
                            if isinstance(args, dict):
                                self.set_parameter_value("selected_asset_id", args.get("asset_id"))
                                self.parameter_output_values["selected_asset_id"] = args.get("asset_id")
                                self.parameter_output_values["selected_asset_data"] = args.get("asset_data")
                                self.publish_update_to_parameter("selected_asset_id", args.get("asset_id"))
                                self.publish_update_to_parameter("selected_asset_data", args.get("asset_data"))
                        break
        return super().after_value_set(parameter, value)

    def _reload_assets(self, button: Button, button_details: ButtonDetailsMessagePayload) -> NodeMessageResult | None:  # noqa: ARG002
        """Reload assets when the reload button is clicked."""
        try:
            # Step 1: Get assets from API
            assets = self._fetch_assets_from_api()

            # Step 2: Process assets into choices
            choices_args, choices_names = self._process_assets_to_choices(assets)

            # Step 3: Update global variables
            self._update_global_choices(choices_args, choices_names)

            # Step 4: Update parameter choices
            self._update_parameter_choices(choices_args, choices_names)

            # Step 5: Trigger UI refresh
            if choices_names and len(choices_names) > 0:
                current_selection = self.get_parameter_value("selected_asset")
                if current_selection and current_selection in choices_names:
                    selected_value = current_selection
                else:
                    selected_value = choices_names[0]
                self.publish_update_to_parameter("selected_asset", selected_value)
                self.set_parameter_value("selected_asset", selected_value, emit_change=True)

        except Exception as e:
            logger.error(f"Failed to reload assets: {e}")
        return None

    def _fetch_assets_from_api(self) -> list[dict]:
        """Fetch assets from ShotGrid API."""
        # Get input parameters
        project_id = self.get_parameter_value("project_id")
        asset_type = self.get_parameter_value("asset_type")

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

        # Make request to get assets
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        # Get base URL
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/assets"

        # Add fields to get thumbnail URLs - no complex filters, we'll filter in code
        params = {"fields": "id,code,name,sg_asset_type,sg_status_list,image,sg_thumbnail,project"}

        logger.info(f"{self.name}: Getting assets for project {project_id}")

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            all_assets = data.get("data", [])

            # Filter assets by project and optionally by asset type
            assets = []
            for asset in all_assets:
                # Check if asset belongs to the specified project
                asset_project = asset.get("relationships", {}).get("project", {}).get("data", {})
                asset_project_id = asset_project.get("id")

                if asset_project_id != project_id:
                    continue

                # Check asset type filter if specified
                if asset_type and asset_type != "All Types":
                    asset_type_value = asset.get("attributes", {}).get("sg_asset_type")
                    if asset_type_value != asset_type:
                        continue

                assets.append(asset)

            return assets

    def _process_assets_to_choices(self, assets: list[dict]) -> tuple[list[dict], list[str]]:
        """Process raw assets data into choices format."""
        asset_list = []
        choices_args = []
        choices_names = []

        for asset in assets:
            asset_data = {
                "id": asset.get("id"),
                "code": asset.get("attributes", {}).get("code"),
                "name": asset.get("attributes", {}).get("name"),
                "sg_asset_type": asset.get("attributes", {}).get("sg_asset_type"),
                "sg_status_list": asset.get("attributes", {}).get("sg_status_list"),
                "image": asset.get("attributes", {}).get("image"),
                "sg_thumbnail": asset.get("attributes", {}).get("sg_thumbnail"),
                "project": asset.get("relationships", {}).get("project", {}).get("data", {}).get("id"),
            }
            asset_list.append(asset_data)

            # Create choice for the dropdown
            asset_id = asset_data["id"]
            asset_code = asset_data["code"] or ""
            asset_type_name = asset_data["sg_asset_type"] or "Unknown"

            # Get thumbnail URL
            thumbnail_url = asset_data.get("sg_thumbnail") or asset_data.get("image") or ""

            # Debug thumbnail URLs
            logger.info(
                f"{self.name}: Asset {asset_id} ({asset_code}) - sg_thumbnail: {asset_data.get('sg_thumbnail')}, image: {asset_data.get('image')}, final_url: {thumbnail_url}"
            )

            # Create display name with asset code as main text and type as subtitle
            display_name = asset_code if asset_code else f"Asset {asset_id}"
            subtitle = asset_type_name

            choice = {
                "name": display_name,
                "icon": thumbnail_url,
                "subtitle": subtitle,
                "args": {
                    "asset_id": asset_id,
                    "asset_data": asset_data,
                },
            }
            choices_args.append(choice)
            choices_names.append(display_name)

        # Output the assets and project_id
        self.parameter_output_values["assets"] = asset_list
        project_id = self.get_parameter_value("project_id")
        logger.info(f"{self.name}: Retrieved {len(asset_list)} assets for project {project_id}")

        return choices_args, choices_names

    def _update_global_choices(self, choices_args: list[dict], choices_names: list[str]) -> None:
        """Update global choice variables."""
        global ASSET_CHOICES_ARGS, ASSET_CHOICES
        ASSET_CHOICES_ARGS = choices_args
        ASSET_CHOICES = choices_names

    def _update_parameter_choices(self, choices_args: list[dict], choices_names: list[str]) -> None:
        """Update the parameter's choices without UI messaging."""
        if choices_names and len(choices_names) > 0:
            # Get the current selected value to preserve it
            current_selection = self.get_parameter_value("selected_asset")

            # If current selection is still valid, keep it; otherwise use first choice
            if current_selection and current_selection in choices_names:
                selected_value = current_selection
            else:
                selected_value = choices_names[0]

            # Use the proper method to update choices (this should persist)
            try:
                # Update choices using the built-in method
                self._update_option_choices("selected_asset", choices_names, selected_value)

                # Update UI options data
                asset_param = self.get_parameter_by_name("selected_asset")
                if asset_param:
                    asset_ui_options = asset_param.ui_options
                    asset_ui_options["data"] = choices_args
                    asset_param.ui_options = asset_ui_options

                # Set parameter value without emitting change events
                self.set_parameter_value("selected_asset", selected_value, emit_change=True)
                self.publish_update_to_parameter("selected_asset", selected_value)
            except Exception as e:
                logger.error(f"Failed to update parameter choices: {e}")
                # Fallback to direct assignment
                self.parameter_values["selected_asset"] = selected_value
        else:
            # Handle no assets case
            try:
                asset_param = self.get_parameter_by_name("selected_asset")
                if asset_param:
                    traits = asset_param.find_elements_by_type(Options)
                    if traits:
                        traits[0].choices = ["No assets available"]
                    asset_param.ui_options["data"] = []

                self.set_parameter_value("selected_asset", "No assets available", emit_change=False)
            except Exception as e:
                logger.error(f"Failed to update parameter choices (no assets): {e}")
                self.parameter_values["selected_asset"] = "No assets available"

    def process(self) -> None:
        """Process the node - assets are only loaded when user clicks the reload button."""

        # Do nothing - assets are only loaded when user clicks the reload button
