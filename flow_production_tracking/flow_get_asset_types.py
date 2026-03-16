import httpx
from base_shotgrid_node import BaseShotGridNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.retained_mode.griptape_nodes import logger


class FlowGetAssetTypes(BaseShotGridNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_parameter(
            Parameter(
                name="project_id",
                type="string",
                default_value=None,
                tooltip="The ID of the project to get asset types for.",
            )
        )
        self.add_parameter(
            Parameter(
                name="asset_types",
                output_type="json",
                type="json",
                default_value=None,
                tooltip="The available asset types for the project.",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"hide_property": True},
            )
        )

    def process(self) -> None:
        try:
            # Get input parameters
            project_id = self.get_parameter_value("project_id")

            if not project_id:
                logger.error(f"{self.name}: project_id is required")
                return

            # Convert project_id to integer if it's a string
            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                logger.error(f"{self.name}: project_id must be a valid integer")
                return

            # Get access token
            access_token = self._get_access_token()

            # Make request to get asset types for the project
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Get base URL
            base_url = self._get_shotgrid_config()["base_url"]

            # Try to get asset types from project preferences or schema
            # First, let's try to get the project's asset types from the schema
            url = f"{base_url}api/v1/schema/Asset"
            params = {"project_id": project_id}

            logger.info(f"{self.name}: Getting asset types for project {project_id}")

            with httpx.Client() as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                asset_schema = data.get("data", {})

                # Extract asset types from the schema
                asset_types = []

                # Look for asset type fields in the schema
                if "properties" in asset_schema:
                    properties = asset_schema["properties"]

                    # Check for sg_asset_type field which typically contains asset types
                    if "sg_asset_type" in properties:
                        sg_asset_type_field = properties["sg_asset_type"]
                        if "properties" in sg_asset_type_field and "properties" in sg_asset_type_field["properties"]:
                            # This might contain the allowed values
                            allowed_values = sg_asset_type_field.get("properties", {}).get("properties", {})
                            for value_key, value_info in allowed_values.items():
                                asset_types.append(
                                    {
                                        "value": value_key,
                                        "display_name": value_info.get("title", value_key),
                                        "description": value_info.get("description", ""),
                                    }
                                )

                # If we didn't find asset types in the schema, try a different approach
                if not asset_types:
                    # Try to get asset types from project preferences
                    try:
                        prefs_url = f"{base_url}api/v1/preferences"
                        prefs_params = {"project_id": project_id}

                        prefs_response = client.get(prefs_url, headers=headers, params=prefs_params)
                        if prefs_response.status_code == 200:
                            prefs_data = prefs_response.json()
                            # Look for asset type preferences
                            if "asset_types" in prefs_data:
                                asset_types = prefs_data["asset_types"]
                    except Exception as e:
                        logger.warning(f"{self.name}: Could not get asset types from preferences: {e}")

                # If still no asset types, provide some common defaults
                if not asset_types:
                    logger.info(f"{self.name}: No specific asset types found, using common defaults")
                    asset_types = [
                        {"value": "Character", "display_name": "Character", "description": "Character assets"},
                        {"value": "Prop", "display_name": "Prop", "description": "Prop assets"},
                        {"value": "Environment", "display_name": "Environment", "description": "Environment assets"},
                        {"value": "Vehicle", "display_name": "Vehicle", "description": "Vehicle assets"},
                        {"value": "FX", "display_name": "FX", "description": "FX assets"},
                        {"value": "Camera", "display_name": "Camera", "description": "Camera assets"},
                        {"value": "Light", "display_name": "Light", "description": "Light assets"},
                        {"value": "Audio", "display_name": "Audio", "description": "Audio assets"},
                    ]

                # Output the asset types
                self.parameter_output_values["asset_types"] = asset_types
                logger.info(f"{self.name}: Found {len(asset_types)} asset types for project {project_id}")

        except Exception as e:
            logger.error(f"{self.name} encountered an error: {e!s}")
