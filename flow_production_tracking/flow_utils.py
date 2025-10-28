import httpx

from griptape_nodes.retained_mode.griptape_nodes import logger


class ShotGridAPI:
    """Centralized ShotGrid API operations for reuse across nodes"""

    def __init__(self, access_token: str, base_url: str):
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    def get_projects(self, show_templates: bool = False, show_only_templates: bool = False) -> list[dict]:
        """Get list of projects with optional template filtering"""
        try:
            url = f"{self.base_url}api/v1/entity/projects"
            params = {
                "fields": "id,name,code,description,sg_status_list,image,sg_thumbnail,sg_type,sg_status,template,is_template"
            }

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                projects = data.get("data", [])

                # Filter based on template settings
                filtered_projects = []
                for project in projects:
                    project_data = {
                        "id": project.get("id"),
                        "name": project.get("attributes", {}).get("name"),
                        "code": project.get("attributes", {}).get("code"),
                        "description": project.get("attributes", {}).get("description"),
                        "sg_status_list": project.get("attributes", {}).get("sg_status_list"),
                        "image": project.get("attributes", {}).get("image"),
                        "sg_thumbnail": project.get("attributes", {}).get("sg_thumbnail"),
                        "sg_type": project.get("attributes", {}).get("sg_type"),
                        "sg_status": project.get("attributes", {}).get("sg_status"),
                        "template": project.get("attributes", {}).get("template"),
                        "is_template": project.get("attributes", {}).get("is_template"),
                    }

                    # Determine if this is a template
                    is_template = self._is_project_template(project_data)
                    project_data["is_template"] = is_template

                    # Apply filtering
                    if show_only_templates and not is_template:
                        continue
                    if not show_templates and not show_only_templates and is_template:
                        continue

                    filtered_projects.append(project_data)

                return filtered_projects

        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []

    def get_project_templates(self) -> list[dict]:
        """Get list of project templates"""
        try:
            url = f"{self.base_url}api/v1/entity/projects"
            params = {"fields": "id,name,code,description,template,sg_type,sg_status,is_template"}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                projects = data.get("data", [])

                # Filter for templates only
                templates = []
                logger.info(f"Checking {len(projects)} projects for templates")
                for project in projects:
                    project_data = {
                        "id": project.get("id"),
                        "name": project.get("attributes", {}).get("name"),
                        "code": project.get("attributes", {}).get("code"),
                        "description": project.get("attributes", {}).get("description"),
                        "sg_type": project.get("attributes", {}).get("sg_type"),
                        "sg_status": project.get("attributes", {}).get("sg_status"),
                        "template": project.get("attributes", {}).get("template"),
                        "is_template": project.get("attributes", {}).get("is_template"),
                    }

                    # Check if this is a template
                    is_template = self._is_project_template(project_data)
                    if is_template:
                        logger.info(f"Found template: {project_data.get('name')} (ID: {project_data.get('id')})")
                        templates.append(project)

                logger.info(f"Found {len(templates)} project templates")
                return templates

        except Exception as e:
            logger.error(f"Failed to get project templates: {e}")
            return []

    def get_assets_for_project(
        self, project_id: int, show_templates: bool = False, show_only_templates: bool = False
    ) -> list[dict]:
        """Get list of assets for a specific project with optional template filtering"""
        try:
            url = f"{self.base_url}api/v1/entity/assets"
            params = {
                "project_id": project_id,
                "fields": "id,name,code,description,sg_status_list,image,sg_thumbnail,sg_asset_type,template,is_template",
            }

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                assets = data.get("data", [])

                # Filter based on template settings
                filtered_assets = []
                for asset in assets:
                    asset_data = {
                        "id": asset.get("id"),
                        "name": asset.get("attributes", {}).get("name"),
                        "code": asset.get("attributes", {}).get("code"),
                        "description": asset.get("attributes", {}).get("description"),
                        "sg_status_list": asset.get("attributes", {}).get("sg_status_list"),
                        "image": asset.get("attributes", {}).get("image"),
                        "sg_thumbnail": asset.get("attributes", {}).get("sg_thumbnail"),
                        "sg_asset_type": asset.get("attributes", {}).get("sg_asset_type"),
                        "template": asset.get("attributes", {}).get("template"),
                        "is_template": asset.get("attributes", {}).get("is_template"),
                    }

                    # Determine if this is a template
                    is_template = self._is_asset_template(asset_data)
                    asset_data["is_template"] = is_template

                    # Apply filtering
                    if show_only_templates and not is_template:
                        continue
                    if not show_templates and not show_only_templates and is_template:
                        continue

                    filtered_assets.append(asset_data)

                return filtered_assets

        except Exception as e:
            logger.error(f"Failed to get assets for project {project_id}: {e}")
            return []

    def get_asset_templates(self, project_id: int | None = None, asset_type: str | None = None) -> list[dict]:
        """Get list of asset templates, optionally filtered by project and asset type"""
        try:
            # First, try to get project-specific templates
            project_templates = []
            if project_id:
                url = f"{self.base_url}api/v1/entity/assets"
                params = {
                    "fields": "id,name,code,description,sg_asset_type,template,is_template",
                    "project_id": project_id,
                }

                if asset_type:
                    params["sg_asset_type"] = asset_type

                with httpx.Client() as client:
                    response = client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    assets = data.get("data", [])

                    # Filter for templates only
                    for asset in assets:
                        asset_data = {
                            "id": asset.get("id"),
                            "name": asset.get("attributes", {}).get("name"),
                            "code": asset.get("attributes", {}).get("code"),
                            "description": asset.get("attributes", {}).get("description"),
                            "sg_asset_type": asset.get("attributes", {}).get("sg_asset_type"),
                            "template": asset.get("attributes", {}).get("template"),
                            "is_template": asset.get("attributes", {}).get("is_template"),
                        }

                        # Check if this is a template
                        if self._is_asset_template(asset_data):
                            project_templates.append(asset)

            # If no project-specific templates found, try global templates
            global_templates = []
            if not project_templates:
                url = f"{self.base_url}api/v1/entity/assets"
                params = {"fields": "id,name,code,description,sg_asset_type,template,is_template"}

                if asset_type:
                    params["sg_asset_type"] = asset_type

                with httpx.Client() as client:
                    response = client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    assets = data.get("data", [])

                    # Filter for templates only
                    for asset in assets:
                        asset_data = {
                            "id": asset.get("id"),
                            "name": asset.get("attributes", {}).get("name"),
                            "code": asset.get("attributes", {}).get("code"),
                            "description": asset.get("attributes", {}).get("description"),
                            "sg_asset_type": asset.get("attributes", {}).get("sg_asset_type"),
                            "template": asset.get("attributes", {}).get("template"),
                            "is_template": asset.get("attributes", {}).get("is_template"),
                        }

                        # Check if this is a template
                        if self._is_asset_template(asset_data):
                            global_templates.append(asset)

            # Return project templates if found, otherwise global templates
            if project_templates:
                logger.info(f"Found {len(project_templates)} project-specific asset templates")
                return project_templates
            if global_templates:
                logger.info(f"Found {len(global_templates)} global asset templates")
                return global_templates
            logger.info("No asset templates found (project-specific or global)")
            return []

        except Exception as e:
            logger.error(f"Failed to get asset templates: {e}")
            return []

    def get_asset_types_for_project(self, project_id: int) -> list[str]:
        """Get available asset types for a project"""
        try:
            url = f"{self.base_url}api/v1/schema/Asset"
            params = {"project_id": project_id}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                asset_schema = data.get("data", {})

                # Extract asset types from the schema
                asset_types = []

                if "properties" in asset_schema:
                    properties = asset_schema["properties"]

                    # Check for sg_asset_type field which typically contains asset types
                    if "sg_asset_type" in properties:
                        sg_asset_type_field = properties["sg_asset_type"]
                        if "properties" in sg_asset_type_field and "properties" in sg_asset_type_field["properties"]:
                            # This might contain the allowed values
                            allowed_values = sg_asset_type_field.get("properties", {}).get("properties", {})
                            for value_key, value_info in allowed_values.items():
                                asset_types.append(value_key)

                # If we didn't find asset types in the schema, provide common defaults
                if not asset_types:
                    asset_types = ["Character", "Prop", "Environment", "Vehicle", "FX", "Camera", "Light", "Audio"]

                return asset_types

        except Exception as e:
            logger.error(f"Failed to get asset types for project {project_id}: {e}")
            return ["Character", "Prop", "Environment", "Vehicle", "FX", "Camera", "Light", "Audio"]

    def get_steps(self) -> list[dict]:
        """Get list of available steps"""
        try:
            url = f"{self.base_url}api/v1/entity/steps"
            params = {"fields": "id,code,short_name"}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                steps = data.get("data", [])

                return steps

        except Exception as e:
            logger.error(f"Failed to get steps: {e}")
            return []

    def get_task_types(self) -> list[dict]:
        """Get list of available task types"""
        try:
            url = f"{self.base_url}api/v1/entity/task_types"
            params = {"fields": "id,code,short_name"}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                task_types = data.get("data", [])

                return task_types

        except Exception as e:
            logger.error(f"Failed to get task types: {e}")
            return []

    def get_task_templates(self, entity_type: str = "Asset", asset_type: str | None = None) -> list[dict]:
        """Get list of task templates for a specific entity type, optionally filtered by asset type"""
        try:
            url = f"{self.base_url}api/v1/entity/task_templates"
            params = {
                "fields": "id,name,code,description,entity_type,step,step.Step.code,step.Step.short_name",
                "entity_type": entity_type,
            }

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                task_templates = data.get("data", [])

                # Filter by asset type if specified
                if asset_type:
                    filtered_templates = []
                    for template in task_templates:
                        template_data = {
                            "id": template.get("id"),
                            "name": template.get("attributes", {}).get("name"),
                            "code": template.get("attributes", {}).get("code"),
                            "description": template.get("attributes", {}).get("description"),
                            "entity_type": template.get("attributes", {}).get("entity_type"),
                            "step": template.get("attributes", {}).get("step"),
                        }

                        # Check if this template is relevant for the asset type
                        if self._is_template_relevant_for_asset_type(template_data, asset_type):
                            filtered_templates.append(template)

                    logger.info(
                        f"Found {len(filtered_templates)} task templates for {entity_type} entity type and {asset_type} asset type"
                    )
                    return filtered_templates

                logger.info(f"Found {len(task_templates)} task templates for {entity_type} entity type")
                return task_templates

        except Exception as e:
            logger.error(f"Failed to get task templates for {entity_type}: {e}")
            return []

    def _is_template_relevant_for_asset_type(self, template_data: dict, asset_type: str) -> bool:
        """Check if a task template is relevant for a specific asset type"""
        # Check if the template name, code, or description contains the asset type
        # Handle None values safely
        name = template_data.get("name") or ""
        code = template_data.get("code") or ""
        description = template_data.get("description") or ""

        name_lower = name.lower()
        code_lower = code.lower()
        description_lower = description.lower()
        asset_type_lower = asset_type.lower()

        # Check for exact matches or keyword matches
        if asset_type_lower in name_lower or asset_type_lower in code_lower or asset_type_lower in description_lower:
            return True

        # Check for common asset type variations
        asset_type_variations = {
            "character": ["char", "character", "actor"],
            "prop": ["prop", "object", "item"],
            "environment": ["env", "environment", "set", "location"],
            "vehicle": ["vehicle", "car", "truck", "transport"],
            "fx": ["fx", "effect", "vfx"],
            "camera": ["camera", "cam"],
            "light": ["light", "lighting"],
            "audio": ["audio", "sound", "music"],
        }

        if asset_type_lower in asset_type_variations:
            variations = asset_type_variations[asset_type_lower]
            for variation in variations:
                if variation in name_lower or variation in code_lower or variation in description_lower:
                    return True

        return False

    def create_project(self, project_data: dict) -> dict | None:
        """Create a new project"""
        try:
            url = f"{self.base_url}api/v1/entity/projects"
            headers = {**self.headers, "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=project_data)
                response.raise_for_status()

                data = response.json()
                return data.get("data", {})

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None

    def create_asset(self, asset_data: dict) -> dict | None:
        """Create a new asset"""
        try:
            url = f"{self.base_url}api/v1/entity/assets"
            headers = {**self.headers, "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=asset_data)
                response.raise_for_status()

                data = response.json()
                return data.get("data", {})

        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            return None

    def create_task(self, task_data: dict) -> dict | None:
        """Create a new task"""
        try:
            url = f"{self.base_url}api/v1/entity/tasks"
            headers = {**self.headers, "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=task_data)
                response.raise_for_status()

                data = response.json()
                return data.get("data", {})

        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None

    def get_entity_data(self, entity_type: str, entity_id: int, fields: str = "*") -> dict | None:
        """Get data for a specific entity"""
        try:
            url = f"{self.base_url}api/v1/entity/{entity_type}/{entity_id}"
            params = {"fields": fields}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                return data.get("data", {})

        except Exception as e:
            logger.error(f"Failed to get {entity_type} {entity_id}: {e}")
            return None

    def _is_project_template(self, project_data: dict) -> bool:
        """Determine if a project is a template based on various fields"""
        # Check various fields that might indicate template status
        if project_data.get("template") is True:
            return True
        if project_data.get("is_template") is True:
            return True
        if project_data.get("sg_type") == "Template":
            return True
        if project_data.get("sg_status") == "Template":
            return True

        # Check if name or code contains "template" (case insensitive)
        name = project_data.get("name") or ""
        code = project_data.get("code") or ""
        name_lower = name.lower()
        code_lower = code.lower()
        if "template" in name_lower or "template" in code_lower:
            return True

        return False

    def _is_asset_template(self, asset_data: dict) -> bool:
        """Determine if an asset is a template based on various fields"""
        # Check various fields that might indicate template status
        if asset_data.get("template") is True:
            return True
        if asset_data.get("is_template") is True:
            return True

        # Check if name or code contains "template" (case insensitive)
        name = asset_data.get("name") or ""
        code = asset_data.get("code") or ""
        name_lower = name.lower()
        code_lower = code.lower()
        if "template" in name_lower or "template" in code_lower:
            return True

        return False

    def get_tasks_for_entity(self, entity_type: str, entity_id: int, project_id: int = None) -> list[dict]:
        """Get all tasks for a specific entity (Asset, Shot, etc.)"""
        try:
            url = f"{self.base_url}api/v1/entity/tasks"
            params = {
                "fields": "id,content,entity,project,step,task_assignees,sg_status_list,created_at,updated_at",
                "filter[entity]": f"{entity_type}.{entity_id}",
            }

            if project_id:
                params["filter[project]"] = f"Project.{project_id}"

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                tasks = data.get("data", [])

                logger.info(f"Found {len(tasks)} tasks for {entity_type} {entity_id}")
                return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks for {entity_type} {entity_id}: {e}")
            return []

    def get_tasks_for_project(self, project_id: int) -> list[dict]:
        """Get all tasks for a project"""
        try:
            url = f"{self.base_url}api/v1/entity/tasks"
            params = {
                "fields": "id,content,entity,project,step,task_assignees,sg_status_list,created_at,updated_at",
                "filter[project]": f"Project.{project_id}",
            }

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                tasks = data.get("data", [])

                logger.info(f"Found {len(tasks)} tasks for project {project_id}")
                return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks for project {project_id}: {e}")
            return []

    def update_task(self, task_id: int, task_data: dict) -> dict | None:
        """Update an existing task"""
        try:
            url = f"{self.base_url}api/v1/entity/tasks/{task_id}"
            headers = {**self.headers, "Content-Type": "application/json"}

            with httpx.Client() as client:
                response = client.patch(url, headers=headers, json=task_data)
                response.raise_for_status()

                data = response.json()
                return data.get("data", {})

        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return None

    def get_task_statuses(self) -> list[dict]:
        """Get available task statuses"""
        try:
            url = f"{self.base_url}api/v1/entity/task_statuses"
            params = {"fields": "id,code,short_name"}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                statuses = data.get("data", [])

                logger.info(f"Found {len(statuses)} task statuses")
                return statuses

        except Exception as e:
            logger.error(f"Failed to get task statuses: {e}")
            return []

    def get_users(self, project_id: int = None) -> list[dict]:
        """Get users, optionally filtered by project"""
        try:
            url = f"{self.base_url}api/v1/entity/users"
            params = {"fields": "id,login,name,email"}
            
            if project_id:
                params["filter[projects]"] = f"Project.{project_id}"

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                users = data.get("data", [])
                
                logger.info(f"Found {len(users)} users")
                return users

        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []

    def get_steps(self) -> list[dict]:
        """Get available steps"""
        try:
            url = f"{self.base_url}api/v1/entity/steps"
            params = {"fields": "id,code,short_name"}

            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                steps = data.get("data", [])
                
                logger.info(f"Found {len(steps)} steps")
                return steps

        except Exception as e:
            logger.error(f"Failed to get steps: {e}")
            return []


def create_shotgrid_api(access_token: str, base_url: str) -> ShotGridAPI:
    """Factory function to create a ShotGridAPI instance"""
    return ShotGridAPI(access_token, base_url)
