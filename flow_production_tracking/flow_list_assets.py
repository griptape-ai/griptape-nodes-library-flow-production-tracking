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
            Parameter(
                name="selected_asset",
                type="string",
                default_value="Load assets to see options",
                tooltip="Select an asset from the list. Use refresh button to update selected asset data.",
                allowed_modes={ParameterMode.PROPERTY},
                traits={
                    Options(choices=ASSET_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_asset,
                        label="Refresh Selected",
                        full_width=True,
                    ),
                },
            )
        )
        self.add_parameter(
            ParameterImage(
                name="asset_image",
                default_value="",
                tooltip="Image/thumbnail of the selected asset",
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
            if value and value != "Load assets to see options":
                # Find the index of the selected asset by matching display names
                assets = self.get_parameter_value("all_assets") or []
                selected_index = 0

                # Clean the selection to match against asset names/codes
                clean_selection = value.replace("📋 ", "").replace(" (Template)", "")

                for i, asset in enumerate(assets):
                    asset_name = asset.get("name", "")
                    asset_code = asset.get("code", "")
                    if asset_name == clean_selection or asset_code == clean_selection:
                        selected_index = i
                        break

                self._update_selected_asset_data(assets[selected_index] if selected_index < len(assets) else {})
        return super().after_value_set(parameter, value)

    def _update_selected_asset_data(self, asset_data: dict) -> None:
        """Update asset outputs based on selected asset data."""
        if not asset_data:
            return

        # Extract basic asset info (from processed data structure)
        asset_id = asset_data.get("id", "")
        asset_name = asset_data.get("name", f"Asset {asset_id}")
        asset_code = asset_data.get("code", "")
        # Try multiple description fields
        asset_description = asset_data.get("description") or asset_data.get("sg_description") or ""
        asset_image = asset_data.get("sg_thumbnail") or asset_data.get("image", "")

        # Generate web UI URL
        try:
            shotgrid_config = self._get_shotgrid_config()
            base_url = shotgrid_config.get("base_url", "https://shotgrid.autodesk.com/")
            asset_url = f"{base_url.rstrip('/')}/detail/Asset/{asset_id}"
        except Exception:
            asset_url = f"https://shotgrid.autodesk.com/detail/Asset/{asset_id}"

        # Update all asset parameters using SetParameterValueRequest
        params = {
            "asset_id": asset_id,
            "asset_data": asset_data,
            "asset_url": asset_url,
            "asset_description": asset_description,
            "asset_image": asset_image,
        }

        for param_name, value in params.items():
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
            )
            self.parameter_output_values[param_name] = value
            self.publish_update_to_parameter(param_name, value)

    def _refresh_selected_asset(
        self, button: Button, button_details: ButtonDetailsMessagePayload
    ) -> NodeMessageResult | None:
        """Refresh the selected asset when the refresh button is clicked."""
        try:
            current_selection = self.get_parameter_value("selected_asset")
            if not current_selection or current_selection == "Load assets to see options":
                logger.warning(f"{self.name}: No asset selected to refresh")
                return None

            # Clean the selection to get the actual asset name/code
            clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")

            # Get the current asset ID from all_assets
            assets = self.get_parameter_value("all_assets") or []
            selected_asset_id = None
            selected_index = 0

            for i, asset in enumerate(assets):
                asset_name = asset.get("name", "")
                asset_code = asset.get("code", "")
                if asset_name == clean_selection or asset_code == clean_selection:
                    selected_asset_id = asset.get("id")
                    selected_index = i
                    break

            if not selected_asset_id:
                logger.warning(f"{self.name}: Could not find asset ID for '{clean_selection}'")
                return None

            # Fetch fresh data for this specific asset
            logger.info(f"{self.name}: Refreshing asset {selected_asset_id} ({clean_selection})")
            fresh_asset_data = self._fetch_single_asset(selected_asset_id)

            if not fresh_asset_data:
                logger.warning(f"{self.name}: Failed to fetch fresh data for asset {selected_asset_id}")
                return None

            # Update the asset in all_assets using SetParameterValueRequest
            assets[selected_index] = fresh_asset_data
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_assets", value=assets, node_name=self.name)
            )
            self.parameter_output_values["all_assets"] = assets
            self.publish_update_to_parameter("all_assets", assets)

            # Update the asset data display
            self._update_selected_asset_data(fresh_asset_data)

            logger.info(f"{self.name}: Successfully refreshed asset {selected_asset_id}")

        except Exception as e:
            logger.error(f"{self.name}: Failed to refresh selected asset: {e}")
        return None

    def _fetch_single_asset(self, asset_id: int) -> dict | None:
        """Fetch a single asset from ShotGrid API."""
        try:
            access_token = self._get_access_token()
            base_url = self._get_shotgrid_config()["base_url"]
            url = f"{base_url}api/v1/entity/assets/{asset_id}"

            params = {
                "fields": "id,code,name,sg_asset_type,sg_status_list,image,sg_thumbnail,project,links,description,sg_description"
            }
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                asset_data = data.get("data")

                if asset_data:
                    # Add URL field for consistency
                    asset_data["url"] = f"{base_url}detail/Asset/{asset_id}"

                    # Process the asset data
                    attributes = asset_data.get("attributes", {})
                    asset_data.update(attributes)

                    return asset_data

                return None

        except Exception as e:
            logger.error(f"{self.name}: Failed to fetch asset {asset_id}: {e}")
            return None

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
        params = {
            "fields": "id,code,name,sg_asset_type,sg_status_list,image,sg_thumbnail,project,links,description,sg_description"
        }

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
                "description": asset.get("attributes", {}).get("description"),
                "sg_description": asset.get("attributes", {}).get("sg_description"),
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

        return asset_list, choices_names

    def process(self) -> None:
        """Process the node - automatically load assets when run."""
        try:
            # Get current selection to preserve it
            current_selection = self.get_parameter_value("selected_asset")

            # Get input parameters
            project_id = self.get_parameter_value("project_id")
            if not project_id:
                logger.warning(f"{self.name}: project_id is required")
                self._update_option_choices("selected_asset", ["No project selected"], "No project selected")
                return

            # Load assets from ShotGrid
            logger.info(f"{self.name}: Loading assets from ShotGrid for project {project_id}...")
            assets = self._fetch_assets_from_api()

            if not assets:
                logger.warning(f"{self.name}: No assets found for project {project_id}")
                self._update_option_choices("selected_asset", ["No assets available"], "No assets available")
                return

            # Process assets to choices
            asset_list, choices_names = self._process_assets_to_choices(assets)

            # Store all assets data first using SetParameterValueRequest
            GriptapeNodes.handle_request(
                SetParameterValueRequest(parameter_name="all_assets", value=asset_list, node_name=self.name)
            )
            self.parameter_output_values["all_assets"] = asset_list
            self.publish_update_to_parameter("all_assets", asset_list)

            # Determine what to select
            selected_value = choices_names[0] if choices_names else "No assets available"
            selected_index = 0

            # Try to preserve the current selection
            if (
                current_selection
                and current_selection != "Load assets to see options"
                and current_selection in choices_names
            ):
                selected_index = choices_names.index(current_selection)
                selected_value = current_selection
                logger.info(f"{self.name}: Preserved selection: {current_selection}")
            else:
                selected_value = choices_names[0]
                selected_index = 0
                logger.info(f"{self.name}: Selected first asset: {choices_names[0]}")

            # Update the dropdown choices
            logger.info(f"{self.name}: Updating dropdown with {len(choices_names)} choices: {choices_names[:3]}...")
            self._update_option_choices("selected_asset", choices_names, selected_value)
            logger.info(f"{self.name}: Dropdown updated, selected_value: {selected_value}")

            # Update the selected asset data
            self._update_selected_asset_data(assets[selected_index] if selected_index < len(assets) else {})

            logger.info(f"{self.name}: Successfully loaded {len(asset_list)} assets")

        except Exception as e:
            logger.error(f"{self.name}: Failed to load assets: {e}")
            self._update_option_choices("selected_asset", ["Error loading assets"], "Error loading assets")
