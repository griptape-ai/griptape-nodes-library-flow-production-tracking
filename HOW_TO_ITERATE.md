# How to Iterate: Testing & Learning Process for ShotGrid Features

This document outlines the systematic approach for testing and implementing new ShotGrid features in our Griptape nodes.

## 🔬 **Testing & Learning Process for ShotGrid Task Templates**

### **Step 1: Identify the Problem**

- User reported that task templates weren't being applied when creating assets
- Needed to understand how ShotGrid task templates actually work

## 🔬 **Testing & Learning Process for ShotGrid Project Templates**

### **Step 1: Identify the Problem**

- User reported that project creation from templates was failing with "Project.template doesn't exist" error
- Needed to understand the correct way to create projects from templates in ShotGrid

### **Step 2: Start with API Key Authentication**

```bash
# Get access token using API key authentication (client credentials flow)
curl -X POST https://griptape-ai.shotgrid.autodesk.com/api/v1/auth/access_token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: application/json' \
  -d "grant_type=client_credentials&client_id=SCRIPT_NAME&client_secret=API_KEY"
```

### **Step 3: Explore Project Schema**

```bash
# Get project schema to understand available fields
curl -H "Authorization: Bearer $TOKEN" \
  "https://griptape-ai.shotgrid.autodesk.com/api/v1/schema/projects"
```

**Key Discovery**: Projects don't have a `template` field, but they do have relationship fields!

### **Step 4: Find Project Templates**

```bash
# Get all projects and filter for templates
curl -H "Authorization: Bearer $TOKEN" \
  "https://griptape-ai.shotgrid.autodesk.com/api/v1/entity/projects?fields=id,name,code,description,template,sg_type,sg_status,is_template"
```

**Key Discovery**: Templates are identified by `is_template: true`, not by a `template` field!

### **Step 5: Test Different Template Creation Approaches**

```python
# Test different approaches for creating from templates
approaches = [
    # Approach 1: Reference the template as a relationship
    {
        'name': 'Test From Template 1',
        'code': 'tft1',
        'template': {'type': 'Project', 'id': template_id}  # ❌ FAILS
    },
    # Approach 2: Use template_id field
    {
        'name': 'Test From Template 2', 
        'code': 'tft2',
        'template_id': template_id  # ❌ FAILS
    },
    # Approach 3: Use layout_project relationship (this works!)
    {
        'name': 'Test From Template 3',
        'code': 'tft3',
        'layout_project': {'type': 'Project', 'id': template_id}  # ✅ SUCCESS!
    }
]
```

### **Step 6: Learn from Working Examples**

- Examined `flow_create_asset.py` which successfully uses templates
- Found that assets use `task_template` field with `{"type": "TaskTemplate", "id": template_id}`
- Applied same pattern to projects with `layout_project` field

### **Step 7: Apply Learning to Node**

- Updated `_create_project_from_template` method to use `layout_project` relationship
- Removed invalid `template` field usage
- Verified the fix works with API testing

**Key Learning**: Different entity types use different relationship field names for templates!

### **Step 2: Start with Basic API Exploration**

```bash
# Get access token using password auth (more reliable than API key)
curl -X POST https://griptape-ai.shotgrid.autodesk.com/api/v1/auth/access_token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: application/json' \
  -d "username=jason@griptape.ai&password=Mousy-Snap-Deplored4&grant_type=password"
```

### **Step 3: Explore Available Data**

```bash
# Get task templates to understand the data structure
curl -H "Authorization: Bearer $TOKEN" \
  "https://griptape-ai.shotgrid.autodesk.com/api/v1/entity/task_templates?fields=id,name,code,description,entity_type&entity_type=Asset"
```

**Key Discovery**: Template information is in the `code` field, not the `name` field!

### **Step 4: Create Simple Test Script**

```python
# test_curl.py - Basic task creation test
# This revealed that manual task creation works but isn't the right approach
```

### **Step 5: Research the "Right Way"**

- Looked at ShotGrid documentation and examples
- Discovered that task templates should be **attached** to assets, not manually applied
- Found the correct field: `"task_template": {"type": "TaskTemplate", "id": template_id}`

### **Step 6: Create Comprehensive Test**

```python
# test_asset_with_template.py - Proper template attachment test
# This revealed the magic: ShotGrid automatically creates tasks when template is attached!
```

### **Step 7: Apply Learning to Node**

- Updated the create asset node to use the correct approach
- Removed manual task creation logic
- Added template attachment during asset creation

## 🎯 **Key Learning Principles:**

### **1. Start Simple**

- Begin with basic curl commands to understand the API
- Don't assume you know how something works

### **2. Explore the Data Structure**

