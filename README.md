# Autodesk Flow Production Tracking Nodes

This library provides Griptape Nodes for interacting with Autodesk Flow Production Tracking (formerly ShotGrid). These nodes allow you to connect to your Autodesk Flow account and create, update, and get information about projects, assets, and entities.

## What You Can Do

With these nodes, you can:

- **Connect to Autodesk Flow**: Configure your connection using the Autodesk Flow Configuration node with your instance URL, script name, and API key
- **Manage Projects**: Create, list, get, and update projects with support for project templates and thumbnails
- **Manage Assets**: Create, list, get, and update assets; retrieve available asset types for projects
- **Manage Tasks**: Create, list, get, and update tasks; retrieve task status information
- **Work with Entities**: Get detailed information about any entity type (Asset, Shot, Sequence, Project, Task, User, Version, etc.) and update entity data
- **Handle Files**: Upload files to entities, update version information, and resolve file paths
- **Manage Users**: List users in your Autodesk Flow instance
- **Access Schemas**: Retrieve schema information for entities

## Configuration

**IMPORTANT:** To use these nodes, you will need:

1. **Autodesk Flow Instance URL**: Your ShotGrid instance URL (e.g., `https://your-company.shotgrid.autodesk.com/`)
2. **Script Name**: A script name created in Autodesk Flow Admin > Scripts
3. **API Key**: The script key (API key) for your script

To configure these settings:

1. Use the **Autodesk Flow Configuration** node to set up your connection
2. Or manually configure secrets in Settings:
   - Open the **Settings** menu
   - Navigate to the **API Keys & Secrets** panel
   - Add secrets for:
     - `SHOTGRID_URL`: Your Autodesk Flow instance URL
     - `SHOTGRID_API_KEY`: Your script key (API key)
     - `SHOTGRID_SCRIPT_NAME`: Your script name (optional, defaults to "Griptape Nodes")

## Installation

To add this library to your Griptape Nodes installation:

1. **Download the library** to your machine in a location you prefer. We recommend creating a folder called `libraries` in your workspace:
   ```bash
   git clone <library_url>
   ```

2. **Open Griptape Nodes**

3. **Add the library**:
   - Go to **Settings** → **Settings** → **Libraries**
   - Click **Add Library**
   - Add the path to the library folder

4. **Reload Libraries**
    - Close the settings modal and click **Reload Libraries** in the sidebar

5. Your library will now be available! You can find the nodes in the **Libraries** dropdown on the left sidebar and drag and drop them into your flows.
