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
            assets_url = base_url.rstrip("/")
        except Exception:
            # Fallback to generic URL if config is not available
            assets_url = "https://shotgrid.autodesk.com/assets"

        self.add_parameter(
            ParameterString(
                name="project_id",
                default_value=None,
                tooltip="The ID of the project to list assets for.",
                placeholder_text="ID of the selected project",
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_type",
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
                    ),
                    Button(
                        label="Load Assets",
                        icon="list-restart",
                        size="icon",
                        variant="secondary",
                        full_width=True,
                        on_click=self._reload_assets,
                    ),
                },
            )
        )
        self.add_parameter(
            Parameter(
                name="all_assets",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The list of assets",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )
        self.add_parameter(
            ParameterString(
                name="selected_asset",
                default_value="No assets available",
                tooltip="Select an asset from the list.",
                allow_input=False,
                allow_property=True,
                ui_options={
                    "display_name": "Select Asset",
                    "data": ASSET_CHOICES_ARGS,
                    "icon_size": "medium",
                },
                traits={
                    Options(choices=ASSET_CHOICES),
                },
            )
        )
        self.add_parameter(
            ParameterImage(
                name="asset_icon",
                default_value="",
                tooltip="Icon/thumbnail of the selected asset",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_description",
                default_value="",
                tooltip="Description of the selected asset",
                allowed_modes={ParameterMode.OUTPUT},
                multiline=True,
            )
        )
        self.add_parameter(
            ParameterString(
                name="asset_url",
                default_value="",
                tooltip="URL of the selected asset in ShotGrid",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_id",
                type="str",
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="ID of the selected asset",
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_data",
                type="json",
                default_value={},
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Complete data for the selected asset",
                ui_options={"hide_property": True},
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "selected_asset":
            self.publish_update_to_parameter("selected_asset", value)
            if value and value != "No assets available":
                # Find the index of the selected asset
                assets = self.get_parameter_value("all_assets") or []
                print(f"assets: {assets}")
                print(f"value: {value}")
                selected_index = next(
                    (
                        i
                        for i, asset in enumerate(assets)
                        if asset.get("attributes", {}).get("name") == value
                        or asset.get("attributes", {}).get("code") == value
                    ),
                    0,
                )
                print(selected_index)
                self._update_selected_asset_data(assets[selected_index] if selected_index < len(assets) else {})
        return super().after_value_set(parameter, value)

    def _update_selected_asset_data(self, asset_data: dict) -> None:
        """Update asset outputs based on selected asset data."""
        if not asset_data:
            return

        # Set basic asset info
        asset_id = asset_data.get("id", "")
        attributes = asset_data.get("attributes", {})

        self.set_parameter_value("asset_id", asset_id)
        self.parameter_output_values["asset_id"] = asset_id
        self.parameter_output_values["asset_data"] = asset_data
        self.publish_update_to_parameter("asset_id", asset_id)
        self.publish_update_to_parameter("asset_data", asset_data)

        # Set asset URL - construct a generic asset URL that ShotGrid can handle
        # Since we don't have the page ID, we'll use a generic format that ShotGrid can redirect
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            # Use a generic asset URL format that ShotGrid can redirect to the correct page
            asset_url = f"{base_url.rstrip('/')}/detail/Asset/{asset_id}"
        except Exception:
            # Fallback to generic URL if config is not available
            asset_url = f"https://shotgrid.autodesk.com/detail/Asset/{asset_id}"

        self.set_parameter_value("asset_url", asset_url)
        self.parameter_output_values["asset_url"] = asset_url
        self.publish_update_to_parameter("asset_url", asset_url)

        # Set asset description
        asset_description = attributes.get("description", "")
        self.set_parameter_value("asset_description", asset_description)
        self.parameter_output_values["asset_description"] = asset_description
        self.publish_update_to_parameter("asset_description", asset_description)

        # Set asset icon/thumbnail
        asset_icon = attributes.get("sg_thumbnail") or attributes.get("image", "")
        self.set_parameter_value("asset_icon", asset_icon)
        self.parameter_output_values["asset_icon"] = asset_icon
        self.publish_update_to_parameter("asset_icon", asset_icon)

    def _update_asset_types(self) -> None:
        """Update asset_type parameter choices with standard ShotGrid asset types."""
        # Standard ShotGrid asset types
        standard_asset_types = [
            "All Types",
            "Character",
            "Prop",
            "Environment",
            "Vehicle",
            "Weapon",
            "Accessory",
            "Set",
            "Background",
            "Foreground",
            "Matte Painting",
            "Lighting",
            "Camera",
            "Rig",
            "Animation",
            "FX",
            "Sound",
            "Music",
            "Voice",
            "Other",
        ]

        # Update the asset_type parameter choices
        asset_type_param = next((p for p in self.parameters if p.name == "asset_type"), None)
        if asset_type_param:
            options_trait = asset_type_param.find_elements_by_type(Options)
            if options_trait:
                options_trait[0].choices = standard_asset_types

    def _reload_assets(
        self,
        button: Button | None = None,
        button_details: ButtonDetailsMessagePayload | None = None,
        preserve_selection: bool = True,
    ) -> NodeMessageResult | None:
        """Reload assets when the reload button is clicked."""
        try:
            # Step 1: Get all assets from API (without filtering by asset type)
            all_assets = self._fetch_all_assets_from_api()

            # Step 2: Update asset types with standard ShotGrid types
            self._update_asset_types()

            # Step 3: Get filtered assets based on current asset type selection
            assets = self._fetch_assets_from_api()

            # Step 4: Process assets into choices
            choices_args, choices_names = self._process_assets_to_choices(assets)

            # Step 5: Update global variables
            self.set_parameter_value("all_assets", all_assets)
            self._update_global_choices(choices_args, choices_names)

            # Step 6: Update parameter choices
            self._update_parameter_choices(choices_args, choices_names)

            # Step 7: Update parameter choices and preserve current selection
            current_selection = self.get_parameter_value("selected_asset")
            selected_id = 0  # Default to first asset
            selected_value = choices_names[0] if choices_names else "No assets available"

            # Try to preserve the current selection by matching asset names
            if preserve_selection and current_selection and current_selection != "No assets available":
                # Find the selected asset in the raw data by name
                for i, asset in enumerate(assets):
                    asset_name = asset.get("name", "")
                    asset_code = asset.get("code", "")
                    # Try to match by name or code
                    if asset_name == current_selection or asset_code == current_selection:
                        selected_id = i
                        selected_value = choices_names[i]
                        break

            self._update_option_choices("selected_asset", choices_names, selected_value)

            # Update the selected asset data outputs
            if assets and selected_id < len(assets):
                self._update_selected_asset_data(assets[selected_id])
            else:
                self._update_selected_asset_data({})

        except Exception as e:
            logger.error(f"Failed to reload assets: {e}")
        return None

    def _fetch_all_assets_from_api(self) -> list[dict]:
        """Fetch all assets from ShotGrid API without filtering by asset type."""
        # Get input parameters
        project_id = self.get_parameter_value("project_id")
        if not project_id:
            return []

        # Get access token
        access_token = self._get_access_token()

        # Make request to get assets
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        # Get base URL
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/assets"

        # Add fields to get asset information
        params = {
            "filter[project.Project.id]": project_id,
            "fields": "id,code,name,sg_asset_type,sg_status_list,image,sg_thumbnail,project,links,description",
        }

        response = httpx.get(url, headers=headers, params=params, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

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
        params = {"fields": "id,code,name,sg_asset_type,sg_status_list,image,sg_thumbnail,project,links,description"}

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
        self.parameter_output_values["all_assets"] = asset_list
        project_id = self.get_parameter_value("project_id")

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

            # Try to find the current selection in the new choices
            selected_value = None
            if current_selection and current_selection in choices_names:
                # Exact match found
                selected_value = current_selection
            else:
                # Try to find by asset ID if we have asset data
                if current_selection and current_selection != "No assets available":
                    # Look for a choice that might match the current selection
                    # This is a fallback for when the display name changes but the asset is the same
                    for i, choice_name in enumerate(choices_names):
                        if (choice_name and current_selection in choice_name) or choice_name in current_selection:
                            selected_value = choice_name
                            break

                if not selected_value:
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

                # Set parameter value without emitting change events to avoid loops
                self.set_parameter_value("selected_asset", selected_value, emit_change=False)
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