- Always check what fields are actually available
- Don't assume field names (e.g., `name` vs `code`)

### **3. Test the "Right Way"**

- Research how the feature is supposed to work
- Don't just make it work - make it work correctly

### **4. Learn from Working Examples**

- Look at similar functionality in other parts of the codebase
- Different entity types may use different field names for the same concept
- Example: Assets use `task_template`, Projects use `layout_project` for templates

### **5. Create Isolated Tests**

- Build simple scripts to test specific functionality
- This allows rapid iteration without complex node logic

### **6. Document the Process**

- Keep track of what you learn
- This helps with future debugging and feature development

## 🚀 **Benefits of This Approach:**

1. **Faster Debugging** - Can test API calls directly without node complexity
1. **Better Understanding** - Learn how the system actually works
1. **More Reliable Solutions** - Find the "right way" instead of workarounds
1. **Reusable Knowledge** - Can apply this process to other features
1. **Confidence** - Know exactly what should happen before implementing

## 📝 **Template for Future Testing:**

```bash
# 1. Get authentication working
curl -X POST https://site.shotgrid.autodesk.com/api/v1/auth/access_token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=user&password=pass&grant_type=password"

# 2. Explore the data
curl -H "Authorization: Bearer $TOKEN" \
  "https://site.shotgrid.autodesk.com/api/v1/entity/ENTITY_TYPE?fields=id,name,code"

# 3. Create test script
# test_feature.py - Isolated test of the feature

# 4. Apply learning to node
# Update node with correct approach
```

## 🔧 **ShotGrid Template Relationship Patterns:**

### **Entity-Specific Template Fields**

Different ShotGrid entity types use different field names for template relationships:

- **Assets**: `task_template` → `{"type": "TaskTemplate", "id": template_id}`
- **Projects**: `layout_project` → `{"type": "Project", "id": template_id}`
- **Shots**: `layout_shot` → `{"type": "Shot", "id": template_id}` (likely)

### **Template Discovery Patterns**

Templates are identified by different fields depending on entity type:

- **Projects**: `is_template: true` (boolean field)
- **Task Templates**: `entity_type` field (e.g., "Asset", "Shot")
- **Other entities**: May use `template: true` or similar boolean fields

## 🔧 **ShotGrid REST API Filter Patterns:**

### **Entity Relationship Filtering**

The ShotGrid REST API uses a specific syntax for filtering by entity relationships:

```bash
# Correct syntax for filtering tasks by entity
filter[entity.EntityType.id]=entity_id

# Examples:
filter[entity.Asset.id]=2208        # Tasks for Asset ID 2208
filter[entity.Shot.id]=1234         # Tasks for Shot ID 1234
filter[entity.Project.id]=264       # Tasks for Project ID 264
```

### **Common Filter Patterns**

```bash
# Filter by single entity
filter[entity.Asset.id]=2208

# Filter by multiple entities (OR logic)
filter[entity.Asset.id]=2208,2209,2210

# Filter by project
filter[project.Project.id]=264

# Filter by status
filter[sg_status_list]=wtg,ip,fin

# Filter by assignee
filter[task_assignees.HumanUser.id]=123
```

### **Entity Discovery Optimization**

Instead of iterating through entity types to find an entity, query entity endpoints directly:

```python
# Efficient approach - query entity directly
entity_types = ["Asset", "Shot", "Sequence", "Episode", "Project"]
for entity_type in entity_types:
    url = f"{base_url}api/v1/entity/{entity_type.lower()}s"
    params = {"fields": "id,project", "filter[id]": str(entity_id)}
    response = client.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            # Found the entity type and project info
            break
```

### **Task Data Structure**

Tasks have rich data available including:

**Core Information:**

- `content`: Task name/description
- `sg_status_list`: Status (wtg, ip, fin, etc.)
- `sg_sort_order`: Display order
- `sg_description`: Detailed description
- `sg_priority_1`: Priority level

**Relationships:**

- `entity`: The entity this task belongs to (Asset, Shot, etc.)
- `project`: The project this task belongs to
- `step`: The pipeline step
- `task_assignees`: Who's assigned to this task
- `template_task`: The template this task was created from
- `upstream_tasks`: Tasks that must be completed before this one
- `downstream_tasks`: Tasks that depend on this one
- `sibling_tasks`: Other tasks for the same entity

**Time Tracking:**

- `duration`: Task duration
- `est_in_mins`: Estimated time in minutes
- `time_logs_sum`: Total time logged
- `start_date`, `due_date`: Scheduling information

### **Testing Template Relationships**

