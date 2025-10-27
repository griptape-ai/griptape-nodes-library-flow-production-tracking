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

## 🎯 **Success Criteria:**

- [ ] API calls work with curl/httpx
- [ ] Data structure is understood
- [ ] Feature works in isolation
- [ ] Node implementation follows the "right way"
- [ ] Feature works reliably in the node
- [ ] Process is documented for future reference

## 📚 **Resources:**

- [ShotGrid API Documentation](https://developer.shotgridsoftware.com/rest-api/)
- [ShotGrid Python API](https://github.com/shotgunsoftware/python-api)
- [Griptape Nodes Documentation](https://docs.griptape.ai/)

______________________________________________________________________

*This process ensures we build features that work correctly and reliably!* 🎯
