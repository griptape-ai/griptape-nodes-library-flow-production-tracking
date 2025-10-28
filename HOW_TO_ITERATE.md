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

## 📚 **Resources:**

- [ShotGrid API Documentation](https://developer.shotgridsoftware.com/rest-api/)
- [ShotGrid Python API](https://github.com/shotgunsoftware/python-api)
- [Griptape Nodes Documentation](https://docs.griptape.ai/)

______________________________________________________________________

*This process ensures we build features that work correctly and reliably!* 🎯