```python
# Test template relationship creation
template_data = {
    "name": "Test Entity",
    "code": "test123",
    "TEMPLATE_FIELD": {"type": "EntityType", "id": template_id}  # Use correct field name
}

# Verify the relationship was created
response = httpx.post(create_url, headers=headers, json=template_data)
if response.status_code == 201:
    result = response.json()
    relationships = result.get('data', {}).get('relationships', {})
    if 'TEMPLATE_FIELD' in relationships:
        template_ref = relationships['TEMPLATE_FIELD']['data']
        print(f"Template linked: {template_ref.get('name')} (ID: {template_ref.get('id')})")
```

## 🔧 **Common Testing Patterns:**

### **Authentication Testing**

```python
import httpx

# Get access token
auth_url = "https://site.shotgrid.autodesk.com/api/v1/auth/access_token"
auth_data = {
    "username": "user@example.com",
    "password": "password",
    "grant_type": "password"
}
auth_headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

auth_response = httpx.post(auth_url, data=auth_data, headers=auth_headers)
auth_response.raise_for_status()
token_data = auth_response.json()
access_token = token_data.get("access_token")
```

### **API Exploration**

```python
# Explore entity data
headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
url = "https://site.shotgrid.autodesk.com/api/v1/entity/ENTITY_TYPE?fields=id,name,code,description"

response = httpx.get(url, headers=headers)
response.raise_for_status()
data = response.json()

for item in data.get('data', []):
    print(f"ID: {item.get('id')}, Name: '{item.get('attributes', {}).get('name', '')}', Code: '{item.get('attributes', {}).get('code', '')}'")
```

### **Feature Testing**

```python
# Test creating something with the feature
create_data = {
    "field1": "value1",
    "field2": "value2",
    "feature_field": {"type": "FeatureType", "id": feature_id}  # The feature we're testing
}

create_url = "https://site.shotgrid.autodesk.com/api/v1/entity/ENTITY_TYPE"
create_headers = {**headers, "Content-Type": "application/json"}

create_response = httpx.post(create_url, headers=create_headers, json=create_data)
create_response.raise_for_status()
result = create_response.json()
print(f"Created with ID: {result.get('data', {}).get('id')}")
```

## 🔧 **UI/UX Parameter Management Patterns:**

### **Selection Persistence in Dynamic Dropdowns**

When building nodes with dynamic dropdown choices (like project lists, asset lists), selection persistence is critical:

```python
def _reload_choices(self, preserve_selection=True):
    """Reload choices while preserving user selection."""
    if preserve_selection:
        # Store current selection before reload
        current_selection = self.get_parameter_value("parameter_name")
        
        # Reload the choices
        new_choices = self._fetch_choices()
        
        # Find and restore the selection
        if current_selection and current_selection in new_choices:
            selected_value = current_selection
        else:
            selected_value = new_choices[0] if new_choices else None
            
        self._update_option_choices("parameter_name", new_choices, selected_value)
    else:
        # Always select first item (e.g., when project changes)
        new_choices = self._fetch_choices()
        self._update_option_choices("parameter_name", new_choices, new_choices[0])
```

### **Parameter Value Preservation in after_value_set**

When `after_value_set` triggers dropdown updates, always preserve the current selection:

```python
def after_value_set(self, parameter: Parameter, value: Any) -> None:
    if parameter.name == "project_id" and value:
        # Get current selection before updating
        current_selection = self.get_parameter_value("asset_type")
        
        # Update choices
        new_choices = self._get_choices_for_project(value)
        
        # Preserve selection if still valid
        if current_selection and current_selection in new_choices:
            selected_value = current_selection
        else:
            selected_value = new_choices[0] if new_choices else None
            
        self._update_option_choices("asset_type", new_choices, selected_value)
```

### **Output Parameter Population Patterns**

For nodes that display selected data, use consistent output parameter patterns:

```python
def _update_selected_data(self, selected_item):
    """Update all output parameters with selected item data."""
    if not selected_item:
        # Clear all outputs
        self.set_parameter_value("item_id", "")
        self.set_parameter_value("item_data", {})
        self.set_parameter_value("item_url", "")
        self.set_parameter_value("item_description", "")
        return
    
    # Populate outputs
    item_id = selected_item.get("id", "")
    self.set_parameter_value("item_id", str(item_id))
    self.set_parameter_value("item_data", selected_item)
    
    # Generate web UI URL
    base_url = self._get_shotgrid_config()["base_url"]
    item_url = f"{base_url.rstrip('/')}/detail/EntityType/{item_id}"
    self.set_parameter_value("item_url", item_url)
    
    # Extract description
    attributes = selected_item.get("attributes", {})
    description = attributes.get("description", "") or attributes.get("sg_description", "")
    self.set_parameter_value("item_description", description)
    
    # Publish updates
    self.publish_update_to_parameter("item_id", str(item_id))
    self.publish_update_to_parameter("item_data", selected_item)
    self.publish_update_to_parameter("item_url", item_url)
    self.publish_update_to_parameter("item_description", description)
```

