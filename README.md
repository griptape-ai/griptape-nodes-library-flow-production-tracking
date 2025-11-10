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

To configure these settings, use the **Autodesk Flow Configuration** node which will walk you through the following steps:

1. **Enter your Autodesk Flow URL**: Provide your instance URL (typically in the format: `https://your-company.shotgrid.autodesk.com/`)

2. **Set your Script Name**: Enter the name of your Autodesk Flow script. This should match the script name you created in Autodesk Flow Admin > Scripts.
   
   If you haven't created a script yet, you need to:
   - Go to Autodesk Flow Admin > Scripts
   - Create a new script with the name you want to use
   - Copy the script key (API key) for use in the next step

3. **Configure your API Key**: Set your `SHOTGRID_API_KEY` (Script Key) in Settings. The configuration node provides a button to open Settings where you can paste your API key.
   
   If you don't have an API key, you can create one in Autodesk Flow Admin > Scripts, or ask your administrator for one.

4. **Check Configuration**: Click the "Check Configuration" button to test your Autodesk Flow configuration and verify everything is working correctly.

## Installation

To add this library to your Griptape Nodes installation:

1. **Download the library** to your machine. We recommend creating a folder called `libraries` in your workspace (for example: `/Users/jason/Documents/GriptapeNodes/libraries`). Then download the library to that location:
   
   **Option A: Download ZIP**
   - In GitHub, click the Green **Code** button and choose [Download zip](https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking/archive/refs/heads/main.zip)
   - Unzip the file (it will be named `griptape-nodes-library-flow-production-tracking-main`)
   - Move the folder to your library location and rename it to `griptape-nodes-library-flow-production-tracking` (remove the `-main` suffix)
   
   **Option B: Using Git** (if you have git installed)
   ```bash
   cd /Users/jason/Documents/GriptapeNodes/libraries
   git clone https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking.git
   ```

2. **Open Griptape Nodes**

3. **Add the library**:
   - Go to **Settings** → **Settings** → **Libraries**
   - Click **Add Library**
   - Add the path to the library folder (ex: `/Users/jason/Documents/GriptapeNodes/libraries/`)
   - This will automatically discover all libraries located in that folder!

4. **Reload Libraries**
    - Close the settings modal and click **Reload Libraries** in the sidebar

5. Your library will now be available! You can find the nodes in the **Libraries** dropdown on the left sidebar and drag and drop them into your flows.