## 🔧 **ShotGrid URL Pattern Consistency:**

### **Web UI URL Generation**

ShotGrid REST API returns API URLs, but users need web UI URLs. Use consistent patterns:

```python
def _generate_web_url(self, entity_type: str, entity_id: int) -> str:
    """Generate ShotGrid web UI URL from entity type and ID."""
    try:
        base_url = self._get_shotgrid_config()["base_url"]
        return f"{base_url.rstrip('/')}/detail/{entity_type}/{entity_id}"
    except Exception:
        # Fallback to generic ShotGrid URL
        return f"https://shotgrid.autodesk.com/detail/{entity_type}/{entity_id}"

# Examples:
# /detail/Project/264
# /detail/Asset/2204  
# /detail/Task/6817
```

### **API vs Web URL Conversion**

When ShotGrid API provides a `self` link, convert it to web URL:

```python
def _convert_api_url_to_web_url(self, api_url: str, entity_type: str, entity_id: int) -> str:
    """Convert ShotGrid API URL to web UI URL."""
    if api_url and f"/api/v1/entity/{entity_type.lower()}s/" in api_url:
        # Extract path and convert to web format
        path = api_url.replace(f"/api/v1/entity/{entity_type.lower()}s/", f"/{entity_type.lower()}s/")
        base_url = self._get_shotgrid_config()["base_url"]
        return f"{base_url.rstrip('/')}{path}"
    else:
        # Fallback to direct URL generation
        return self._generate_web_url(entity_type, entity_id)
```

## 🔧 **Parameter Message vs Output Parameter Patterns:**

### **When to Use ParameterMessage vs Output Parameters**

**Use ParameterMessage for:**

- Temporary status updates during processing
- Interactive buttons that trigger actions
- Non-persistent information display

**Use Output Parameters for:**

- Data that other nodes need to consume
- Persistent information that should be available after processing
- URLs, IDs, and structured data

### **Migration from ParameterMessage to Output Parameters**

```python
# OLD: ParameterMessage approach
self.project_message = ParameterMessage(
    name="project_message",
    message="Select a project to view details",
    button_text="View Project",
    button_link=""
)

# NEW: Output parameter approach
self.add_parameter(
    Parameter(
        name="project_url",
        type="string", 
        default_value="",
        tooltip="The URL to view the project in ShotGrid",
        allowed_modes={ParameterMode.OUTPUT}
    )
)
```

## 🔧 **JSON Path Extraction Patterns:**

### **Root Array Indexing**

When extracting values from JSON arrays, handle root-level indexing:

```python
def extract_value_from_path(data, path):
    """Extract value from JSON data using dot notation path."""
    parts = path.split('.')
    current = data
    
    for part in parts:
        # Handle array indexing: [0], [1], etc.
        if part.startswith('[') and part.endswith(']'):
            index = int(part[1:-1])
            if isinstance(current, list) and 0 <= index < len(current):
                current = current[index]
            else:
                return None
        # Handle key[0] pattern: items[0]
        elif '[' in part and ']' in part:
            key, index_part = part.split('[', 1)
            index = int(index_part.rstrip(']'))
            if isinstance(current, dict) and key in current:
                if isinstance(current[key], list) and 0 <= index < len(current[key]):
                    current = current[key][index]
                else:
                    return None
            else:
                return None
        # Handle regular key access
        else:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
    
    return current

# Examples:
# "[0]" -> data[0]
# "[0].id" -> data[0]["id"] 
# "items[0]" -> data["items"][0]
# "items[0].name" -> data["items"][0]["name"]
```

## 🔧 **Error Handling and User Experience:**

### **Graceful Fallbacks for Missing Data**

Always provide fallbacks for missing or invalid data:

```python
def _safe_get_description(self, item_data):
    """Safely extract description with multiple fallbacks."""
    attributes = item_data.get("attributes", {})
    
    # Try multiple description fields
    description = (
        attributes.get("description") or
        attributes.get("sg_description") or 
        attributes.get("name") or
        ""
    )
    
    return description.strip() if description else "No description available"
```

### **Image Handling with Fallbacks**

```python
def _create_fallback_image(self, text: str, width: int = 200, height: int = 150):
    """Create a fallback image when the original is unavailable."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image
        img = Image.new('RGB', (width, height), color='#404040')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        
        # Convert to base64
        import io
        import base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_data}"
        
    except Exception as e:
        logger.warning(f"Failed to create fallback image: {e}")
        return None
```

## 🔧 **Dynamic Data Management Pattern (List + Select + Refresh):**

### **The "Load All, Select One, Refresh One" Pattern**

This is a powerful UI/UX pattern for managing collections of data (projects, assets, tasks, etc.) that provides excellent user experience and efficient API usage.

#### **Core Pattern Components:**

1. **Process Method**: Loads ALL items from API and populates dropdown
2. **Selection Change**: Updates display from cached data (no API call)
3. **Refresh Button**: Updates only the selected item from API

#### **Implementation Structure:**

```python
class FlowListItems(BaseShotGridNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Input parameter for selection
        self.add_parameter(
            ParameterString(
                name="selected_item",
                default_value="Load items to see options",
                tooltip="Select an item from the list",
                traits={
                    Options(choices=ITEM_CHOICES),
                    Button(
                        icon="refresh-cw",
                        variant="secondary",
                        on_click=self._refresh_selected_item,
                        label="Refresh Selected",
                    ),
                },
            )
        )
        
        # Output parameters for selected item data
        self.add_parameter(ParameterString(name="item_id", allowed_modes={ParameterMode.OUTPUT}))
        self.add_parameter(ParameterString(name="item_name", allowed_modes={ParameterMode.OUTPUT}))
        self.add_parameter(ParameterString(name="item_url", allowed_modes={ParameterMode.OUTPUT}))
        self.add_parameter(ParameterString(name="item_description", allowed_modes={ParameterMode.OUTPUT}))
        self.add_parameter(Parameter(name="item_data", type="json", allowed_modes={ParameterMode.OUTPUT}))
        self.add_parameter(Parameter(name="all_items", type="json", allowed_modes={ParameterMode.OUTPUT}))
```

#### **1. Process Method - Load All Items:**

```python
def process(self) -> None:
    """Load all items when node is run."""
    try:
        # Get current selection to preserve it
        current_selection = self.get_parameter_value("selected_item")
        
        # Load all items from API
        logger.info(f"{self.name}: Loading items from API...")
        items = self._fetch_all_items_from_api()
        
        if not items:
            logger.warning(f"{self.name}: No items found")
            self._update_option_choices("selected_item", ["No items available"], "No items available")
            return
        
        # Process items to choices
        item_list, choices_names = self._process_items_to_choices(items)
        
        # Store all items data using SetParameterValueRequest
        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name="all_items", value=item_list, node_name=self.name)
        )
        self.parameter_output_values["all_items"] = item_list
        self.publish_update_to_parameter("all_items", item_list)
        
        # Determine what to select
        selected_value = choices_names[0] if choices_names else "No items available"
        selected_index = 0
        
        # Try to preserve the current selection
        if current_selection and current_selection != "Load items to see options" and current_selection in choices_names:
            selected_index = choices_names.index(current_selection)
            selected_value = current_selection
            logger.info(f"{self.name}: Preserved selection: {current_selection}")
        else:
            selected_value = choices_names[0]
            selected_index = 0
            logger.info(f"{self.name}: Selected first item: {choices_names[0]}")
        
        # Update the dropdown choices - CRITICAL: Use _update_option_choices, NOT global variables
        self._update_option_choices("selected_item", choices_names, selected_value)
        
        # Update the selected item data
        self._update_item_data(selected_index)
        
        logger.info(f"{self.name}: Successfully loaded {len(item_list)} items")
        
    except Exception as e:
        logger.error(f"{self.name}: Failed to load items: {e}")
        self._update_option_choices("selected_item", ["Error loading items"], "Error loading items")
```

#### **2. Selection Change - Use Cached Data:**

```python
def after_value_set(self, parameter: Parameter, value: Any) -> None:
    """Update item data when selection changes."""
    if parameter.name == "selected_item":
        self.publish_update_to_parameter("selected_item", value)
        if value and value != "Load items to see options":
            # Find the index of the selected item by matching display names
            items = self.get_parameter_value("all_items") or []
            selected_index = 0
            
            # Clean the selection to match against item names
            clean_selection = value.replace("📋 ", "").replace(" (Template)", "")
            
            for i, item in enumerate(items):
                item_name = item.get("name", "")
                if item_name == clean_selection:
                    selected_index = i
                    break
            
            self._update_item_data(selected_index)
    return super().after_value_set(parameter, value)
```

#### **3. Refresh Button - Update Selected Item Only:**

```python
def _refresh_selected_item(self, button: Button, button_details: ButtonDetailsMessagePayload) -> None:
    """Refresh the selected item when refresh button is clicked."""
    try:
        current_selection = self.get_parameter_value("selected_item")
        if not current_selection or current_selection == "Load items to see options":
            logger.warning(f"{self.name}: No item selected to refresh")
            return None

        # Clean the selection to get the actual item name
        clean_selection = current_selection.replace("📋 ", "").replace(" (Template)", "")
        
        # Get the current item ID from all_items
        items = self.get_parameter_value("all_items") or []
        selected_item_id = None
        selected_index = 0
        
        for i, item in enumerate(items):
            item_name = item.get("name", "")
            if item_name == clean_selection:
                selected_item_id = item.get("id")
                selected_index = i
                break
        
        if not selected_item_id:
            logger.warning(f"{self.name}: Could not find item ID for '{clean_selection}'")
            return None

        # Fetch fresh data for this specific item
        logger.info(f"{self.name}: Refreshing item {selected_item_id} ({clean_selection})")
        fresh_item_data = self._fetch_single_item(selected_item_id)
        
        if not fresh_item_data:
            logger.warning(f"{self.name}: Failed to fetch fresh data for item {selected_item_id}")
            return None

        # Update the item in all_items using SetParameterValueRequest
        items[selected_index] = fresh_item_data
        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name="all_items", value=items, node_name=self.name)
        )
        self.parameter_output_values["all_items"] = items
        self.publish_update_to_parameter("all_items", items)

        # Update the item data display
        self._update_item_data(selected_index)
        
        logger.info(f"{self.name}: Successfully refreshed item {selected_item_id}")

    except Exception as e:
        logger.error(f"{self.name}: Failed to refresh selected item: {e}")
    return None
```

#### **4. Data Update Helper - Use SetParameterValueRequest:**

```python
def _update_item_data(self, selected_index: int) -> None:
    """Update item parameters based on the selected item index."""
    items = self.get_parameter_value("all_items")
    if not items or selected_index >= len(items):
        return

    item = items[selected_index]
    item_name = item.get("name", f"Item {item.get('id', 'Unknown')}")
    item_description = item.get("description", "")
    
    # Generate web UI URL
    base_url = self._get_shotgrid_config()["base_url"]
    item_url = f"{base_url}detail/ItemType/{item['id']}"

    # Update all item parameters using SetParameterValueRequest
    params = {
        "item_id": item["id"],
        "item_name": item_name,
        "item_url": item_url,
        "item_description": item_description,
        "item_data": item,
    }

    for param_name, value in params.items():
        GriptapeNodes.handle_request(
            SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
        )
        self.parameter_output_values[param_name] = value
        self.publish_update_to_parameter(param_name, value)
```

#### **5. Single Item Fetch Helper:**

```python
def _fetch_single_item(self, item_id: int) -> dict | None:
    """Fetch a single item from API."""
    try:
        access_token = self._get_access_token()
        base_url = self._get_shotgrid_config()["base_url"]
        url = f"{base_url}api/v1/entity/items/{item_id}"
        
        params = {"fields": "id,name,description,status,created_at,updated_at"}
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            item_data = data.get("data")
            
            if item_data:
                # Add URL field for consistency
                item_data["url"] = f"{base_url}detail/ItemType/{item_id}"
                
                # Process the item data
                attributes = item_data.get("attributes", {})
                item_data.update(attributes)
                
                return item_data
            
            return None
            
    except Exception as e:
        logger.error(f"{self.name}: Failed to fetch item {item_id}: {e}")
        return None
```

#### **🚨 CRITICAL: Dropdown Update Pattern**

**❌ WRONG - Don't Use Global Variables:**
```python
# DON'T DO THIS - Global variables don't update the UI
global ITEM_CHOICES, ITEM_CHOICES_ARGS
ITEM_CHOICES = choices_names
ITEM_CHOICES_ARGS = []
```

**✅ CORRECT - Use _update_option_choices Method:**
```python
# DO THIS - Updates the Options trait directly
self._update_option_choices("selected_item", choices_names, selected_value)
```

**Why This Matters:**
- Global variables (`ITEM_CHOICES`) are only used during parameter initialization
- The dropdown UI is controlled by the `Options` trait on the parameter
- `_update_option_choices()` directly updates the `Options` trait, which updates the UI
- This is the same pattern used in `flow_list_projects.py` and other working nodes

#### **Key Benefits of This Pattern:**

1. **🚀 Fast Selection**: No API calls when switching items (uses cached data)
2. **🎯 Targeted Refresh**: Only updates what changed (efficient API usage)
3. **🔄 Smart Caching**: Maintains full dataset while allowing individual updates
4. **🧠 Selection Persistence**: Preserves user selections across reloads
5. **📱 Intuitive UX**: Standard "run node → get results" workflow
6. **⚡ Efficient**: Minimal API calls, maximum responsiveness

#### **Required Imports:**

```python
from griptape_nodes.retained_mode.events.parameter_events import SetParameterValueRequest
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes, logger
```

#### **SetParameterValueRequest Pattern:**

Always use this three-step pattern for parameter updates:

```python
# 1. SetParameterValueRequest for proper UI updates
GriptapeNodes.handle_request(
    SetParameterValueRequest(parameter_name=param_name, value=value, node_name=self.name)
)

# 2. Update parameter_output_values for downstream nodes
self.parameter_output_values[param_name] = value

# 3. Publish updates to trigger UI updates
self.publish_update_to_parameter(param_name, value)
```

#### **When to Use This Pattern:**

- ✅ **List/Select Nodes**: When users need to choose from a collection
- ✅ **Data Refresh**: When individual items might change frequently
- ✅ **Large Datasets**: When loading all data upfront is acceptable
- ✅ **User Selection**: When preserving user choices is important
- ✅ **Efficient Updates**: When you want to minimize API calls

#### **Examples in Codebase:**

- `flow_list_projects.py` - Projects with refresh
- `flow_list_assets.py` - Assets with refresh  
- `flow_list_tasks.py` - Tasks with refresh

#### **🔧 Troubleshooting: Dropdown Not Updating**

**Symptoms:**
- Running the node updates `all_items` but dropdown shows old choices
- Dropdown shows "Load items to see options" even after successful API call
- Selection works but choices don't refresh

**Common Causes:**
1. **Using global variables instead of `_update_option_choices()`**
   ```python
   # ❌ This won't update the UI
   global ITEM_CHOICES
   ITEM_CHOICES = choices_names
   
   # ✅ This will update the UI
   self._update_option_choices("selected_item", choices_names, selected_value)
   ```

2. **Missing `_update_option_choices()` call in process method**
   ```python
   # ❌ Missing this line
   self._update_option_choices("selected_item", choices_names, selected_value)
   ```

3. **Incorrect parameter name in `_update_option_choices()`**
   ```python
   # ❌ Wrong parameter name
   self._update_option_choices("selected_items", choices_names, selected_value)
   
   # ✅ Correct parameter name
   self._update_option_choices("selected_item", choices_names, selected_value)
   ```

**Quick Fix Checklist:**
- [ ] Using `_update_option_choices()` not global variables
- [ ] Calling `_update_option_choices()` in process method
- [ ] Parameter name matches exactly
- [ ] Choices list is not empty
- [ ] Selected value is in the choices list

#### **🚨 CRITICAL: Parameter Type and Data Structure Issues**

**❌ WRONG - Using ParameterString with ui_options:**
```python
# DON'T DO THIS - ParameterString doesn't work with _update_option_choices
ParameterString(
    name="selected_item",
    allow_property=True,
    ui_options={
        "display_name": "Select Item",
        "data": ITEM_CHOICES_ARGS,  # This interferes with dropdown updates!
        "icon_size": "medium",
    },
    traits={Options(choices=ITEM_CHOICES)}
)
```

**✅ CORRECT - Use Parameter with allowed_modes:**
```python
# DO THIS - Parameter works with _update_option_choices
Parameter(
    name="selected_item",
    type="string",
    allowed_modes={ParameterMode.PROPERTY},
    traits={Options(choices=ITEM_CHOICES)}
)
```

**Why This Matters:**
- `_update_option_choices()` is designed for the base `Parameter` class, not specialized types like `ParameterString`
- `ui_options` with `data` can interfere with dropdown updates
- `allowed_modes={ParameterMode.PROPERTY}` is the correct pattern for dropdown parameters

#### **🚨 CRITICAL: Data Structure Mismatch in Selection Updates**

**The Problem:**
When `after_value_set` calls `_update_selected_item_data()`, it passes data from `all_items` (processed structure), but the method expects raw API data structure.

**❌ WRONG - Expecting raw API structure:**
```python
def _update_selected_item_data(self, item_data: dict) -> None:
    # This expects raw ShotGrid API structure
    attributes = item_data.get("attributes", {})
    item_name = attributes.get("name", f"Item {item_id}")
    item_description = attributes.get("description", "")
```

**✅ CORRECT - Handle processed data structure:**
```python
def _update_selected_item_data(self, item_data: dict) -> None:
    # This works with processed all_items structure
    item_name = item_data.get("name", f"Item {item_id}")
    item_description = item_data.get("description", "")
```

**Data Structure Patterns:**

**Raw ShotGrid API Response:**
```json
{
  "id": 123,
  "attributes": {
    "name": "Item Name",
    "code": "ITEM_CODE", 
    "description": "Description"
  }
}
```

**Processed all_items Structure:**
```json
{
  "id": 123,
  "name": "Item Name",
  "code": "ITEM_CODE",
  "description": "Description"
}
```

**Key Learning:**
- `all_items` contains processed/flattened data structure
- `_update_selected_item_data()` must work with processed structure
- Raw API data is only used during initial fetch and single item refresh

#### **🔍 Debugging Process for Dropdown Issues**

**Step 1: Verify Dropdown Updates**
- Check if `_update_option_choices()` is being called
- Verify parameter name matches exactly
- Confirm choices list is not empty

**Step 2: Check Parameter Definition**
- Use `Parameter` not `ParameterString` for dropdowns
- Use `allowed_modes={ParameterMode.PROPERTY}` not `allow_property=True`
- Avoid `ui_options` with `data` that might interfere

**Step 3: Verify Data Structure Consistency**
- Check if `_update_selected_item_data()` expects the right data structure
- Raw API data: `item.get("attributes", {}).get("name")`
- Processed data: `item.get("name")`
- `all_items` contains processed data, not raw API data

**Step 4: Test Selection Updates**
- Verify `after_value_set` is called when dropdown changes
- Check if selection matching logic works correctly
- Ensure `_update_selected_item_data()` is called with correct data

**Common Debugging Questions:**
1. "Is the dropdown updating?" → Check `_update_option_choices()` usage
2. "Are selections working?" → Check parameter type and data structure
3. "Are details updating?" → Check `_update_selected_item_data()` data structure handling

## 🎯 **Success Criteria:**

- [ ] API calls work with curl/httpx
- [ ] Data structure is understood
- [ ] Feature works in isolation
- [ ] Node implementation follows the "right way"
- [ ] Feature works reliably in the node
- [ ] UI/UX patterns are consistent and user-friendly
- [ ] Selection persistence works correctly
- [ ] Output parameters provide useful data
- [ ] Error handling is graceful with fallbacks
- [ ] Process is documented for future reference
- [ ] **Dynamic data management pattern is implemented correctly**
- [ ] **SetParameterValueRequest is used for all parameter updates**
- [ ] **Process loads all data, selection uses cache, refresh updates selected item**

## 📚 **Resources:**

- [ShotGrid API Documentation](https://developer.shotgridsoftware.com/rest-api/)
- [ShotGrid Python API](https://github.com/shotgunsoftware/python-api)
- [Griptape Nodes Documentation](https://docs.griptape.ai/)

## 🔧 **ShotGrid API Reference - Postman Collection:**

### **Using the ShotGrid REST API v1.x Postman Collection**

The project includes a comprehensive Postman collection that contains all ShotGrid REST API endpoints with examples:

**Location**: `GriptapeNodes/libraries/griptape-nodes-library-flow-production-tracking/ShotGrid REST API v1.x.postman_collection.json`

### **How to Use the Postman Collection:**

1. **Import into Postman**: Load the JSON file into Postman to explore all available endpoints
2. **Find Specific Endpoints**: Search for keywords like "upload", "create", "update" to find relevant APIs
3. **Check Request/Response Examples**: Each endpoint includes example requests and responses
4. **Understand Parameters**: See exactly what query parameters and body fields are required

### **Key Benefits:**

- **Exact Endpoint URLs**: No guessing about API structure
- **Parameter Examples**: See real examples of required fields
- **Response Formats**: Understand the exact JSON structure returned
- **Authentication Patterns**: See how different auth methods work
- **Error Examples**: Understand common error responses

### **Example: Finding Upload Endpoints**

```bash
# Search the Postman collection for upload patterns
grep -i "_upload" "ShotGrid REST API v1.x.postman_collection.json"

# This reveals the exact API structure:
# GET /api/v1/entity/:entity/:record_id/_upload?filename=<string>
# PUT /api/v1/entity/:entity/:record_id/_upload?filename=<string>&signature=<string>
# POST /api/v1/entity/:entity/:record_id/_upload?filename=<string>
```

### **When to Reference the Postman Collection:**

- ✅ **New Feature Development**: Before implementing any ShotGrid API calls
- ✅ **Debugging API Issues**: When endpoints return unexpected errors
- ✅ **Understanding Response Structure**: To parse API responses correctly
- ✅ **Finding Required Parameters**: To ensure all required fields are included
- ✅ **Testing API Changes**: To verify endpoint behavior before coding

### **Pro Tips:**

1. **Search by Feature**: Use `grep` to find all endpoints related to a specific feature
2. **Check Examples**: Look at the example request/response bodies for data structure
3. **Verify Parameters**: Ensure you're using the correct query parameters and field names
4. **Test First**: Use Postman to test endpoints before implementing in code

______________________________________________________________________

*This process ensures we build features that work correctly and reliably!* 🎯
