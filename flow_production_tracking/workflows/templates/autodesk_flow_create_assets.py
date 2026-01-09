# /// script
# dependencies = []
#
# [tool.griptape-nodes]
# name = "autodesk_flow_create_assets"
# schema_version = "0.14.0"
# engine_version_created_with = "0.67.0"
# node_libraries_referenced = [["Griptape Nodes Library", "0.56.1"], ["Flow Production Tracking Library", "0.1.1"]]
# node_types_used = [["Flow Production Tracking Library", "FlowCreateAsset"], ["Flow Production Tracking Library", "FlowListProjects"], ["Griptape Nodes Library", "Agent"], ["Griptape Nodes Library", "DisplayList"], ["Griptape Nodes Library", "FluxImageGeneration"], ["Griptape Nodes Library", "ForEachEndNode"], ["Griptape Nodes Library", "ForEachStartNode"], ["Griptape Nodes Library", "MergeTexts"], ["Griptape Nodes Library", "Note"], ["Griptape Nodes Library", "SplitText"], ["Griptape Nodes Library", "TextInput"]]
# is_griptape_provided = true
# is_template = true
# descsription = "Create assets within a project."
# creation_date = 2026-01-09T20:25:55.927668Z
# last_modified_date = 2026-01-09T20:57:25.458419Z
#
# ///

import pickle

from griptape_nodes.node_library.library_registry import NodeMetadata
from griptape_nodes.retained_mode.events.connection_events import CreateConnectionRequest
from griptape_nodes.retained_mode.events.flow_events import CreateFlowRequest
from griptape_nodes.retained_mode.events.library_events import LoadLibrariesRequest
from griptape_nodes.retained_mode.events.node_events import CreateNodeRequest
from griptape_nodes.retained_mode.events.parameter_events import (
    AlterParameterDetailsRequest,
    SetParameterValueRequest,
)
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

GriptapeNodes.handle_request(LoadLibrariesRequest())

context_manager = GriptapeNodes.ContextManager()

if not context_manager.has_current_workflow():
    context_manager.push_workflow(workflow_name="autodesk_flow_create_assets")

"""
1. We've collated all of the unique parameter values into a dictionary so that we do not have to duplicate them.
   This minimizes the size of the code, especially for large objects like serialized image files.
2. We're using a prefix so that it's clear which Flow these values are associated with.
3. The values are serialized using pickle, which is a binary format. This makes them harder to read, but makes
   them consistently save and load. It allows us to serialize complex objects like custom classes, which otherwise
   would be difficult to serialize.
"""
top_level_unique_values_dict = {
    "8adec450-bc0c-4bcb-a599-d77b4d042a3e": pickle.loads(
        b"\x80\x04\x95\xcb\x00\x00\x00\x00\x00\x00\x00\x8c\xc7# Generating Assets\n\nThis willflow will demonstrate two different ways to create assets.\n\nOne will be a single asset, and then the second will be a flow that lets you create a list of assets at once.\x94."
    ),
    "ca114065-d664-46d7-8a77-19d6cad4f9cb": pickle.loads(
        b"\x80\x04\x95\xbc\x00\x00\x00\x00\x00\x00\x00\x8c\xb8## Create an Asset\n\nTo get started, let's just create a single asset for this project. \n\nHere, we'll create the asset name, a description, generate an image, and then create the asset.\x94."
    ),
    "4bc98aee-212c-420d-8bc1-12c65d1556bf": pickle.loads(
        b'\x80\x04\x95"\x00\x00\x00\x00\x00\x00\x00\x8c\x1ea rough production sketch of a\x94.'
    ),
    "264031c2-4d9e-4654-9df7-bdbfd921a626": pickle.loads(
        b"\x80\x04\x95\x0e\x00\x00\x00\x00\x00\x00\x00\x8c\ncoffee mug\x94."
    ),
    "0fff65fc-b4ef-44b7-8298-c646c9d5c572": pickle.loads(
        b"\x80\x04\x95\x08\x00\x00\x00\x00\x00\x00\x00\x8c\x04\\n\\n\x94."
    ),
    "f17c0f0b-307c-49e0-9d12-54301ae072d6": pickle.loads(b"\x80\x04\x89."),
    "18e1442b-0973-40c2-8cce-210be417536a": pickle.loads(
        b"\x80\x04\x95.\x00\x00\x00\x00\x00\x00\x00\x8c*a rough production sketch of a\n\ncoffee mug\x94."
    ),
    "59e7d59d-a238-4e04-be92-597c47cfc17c": pickle.loads(
        b"\x80\x04\x95\x14\x00\x00\x00\x00\x00\x00\x00\x8c\x10flux-kontext-pro\x94."
    ),
    "0d85767e-a7ef-4c37-86be-c0736f69df8e": pickle.loads(
        b"\x80\x04\x95\x07\x00\x00\x00\x00\x00\x00\x00\x8c\x031:1\x94."
    ),
    "cf743287-ff47-4258-bd68-fc9bf17cefff": pickle.loads(
        b"\x80\x04\x95\x06\x00\x00\x00\x00\x00\x00\x00J\xff\xff\xff\xff."
    ),
    "8dbb56e0-5370-4062-bdb1-2ac510711b47": pickle.loads(
        b"\x80\x04\x95\x08\x00\x00\x00\x00\x00\x00\x00\x8c\x04jpeg\x94."
    ),
    "a208f3c6-cfe7-4420-bd35-b90de660c0ab": pickle.loads(
        b"\x80\x04\x95\x15\x00\x00\x00\x00\x00\x00\x00\x8c\x11least restrictive\x94."
    ),
    "9a6c0db2-046f-4dc4-a35c-6c6276d1e9ef": pickle.loads(
        b"\x80\x04\x95(\x00\x00\x00\x00\x00\x00\x00\x8c$b5a420a4-8a59-46ad-917c-bbede1977345\x94."
    ),
    "46375d4f-e1ad-4549-af43-538523257502": pickle.loads(
        b"\x80\x04\x95\xe6\x01\x00\x00\x00\x00\x00\x00}\x94(\x8c\x02id\x94\x8c$b0fee5ba-5c4b-46f8-b190-f915a6860618\x94\x8c\x06status\x94\x8c\x05Ready\x94\x8c\x06result\x94}\x94(\x8c\x06sample\x94\x8c\xe9https://bfldeliverysc.blob.core.windows.net/results/65/43147278113a26/78113a26fe744c78a0bcb3d6f7079cdb/sample.jpeg?se=2025-11-18T00%3A33%3A52Z&sp=r&sv=2024-11-04&sr=b&rsct=image/jpeg&sig=LGW5xXZKIesHnWdf86hh4gCs1olDXD/nzz0tzDFgfxw%3D\x94\x8c\x06prompt\x94\x8c*a rough production sketch of a\n\ncoffee mug\x94\x8c\x04seed\x94J\xec8\xe8y\x8c\nstart_time\x94GA\xdaF\xef%r\x1a\x8e\x8c\x08end_time\x94GA\xdaF\xef&!\x03{\x8c\x08duration\x94G@\x05\xdd\x1d\xa0\x00\x00\x00u\x8c\x08progress\x94N\x8c\x07details\x94N\x8c\x07preview\x94Nu."
    ),
    "3b7f625b-d44c-42bc-abc5-9998b2b2f651": pickle.loads(
        b"\x80\x04\x95\x8a\x01\x00\x00\x00\x00\x00\x00\x8c%griptape.artifacts.image_url_artifact\x94\x8c\x10ImageUrlArtifact\x94\x93\x94)\x81\x94}\x94(\x8c\x04type\x94\x8c\x10ImageUrlArtifact\x94\x8c\x0bmodule_name\x94\x8c%griptape.artifacts.image_url_artifact\x94\x8c\x02id\x94\x8c 9df65b94a0b74ad3b1bdf91d65c8b8a0\x94\x8c\treference\x94N\x8c\x04meta\x94}\x94\x8c\x04name\x94\x8c\x19flux_image_1763425439.jpg\x94\x8c\x16encoding_error_handler\x94\x8c\x06strict\x94\x8c\x08encoding\x94\x8c\x05utf-8\x94\x8c\x05value\x94\x8cShttp://localhost:8124/workspace/static_files/flux_image_1763425439.jpg?t=1763425440\x94ub."
    ),
    "6f275bad-e844-4c94-8055-0efa963db3c2": pickle.loads(b"\x80\x04\x88."),
    "f0f5060e-07af-43a4-9c09-82aa66854709": pickle.loads(
        b"\x80\x04\x95H\x00\x00\x00\x00\x00\x00\x00\x8cDImage generated successfully and saved as flux_image_1763425439.jpg.\x94."
    ),
    "c8c83190-e339-4b1b-a19a-f830b605563e": pickle.loads(
        b"\x80\x04\x95\x08\x00\x00\x00\x00\x00\x00\x00\x8c\x04Prop\x94."
    ),
    "36ec5401-d5a5-4f00-aef6-fc4d87e141e0": pickle.loads(
        b"\x80\x04\x95*\x00\x00\x00\x00\x00\x00\x00\x8c&an incredibly piping hot mug of coffee\x94."
    ),
    "afb6ad84-7967-4f85-8c75-3fc79825f726": pickle.loads(
        b"\x80\x04\x95)\x00\x00\x00\x00\x00\x00\x00\x8c%Film VFX - Full CG Shot w/o Character\x94."
    ),
    "a4ec59f9-35d8-46dc-a19a-f7d30d13bbc0": pickle.loads(b"\x80\x04\x95\x04\x00\x00\x00\x00\x00\x00\x00M\xa4\t."),
    "8faac5c5-8c2a-492f-8a7b-43d5926f8036": pickle.loads(
        b"\x80\x04\x95?\x00\x00\x00\x00\x00\x00\x00\x8c;https://griptape-ai.shotgrid.autodesk.com/detail/Asset/2468\x94."
    ),
    "e5d46b0d-5329-4ac8-b86f-4863564669ae": pickle.loads(
        b'\x80\x04\x95\xd7\x0b\x00\x00\x00\x00\x00\x00}\x94(\x8c\x04type\x94\x8c\x05Asset\x94\x8c\nattributes\x94}\x94(\x8c\rsg_regenerate\x94\x89\x8c\x06step_0\x94N\x8c\x13cached_display_name\x94\x8c\ncoffee mug\x94\x8c\x0ffilmstrip_image\x94N\x8c\x0fimage_blur_hash\x94N\x8c\x07sg_keep\x94\x89\x8c\x0csg_outsource\x94\x89\x8c\x11sg_creative_brief\x94N\x8c\x07step_13\x94N\x8c\x08step_129\x94N\x8c\x08step_137\x94N\x8c\x07step_14\x94N\x8c\x07step_15\x94N\x8c\x07step_16\x94N\x8c\x07step_32\x94N\x8c\x08step_130\x94N\x8c\x08step_131\x94N\x8c\x08step_132\x94N\x8c\x10open_notes_count\x94K\x00\x8c\nupdated_at\x94\x8c\x142025-11-18T00:24:13Z\x94\x8c\rsg_asset_type\x94\x8c\x04Prop\x94\x8c\x04code\x94\x8c\ncoffee mug\x94\x8c\x0esg_status_list\x94\x8c\x03wtg\x94\x8c\x0bdescription\x94\x8c&an incredibly piping hot mug of coffee\x94\x8c\x05image\x94\x8cWhttps://griptape-ai.shotgrid.autodesk.com/images/status/transient/thumbnail_pending.png\x94\x8c\ncreated_at\x94\x8c\x142025-11-18T00:24:03Z\x94u\x8c\rrelationships\x94}\x94(\x8c\x0bmocap_takes\x94}\x94(\x8c\x04data\x94]\x94\x8c\x05links\x94}\x94\x8c\x04self\x94\x8c4/api/v1/entity/assets/2468/relationships/mocap_takes\x94su\x8c\rtask_template\x94}\x94(h+}\x94(\x8c\x02id\x94K+\x8c\x04name\x94\x8c%Film VFX - Full CG Shot w/o Character\x94h\x01\x8c\x0cTaskTemplate\x94uh-}\x94(h/\x8c6/api/v1/entity/assets/2468/relationships/task_template\x94\x8c\x07related\x94\x8c /api/v1/entity/task_templates/43\x94uu\x8c\x0eaddressings_cc\x94}\x94(h+]\x94h-}\x94h/\x8c7/api/v1/entity/assets/2468/relationships/addressings_cc\x94su\x8c\x0bsg_versions\x94}\x94(h+]\x94h-}\x94h/\x8c4/api/v1/entity/assets/2468/relationships/sg_versions\x94su\x8c\x12sg_published_files\x94}\x94(h+]\x94h-}\x94h/\x8c;/api/v1/entity/assets/2468/relationships/sg_published_files\x94su\x8c\x08episodes\x94}\x94(h+]\x94h-}\x94h/\x8c1/api/v1/entity/assets/2468/relationships/episodes\x94su\x8c\x06levels\x94}\x94(h+]\x94h-}\x94h/\x8c//api/v1/entity/assets/2468/relationships/levels\x94su\x8c\x13image_source_entity\x94}\x94(h+}\x94(h\x01\x8c\x05Asset\x94h4M\xa4\th5\x8c\ncoffee mug\x94uh-}\x94(h/\x8c</api/v1/entity/assets/2468/relationships/image_source_entity\x94h:\x8c\x1a/api/v1/entity/assets/2468\x94uu\x8c\x10sg_vendor_groups\x94}\x94(h+]\x94h-}\x94h/\x8c9/api/v1/entity/assets/2468/relationships/sg_vendor_groups\x94su\x8c\x0flinked_projects\x94}\x94(h+]\x94h-}\x94h/\x8c8/api/v1/entity/assets/2468/relationships/linked_projects\x94su\x8c\x05notes\x94}\x94(h+]\x94h-}\x94h/\x8c./api/v1/entity/assets/2468/relationships/notes\x94su\x8c\nopen_notes\x94}\x94(h+]\x94h-}\x94h/\x8c3/api/v1/entity/assets/2468/relationships/open_notes\x94su\x8c\tsequences\x94}\x94(h+]\x94h-}\x94h/\x8c2/api/v1/entity/assets/2468/relationships/sequences\x94su\x8c\x07parents\x94}\x94(h+]\x94h-}\x94h/\x8c0/api/v1/entity/assets/2468/relationships/parents\x94su\x8c\x07project\x94}\x94(h+}\x94(h4K\xe2h5\x8c\x10jasonLovesCoffee\x94h\x01\x8c\x07Project\x94uh-}\x94(h/\x8c0/api/v1/entity/assets/2468/relationships/project\x94h:\x8c\x1b/api/v1/entity/projects/226\x94uu\x8c\x06assets\x94}\x94(h+]\x94h-}\x94h/\x8c//api/v1/entity/assets/2468/relationships/assets\x94su\x8c\ncreated_by\x94}\x94(h+}\x94(h4K\xa4h5\x8c\x07gtn 1.0\x94h\x01\x8c\x07ApiUser\x94uh-}\x94(h/\x8c3/api/v1/entity/assets/2468/relationships/created_by\x94h:\x8c\x1c/api/v1/entity/api_users/164\x94uu\x8c\nupdated_by\x94}\x94(h+}\x94(h4K\xa4h5\x8c\x07gtn 1.0\x94h\x01\x8c\x07ApiUser\x94uh-}\x94(h/\x8c3/api/v1/entity/assets/2468/relationships/updated_by\x94h:\x8c\x1c/api/v1/entity/api_users/164\x94uu\x8c\x04tags\x94}\x94(h+]\x94h-}\x94h/\x8c-/api/v1/entity/assets/2468/relationships/tags\x94su\x8c\x05tasks\x94}\x94(h+]\x94(}\x94(h4M\x1e\x1eh5\x8c\tAnimation\x94h\x01\x8c\x04Task\x94u}\x94(h4M"\x1eh5\x8c\x04Comp\x94h\x01\x8c\x04Task\x94u}\x94(h4M#\x1eh5\x8c\x02FX\x94h\x01\x8c\x04Task\x94u}\x94(h4M \x1eh5\x8c\x06Layout\x94h\x01\x8c\x04Task\x94u}\x94(h4M!\x1eh5\x8c\x08Lighting\x94h\x01\x8c\x04Task\x94u}\x94(h4M\x1f\x1eh5\x8c\x0cPlate Online\x94h\x01\x8c\x04Task\x94u}\x94(h4M\x1d\x1eh5\x8c\x04Roto\x94h\x01\x8c\x04Task\x94u}\x94(h4M\x1c\x1eh5\x8c\x08Tracking\x94h\x01\x8c\x04Task\x94ueh-}\x94h/\x8c./api/v1/entity/assets/2468/relationships/tasks\x94su\x8c\x05shots\x94}\x94(h+]\x94h-}\x94h/\x8c./api/v1/entity/assets/2468/relationships/shots\x94suuh4M\xa4\th-}\x94h/\x8c\x1a/api/v1/entity/assets/2468\x94su.'
    ),
    "dc45cef0-b7bd-4de1-9d45-35f8041de7e3": pickle.loads(
        b"\x80\x04\x95w\x00\x00\x00\x00\x00\x00\x00\x8cs## Review the Asset\n\nOnce the asset is created, you can go and check it out by reviewing the generated `asset_url`.\x94."
    ),
    "d6c5fc14-23ce-4e37-9d0d-83b50cddf481": pickle.loads(
        b"\x80\x04\x95\x85\x00\x00\x00\x00\x00\x00\x00\x8c\x81## Listing Projects\n\nIt all starts with getting a list of your existing projects, so you can be sure you've got one to work with.\x94."
    ),
    "76b86360-8c12-4358-b015-8ac376f851c8": pickle.loads(
        b"\x80\x04\x952\x00\x00\x00\x00\x00\x00\x00\x8c.pitcher of water\nvase\nold shoe\npineapple phone\x94."
    ),
    "e580eedf-f42e-4792-b105-447a91816857": pickle.loads(
        b"\x80\x04\x95\t\x00\x00\x00\x00\x00\x00\x00\x8c\x05split\x94."
    ),
    "d5ce5408-1cab-41c1-b3f6-83a8c9edea0d": pickle.loads(
        b"\x80\x04\x95\x0c\x00\x00\x00\x00\x00\x00\x00\x8c\x08newlines\x94."
    ),
    "719bdb4d-b0dd-497d-9448-a30df3e44fe5": pickle.loads(
        b"\x80\x04\x95\x11\x00\x00\x00\x00\x00\x00\x00]\x94\x8c\ncoffee mug\x94a."
    ),
    "d4cb2615-c977-4467-acaa-454b5a224b8e": pickle.loads(b"\x80\x04K\x00."),
    "8cb0aa39-391e-42b9-a5ac-01feefc7d300": pickle.loads(b"\x80\x04\x95\x04\x00\x00\x00\x00\x00\x00\x00\x8c\x00\x94."),
    "10ce1eb6-7869-4a33-9f03-4909e4a5b80b": pickle.loads(
        b"\x80\x04\x95\x16\x00\x00\x00\x00\x00\x00\x00\x8c\x12Games - Small Prop\x94."
    ),
    "50fbf820-ca67-4cda-a2df-facb9679961c": pickle.loads(
        b"\x80\x04\x95\x8a\x01\x00\x00\x00\x00\x00\x00\x8c%griptape.artifacts.image_url_artifact\x94\x8c\x10ImageUrlArtifact\x94\x93\x94)\x81\x94}\x94(\x8c\x04type\x94\x8c\x10ImageUrlArtifact\x94\x8c\x0bmodule_name\x94\x8c%griptape.artifacts.image_url_artifact\x94\x8c\x02id\x94\x8c 9df65b94a0b74ad3b1bdf91d65c8b8a0\x94\x8c\treference\x94N\x8c\x04meta\x94}\x94\x8c\x04name\x94\x8c\x19flux_image_1763425439.jpg\x94\x8c\x16encoding_error_handler\x94\x8c\x06strict\x94\x8c\x08encoding\x94\x8c\x05utf-8\x94\x8c\x05value\x94\x8cShttp://localhost:8124/workspace/static_files/flux_image_1763425439.jpg?t=1763425440\x94ub."
    ),
    "658c1944-082c-443c-8cb1-1c42cc150a6f": pickle.loads(
        b'\x80\x04\x95\xd7\x0b\x00\x00\x00\x00\x00\x00}\x94(\x8c\x04type\x94\x8c\x05Asset\x94\x8c\nattributes\x94}\x94(\x8c\rsg_regenerate\x94\x89\x8c\x06step_0\x94N\x8c\x13cached_display_name\x94\x8c\ncoffee mug\x94\x8c\x0ffilmstrip_image\x94N\x8c\x0fimage_blur_hash\x94N\x8c\x07sg_keep\x94\x89\x8c\x0csg_outsource\x94\x89\x8c\x11sg_creative_brief\x94N\x8c\x07step_13\x94N\x8c\x08step_129\x94N\x8c\x08step_137\x94N\x8c\x07step_14\x94N\x8c\x07step_15\x94N\x8c\x07step_16\x94N\x8c\x07step_32\x94N\x8c\x08step_130\x94N\x8c\x08step_131\x94N\x8c\x08step_132\x94N\x8c\x10open_notes_count\x94K\x00\x8c\nupdated_at\x94\x8c\x142025-11-18T00:24:13Z\x94\x8c\rsg_asset_type\x94\x8c\x04Prop\x94\x8c\x04code\x94\x8c\ncoffee mug\x94\x8c\x0esg_status_list\x94\x8c\x03wtg\x94\x8c\x0bdescription\x94\x8c&an incredibly piping hot mug of coffee\x94\x8c\x05image\x94\x8cWhttps://griptape-ai.shotgrid.autodesk.com/images/status/transient/thumbnail_pending.png\x94\x8c\ncreated_at\x94\x8c\x142025-11-18T00:24:03Z\x94u\x8c\rrelationships\x94}\x94(\x8c\x0bmocap_takes\x94}\x94(\x8c\x04data\x94]\x94\x8c\x05links\x94}\x94\x8c\x04self\x94\x8c4/api/v1/entity/assets/2468/relationships/mocap_takes\x94su\x8c\rtask_template\x94}\x94(h+}\x94(\x8c\x02id\x94K+\x8c\x04name\x94\x8c%Film VFX - Full CG Shot w/o Character\x94h\x01\x8c\x0cTaskTemplate\x94uh-}\x94(h/\x8c6/api/v1/entity/assets/2468/relationships/task_template\x94\x8c\x07related\x94\x8c /api/v1/entity/task_templates/43\x94uu\x8c\x0eaddressings_cc\x94}\x94(h+]\x94h-}\x94h/\x8c7/api/v1/entity/assets/2468/relationships/addressings_cc\x94su\x8c\x0bsg_versions\x94}\x94(h+]\x94h-}\x94h/\x8c4/api/v1/entity/assets/2468/relationships/sg_versions\x94su\x8c\x12sg_published_files\x94}\x94(h+]\x94h-}\x94h/\x8c;/api/v1/entity/assets/2468/relationships/sg_published_files\x94su\x8c\x08episodes\x94}\x94(h+]\x94h-}\x94h/\x8c1/api/v1/entity/assets/2468/relationships/episodes\x94su\x8c\x06levels\x94}\x94(h+]\x94h-}\x94h/\x8c//api/v1/entity/assets/2468/relationships/levels\x94su\x8c\x13image_source_entity\x94}\x94(h+}\x94(h\x01\x8c\x05Asset\x94h4M\xa4\th5\x8c\ncoffee mug\x94uh-}\x94(h/\x8c</api/v1/entity/assets/2468/relationships/image_source_entity\x94h:\x8c\x1a/api/v1/entity/assets/2468\x94uu\x8c\x10sg_vendor_groups\x94}\x94(h+]\x94h-}\x94h/\x8c9/api/v1/entity/assets/2468/relationships/sg_vendor_groups\x94su\x8c\x0flinked_projects\x94}\x94(h+]\x94h-}\x94h/\x8c8/api/v1/entity/assets/2468/relationships/linked_projects\x94su\x8c\x05notes\x94}\x94(h+]\x94h-}\x94h/\x8c./api/v1/entity/assets/2468/relationships/notes\x94su\x8c\nopen_notes\x94}\x94(h+]\x94h-}\x94h/\x8c3/api/v1/entity/assets/2468/relationships/open_notes\x94su\x8c\tsequences\x94}\x94(h+]\x94h-}\x94h/\x8c2/api/v1/entity/assets/2468/relationships/sequences\x94su\x8c\x07parents\x94}\x94(h+]\x94h-}\x94h/\x8c0/api/v1/entity/assets/2468/relationships/parents\x94su\x8c\x07project\x94}\x94(h+}\x94(h4K\xe2h5\x8c\x10jasonLovesCoffee\x94h\x01\x8c\x07Project\x94uh-}\x94(h/\x8c0/api/v1/entity/assets/2468/relationships/project\x94h:\x8c\x1b/api/v1/entity/projects/226\x94uu\x8c\x06assets\x94}\x94(h+]\x94h-}\x94h/\x8c//api/v1/entity/assets/2468/relationships/assets\x94su\x8c\ncreated_by\x94}\x94(h+}\x94(h4K\xa4h5\x8c\x07gtn 1.0\x94h\x01\x8c\x07ApiUser\x94uh-}\x94(h/\x8c3/api/v1/entity/assets/2468/relationships/created_by\x94h:\x8c\x1c/api/v1/entity/api_users/164\x94uu\x8c\nupdated_by\x94}\x94(h+}\x94(h4K\xa4h5\x8c\x07gtn 1.0\x94h\x01\x8c\x07ApiUser\x94uh-}\x94(h/\x8c3/api/v1/entity/assets/2468/relationships/updated_by\x94h:\x8c\x1c/api/v1/entity/api_users/164\x94uu\x8c\x04tags\x94}\x94(h+]\x94h-}\x94h/\x8c-/api/v1/entity/assets/2468/relationships/tags\x94su\x8c\x05tasks\x94}\x94(h+]\x94(}\x94(h4M\x1e\x1eh5\x8c\tAnimation\x94h\x01\x8c\x04Task\x94u}\x94(h4M"\x1eh5\x8c\x04Comp\x94h\x01\x8c\x04Task\x94u}\x94(h4M#\x1eh5\x8c\x02FX\x94h\x01\x8c\x04Task\x94u}\x94(h4M \x1eh5\x8c\x06Layout\x94h\x01\x8c\x04Task\x94u}\x94(h4M!\x1eh5\x8c\x08Lighting\x94h\x01\x8c\x04Task\x94u}\x94(h4M\x1f\x1eh5\x8c\x0cPlate Online\x94h\x01\x8c\x04Task\x94u}\x94(h4M\x1d\x1eh5\x8c\x04Roto\x94h\x01\x8c\x04Task\x94u}\x94(h4M\x1c\x1eh5\x8c\x08Tracking\x94h\x01\x8c\x04Task\x94ueh-}\x94h/\x8c./api/v1/entity/assets/2468/relationships/tasks\x94su\x8c\x05shots\x94}\x94(h+]\x94h-}\x94h/\x8c./api/v1/entity/assets/2468/relationships/shots\x94suuh4M\xa4\th-}\x94h/\x8c\x1a/api/v1/entity/assets/2468\x94su.'
    ),
    "d1c7c00b-bd78-44ab-9a22-36213f8066dd": pickle.loads(
        b"\x80\x04\x95\xe6\x01\x00\x00\x00\x00\x00\x00}\x94(\x8c\x02id\x94\x8c$b0fee5ba-5c4b-46f8-b190-f915a6860618\x94\x8c\x06status\x94\x8c\x05Ready\x94\x8c\x06result\x94}\x94(\x8c\x06sample\x94\x8c\xe9https://bfldeliverysc.blob.core.windows.net/results/65/43147278113a26/78113a26fe744c78a0bcb3d6f7079cdb/sample.jpeg?se=2025-11-18T00%3A33%3A52Z&sp=r&sv=2024-11-04&sr=b&rsct=image/jpeg&sig=LGW5xXZKIesHnWdf86hh4gCs1olDXD/nzz0tzDFgfxw%3D\x94\x8c\x06prompt\x94\x8c*a rough production sketch of a\n\ncoffee mug\x94\x8c\x04seed\x94J\xec8\xe8y\x8c\nstart_time\x94GA\xdaF\xef%r\x1a\x8e\x8c\x08end_time\x94GA\xdaF\xef&!\x03{\x8c\x08duration\x94G@\x05\xdd\x1d\xa0\x00\x00\x00u\x8c\x08progress\x94N\x8c\x07details\x94N\x8c\x07preview\x94Nu."
    ),
    "b8cd49bf-4802-4d1a-ac47-3b1f05281073": pickle.loads(
        b"\x80\x04\x95\x1c\x00\x00\x00\x00\x00\x00\x00\x8c\x18claude-sonnet-4-20250514\x94."
    ),
    "79abc8c0-3263-453c-83ca-d59a754908ed": pickle.loads(b"\x80\x04}\x94."),
    "746a8fa8-bed7-4647-98fc-49cf2af29cd2": pickle.loads(
        b"\x80\x04\x95\\\x00\x00\x00\x00\x00\x00\x00\x8cXcreate a concise creative description of the following, and output only the description:\x94."
    ),
    "ae78389b-1186-4fc1-b7b4-31b76386282f": pickle.loads(b"\x80\x04]\x94."),
    "96886147-549f-4ca1-864c-a8c3ef972cf3": pickle.loads(b"\x80\x04]\x94."),
    "676bb48e-f5b0-4408-99a2-46ef2bdef4f2": pickle.loads(
        b"\x80\x04\x95o\x00\x00\x00\x00\x00\x00\x00\x8ck## Create Multiple Assets\n\nNow that you can create a single asset - let's look at creating multiple assets.\x94."
    ),
    "1415e3ea-b2d6-4692-b48c-78893dc4e6d0": pickle.loads(
        b"\x80\x04\x95`\x00\x00\x00\x00\x00\x00\x00\x8c\\## Make a list\n\nStart with a text input node of a list of assets you'd like.\n\nOne each line.\x94."
    ),
    "4da5e7a8-43a6-40f0-9ce9-9136dedd1fb3": pickle.loads(
        b"\x80\x04\x95\xc1\x00\x00\x00\x00\x00\x00\x00\x8c\xbd## Split the list\n\nThe `Split Text` node will take an input and split it into individual items.\n\nYou can then iterate on this list of items, sort it, reorder, etc.\n\nLists are very powerful!\x94."
    ),
    "ef3d113d-5dcd-498f-9a30-80dc7bcb1594": pickle.loads(
        b"\x80\x04\x95d\x00\x00\x00\x00\x00\x00\x00\x8c`## For each item in the list\n\nThis is a loop - we'll do these nodes for each item in the list...\x94."
    ),
    "cbf867b5-9a43-4060-a31b-222a324c0d0f": pickle.loads(
        b"\x80\x04\x95Y\x00\x00\x00\x00\x00\x00\x00\x8cU## Create a Description\n\nFor each item, we'll use an agent to generate a description.\x94."
    ),
    "eb7fe00d-e8b2-471d-966b-12646ee5b842": pickle.loads(
        b"\x80\x04\x95\xa4\x00\x00\x00\x00\x00\x00\x00\x8c\xa0## Create a Prompt\n\nUse the `Merge Texts` node to combine a prompt style, the name, and the description to create a prompt to give to the image generation node.\x94."
    ),
    "a906dd37-556c-4770-9f5e-a909870eb8b3": pickle.loads(
        b"\x80\x04\x957\x00\x00\x00\x00\x00\x00\x00\x8c3## Create an Image\n\nGenerate an image for the asset\x94."
    ),
    "cced66f9-f9cd-4b40-95c7-14ba383e8251": pickle.loads(
        b"\x80\x04\x95N\x00\x00\x00\x00\x00\x00\x00\x8cJ## Create an Asset\n\nCreate the asset with the name, description, and image\x94."
    ),
    "bef92170-3c3c-4f08-adc5-fc3c7c22728e": pickle.loads(
        b"\x80\x04\x95Z\x00\x00\x00\x00\x00\x00\x00\x8cV## Display the results\n\nWe collected the URL of the asset created. \n\nDisplay the list.\x94."
    ),
    "3bf276b0-07fc-4338-8c76-9b8336f0d649": pickle.loads(
        b"\x80\x04\x95\x97\x00\x00\x00\x00\x00\x00\x00\x8c\x93## Loop Finished\n\nThis is the end of the loop. When finished, collect the results in the `new_item_to_add` parameter, and go back to the beginning.\x94."
    ),
    "c985ffc0-ffec-4332-97b0-e22cf7ec0532": pickle.loads(
        b"\x80\x04\x95\x1a\x00\x00\x00\x00\x00\x00\x00\x8c\x16Reload to see projects\x94."
    ),
    "b3059f79-de83-48ab-810c-c5a74139c333": pickle.loads(b"\x80\x04}\x94."),
}

"# Create the Flow, then do work within it as context."

flow0_name = GriptapeNodes.handle_request(
    CreateFlowRequest(parent_flow_name=None, flow_name="ControlFlow_1", set_as_new_context=False, metadata={})
).flow_name

with GriptapeNodes.ContextManager().flow(flow0_name):
    node0_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_2",
            metadata={
                "position": {"x": 2553.2298952798324, "y": 283.6338795264069},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 1227, "height": 304},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node1_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_4",
            metadata={
                "position": {"x": 4733.514085760192, "y": 293.6338795264069},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 621, "height": 284},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node2_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="MergeTexts",
            specific_library_name="Griptape Nodes Library",
            node_name="Merge Texts",
            metadata={
                "position": {"x": 5644.093509776407, "y": 1138.5762526221615},
                "tempId": "placing-1763424778811-wykk5h",
                "library_node_metadata": NodeMetadata(
                    category="text",
                    description="MergeTexts node",
                    display_name="Merge Texts",
                    tags=None,
                    icon="merge",
                    color=None,
                    group="merge",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "MergeTexts",
                "showaddparameter": False,
                "size": {"width": 600, "height": 500},
                "category": "text",
            },
            resolution="resolved",
            initial_setup=True,
        )
    ).node_name
    node3_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="FluxImageGeneration",
            specific_library_name="Griptape Nodes Library",
            node_name="Flux Image Generation",
            metadata={
                "library_node_metadata": NodeMetadata(
                    category="image",
                    description="Generate images using FLUX.1 models via Griptape model proxy",
                    display_name="FLUX.1 Image Generation",
                    tags=None,
                    icon="Zap",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "FluxImageGeneration",
                "position": {"x": 6279.385692620228, "y": 1122.320460227958},
                "size": {"width": 768, "height": 1174},
                "showaddparameter": False,
                "category": "image",
            },
            resolution="resolved",
            initial_setup=True,
        )
    ).node_name
    node4_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="FlowCreateAsset",
            specific_library_name="Flow Production Tracking Library",
            node_name="Create Asset",
            metadata={
                "position": {"x": 7367.7036457951845, "y": 621.0155514441952},
                "tempId": "placing-1763425097548-vqmvl7",
                "library_node_metadata": NodeMetadata(
                    category="autodesk",
                    description="Griptape Node that creates a new asset in a ShotGrid project.",
                    display_name="Create Asset",
                    tags=None,
                    icon=None,
                    color=None,
                    group="assets",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Flow Production Tracking Library",
                "node_type": "FlowCreateAsset",
                "showaddparameter": False,
                "size": {"width": 649, "height": 917},
                "category": "autodesk",
            },
            initial_setup=True,
        )
    ).node_name
    with GriptapeNodes.ContextManager().node(node4_name):
        GriptapeNodes.handle_request(
            AlterParameterDetailsRequest(
                parameter_name="task_template_id",
                ui_options={
                    "simple_dropdown": [
                        "Games - Small Prop",
                        "Games - Medium Prop",
                        "Games - Large Prop",
                        "Film VFX - Full CG Shot w/o Character",
                        "GenAI - Prop Asset",
                    ],
                    "show_search": True,
                    "search_filter": "",
                },
                initial_setup=True,
            )
        )
    node5_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="TextInput",
            specific_library_name="Griptape Nodes Library",
            node_name="asset name",
            metadata={
                "position": {"x": 4733.514085760192, "y": 621.0155514441952},
                "tempId": "placing-1763424560930-irxvfa",
                "library_node_metadata": NodeMetadata(
                    category="text",
                    description="TextInput node",
                    display_name="Text Input",
                    tags=None,
                    icon="text-cursor",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "TextInput",
                "showaddparameter": False,
                "size": {"width": 600, "height": 189},
                "category": "text",
            },
            resolution="resolved",
            initial_setup=True,
        )
    ).node_name
    node6_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="TextInput",
            specific_library_name="Griptape Nodes Library",
            node_name="asset description",
            metadata={
                "position": {"x": 4733.514085760192, "y": 830.0237300563861},
                "tempId": "placing-1763424560930-irxvfa",
                "library_node_metadata": NodeMetadata(
                    category="text",
                    description="TextInput node",
                    display_name="Text Input",
                    tags=None,
                    icon="text-cursor",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "TextInput",
                "showaddparameter": False,
                "size": {"width": 600, "height": 189},
                "category": "text",
            },
            resolution="resolved",
            initial_setup=True,
        )
    ).node_name
    node7_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_5",
            metadata={
                "position": {"x": 8073.037015770664, "y": 1294.062251115372},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 627, "height": 213},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node8_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_1",
            metadata={
                "position": {"x": 2553.2298952798324, "y": 621.0155514441952},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 600, "height": 301},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node9_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="TextInput",
            specific_library_name="Griptape Nodes Library",
            node_name="a list of assets",
            metadata={
                "position": {"x": 4865.2377283349515, "y": 3635.922623902077},
                "tempId": "placing-1763424560930-irxvfa",
                "library_node_metadata": NodeMetadata(
                    category="text",
                    description="TextInput node",
                    display_name="Text Input",
                    tags=None,
                    icon="text-cursor",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "TextInput",
                "showaddparameter": False,
                "size": {"width": 604, "height": 318},
                "category": "text",
            },
            initial_setup=True,
        )
    ).node_name
    node10_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="SplitText",
            specific_library_name="Griptape Nodes Library",
            node_name="Split Text",
            metadata={
                "position": {"x": 5736.440941826581, "y": 3635.922623902077},
                "tempId": "placing-1763431586838-7bsxt",
                "library_node_metadata": NodeMetadata(
                    category="lists",
                    description="Takes a text string and splits it into a list based on a specified delimiter.",
                    display_name="Split Text",
                    tags=None,
                    icon="scissors",
                    color=None,
                    group="edit",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "SplitText",
                "showaddparameter": False,
                "size": {"width": 600, "height": 456},
                "category": "lists",
            },
            initial_setup=True,
        )
    ).node_name
    node11_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="ForEachStartNode",
            specific_library_name="Griptape Nodes Library",
            node_name="ForEach Start",
            metadata={
                "position": {"x": 6679.599727318205, "y": 3570.4062109313495},
                "tempId": "placing-1763431594871-tz3hh",
                "library_node_metadata": NodeMetadata(
                    category="execution_flow",
                    description="Start node for iterating through a list of items and running a flow for each one",
                    display_name="ForEach Start",
                    tags=None,
                    icon="list-start",
                    color=None,
                    group="iteration",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "ForEachStartNode",
                "showaddparameter": False,
                "size": {"width": 640, "height": 624},
                "category": "execution_flow",
            },
            initial_setup=True,
        )
    ).node_name
    node12_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="ForEachEndNode",
            specific_library_name="Griptape Nodes Library",
            node_name="ForEach End",
            metadata={
                "position": {"x": 11295.18220290928, "y": 3485.936718128499},
                "library_node_metadata": NodeMetadata(
                    category="execution_flow",
                    description="End node that completes a loop iteration and connects back to the ForEachStartNode",
                    display_name="ForEach End",
                    tags=None,
                    icon="list-end",
                    color=None,
                    group="iteration",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "ForEachEndNode",
                "showaddparameter": False,
                "size": {"width": 600, "height": 372},
                "category": "execution_flow",
            },
            initial_setup=True,
        )
    ).node_name
    node13_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="FlowCreateAsset",
            specific_library_name="Flow Production Tracking Library",
            node_name="Create Asset_1",
            metadata={
                "position": {"x": 10552.915575160308, "y": 3672.81945509814},
                "tempId": "placing-1763425097548-vqmvl7",
                "library_node_metadata": NodeMetadata(
                    category="autodesk",
                    description="Griptape Node that creates a new asset in a ShotGrid project.",
                    display_name="Create Asset",
                    tags=None,
                    icon=None,
                    color=None,
                    group="assets",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Flow Production Tracking Library",
                "node_type": "FlowCreateAsset",
                "showaddparameter": False,
                "size": {"width": 649, "height": 917},
                "category": "autodesk",
            },
            initial_setup=True,
        )
    ).node_name
    with GriptapeNodes.ContextManager().node(node13_name):
        GriptapeNodes.handle_request(
            AlterParameterDetailsRequest(
                parameter_name="task_template_id",
                ui_options={
                    "simple_dropdown": [
                        "Games - Small Prop",
                        "Games - Medium Prop",
                        "Games - Large Prop",
                        "Film VFX - Full CG Shot w/o Character",
                        "GenAI - Prop Asset",
                    ],
                    "show_search": True,
                    "search_filter": "",
                },
                initial_setup=True,
            )
        )
    node14_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="MergeTexts",
            specific_library_name="Griptape Nodes Library",
            node_name="Merge Texts_1",
            metadata={
                "position": {"x": 8463.717975392006, "y": 3975.829760806183},
                "tempId": "placing-1763424778811-wykk5h",
                "library_node_metadata": NodeMetadata(
                    category="text",
                    description="MergeTexts node",
                    display_name="Merge Texts",
                    tags=None,
                    icon="merge",
                    color=None,
                    group="merge",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "MergeTexts",
                "showaddparameter": False,
                "size": {"width": 600, "height": 500},
                "category": "text",
            },
            initial_setup=True,
        )
    ).node_name
    node15_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="FluxImageGeneration",
            specific_library_name="Griptape Nodes Library",
            node_name="Flux Image Generation_1",
            metadata={
                "library_node_metadata": NodeMetadata(
                    category="image",
                    description="Generate images using FLUX.1 models via Griptape model proxy",
                    display_name="FLUX.1 Image Generation",
                    tags=None,
                    icon="Zap",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "FluxImageGeneration",
                "position": {"x": 9573.701512180003, "y": 3975.829760806183},
                "size": {"width": 768, "height": 1174},
                "showaddparameter": False,
                "category": "image",
            },
            initial_setup=True,
        )
    ).node_name
    node16_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Agent",
            specific_library_name="Griptape Nodes Library",
            node_name="Agent",
            metadata={
                "position": {"x": 7496.586806562884, "y": 3975.829760806183},
                "tempId": "placing-1763431694452-m08di9",
                "library_node_metadata": NodeMetadata(
                    category="agents",
                    description="Creates an AI agent with conversation memory and the ability to use tools",
                    display_name="Agent",
                    tags=None,
                    icon=None,
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Agent",
                "showaddparameter": False,
                "size": {"width": 600, "height": 864},
                "category": "agents",
            },
            initial_setup=True,
        )
    ).node_name
    with GriptapeNodes.ContextManager().node(node16_name):
        GriptapeNodes.handle_request(
            AlterParameterDetailsRequest(
                parameter_name="additional_context", mode_allowed_property=False, initial_setup=True
            )
        )
    node17_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="DisplayList",
            specific_library_name="Griptape Nodes Library",
            node_name="Display List",
            metadata={
                "position": {"x": 12164.966143416219, "y": 3508.036484286209},
                "tempId": "placing-1763431773695-ci3es",
                "library_node_metadata": NodeMetadata(
                    category="lists",
                    description="Takes a list input and creates output parameters for each item in the list",
                    display_name="Display List",
                    tags=None,
                    icon=None,
                    color=None,
                    group="display",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "DisplayList",
                "showaddparameter": False,
                "size": {"width": 600, "height": 280},
                "category": "lists",
            },
            initial_setup=True,
        )
    ).node_name
    node18_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_3",
            metadata={
                "position": {"x": 4213.8400369263, "y": 2997.059658821986},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 621, "height": 284},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node19_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_7",
            metadata={
                "position": {"x": 4865.2377283349515, "y": 3320.1468316086703},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 600, "height": 284},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node20_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_8",
            metadata={
                "position": {"x": 5736.440941826581, "y": 3320.1468316086703},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 600, "height": 284},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node21_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_9",
            metadata={
                "position": {"x": 6679.599727318205, "y": 3135.7023450901256},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 4502, "height": 268},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node22_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_10",
            metadata={
                "position": {"x": 7496.586806562884, "y": 3726.8337734423917},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 600, "height": 205},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node23_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_11",
            metadata={
                "position": {"x": 8453.717975392006, "y": 3726.8337734423917},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 610, "height": 208},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node24_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_12",
            metadata={
                "position": {"x": 9573.701512180003, "y": 3726.8337734423917},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 759, "height": 209},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node25_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_13",
            metadata={
                "position": {"x": 10555.011956935225, "y": 3437.4795212493655},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 628, "height": 206},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node26_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_14",
            metadata={
                "position": {"x": 12164.966143416219, "y": 3252.516864309315},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 600, "height": 207},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node27_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="Note",
            specific_library_name="Griptape Nodes Library",
            node_name="Getting Started_15",
            metadata={
                "position": {"x": 11295.18220290928, "y": 3231.4795212493655},
                "tempId": "placing-1763418749829-j1ogey",
                "library_node_metadata": NodeMetadata(
                    category="misc",
                    description="Create a note node to provide helpful context in your workflow",
                    display_name="Note",
                    tags=None,
                    icon="notepad-text",
                    color=None,
                    group="create",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Griptape Nodes Library",
                "node_type": "Note",
                "showaddparameter": False,
                "size": {"width": 600, "height": 208},
                "category": "misc",
            },
            initial_setup=True,
        )
    ).node_name
    node28_name = GriptapeNodes.handle_request(
        CreateNodeRequest(
            node_type="FlowListProjects",
            specific_library_name="Flow Production Tracking Library",
            node_name="List Projects",
            metadata={
                "library_node_metadata": NodeMetadata(
                    category="autodesk",
                    description="Griptape Node that lists all projects in ShotGrid.",
                    display_name="List Projects",
                    tags=None,
                    icon=None,
                    color=None,
                    group="projects",
                    deprecation=None,
                    is_node_group=None,
                ),
                "library": "Flow Production Tracking Library",
                "node_type": "FlowListProjects",
                "position": {"x": 3180.8714573545685, "y": 621.0155514441952},
                "size": {"width": 600, "height": 1184},
            },
            initial_setup=True,
        )
    ).node_name
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node2_name,
            source_parameter_name="output",
            target_node_name=node3_name,
            target_parameter_name="prompt",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node5_name,
            source_parameter_name="text",
            target_node_name=node4_name,
            target_parameter_name="asset_code",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node5_name,
            source_parameter_name="text",
            target_node_name=node2_name,
            target_parameter_name="input_2",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node3_name,
            source_parameter_name="image_url",
            target_node_name=node4_name,
            target_parameter_name="thumbnail_image",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node6_name,
            source_parameter_name="text",
            target_node_name=node4_name,
            target_parameter_name="asset_description",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node9_name,
            source_parameter_name="text",
            target_node_name=node10_name,
            target_parameter_name="text",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node11_name,
            source_parameter_name="loop",
            target_node_name=node12_name,
            target_parameter_name="from_start",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node11_name,
            source_parameter_name="loop_end_condition_met_signal",
            target_node_name=node12_name,
            target_parameter_name="loop_end_condition_met_signal_input",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node12_name,
            source_parameter_name="trigger_next_iteration_signal_output",
            target_node_name=node11_name,
            target_parameter_name="trigger_next_iteration_signal",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node12_name,
            source_parameter_name="break_loop_signal_output",
            target_node_name=node11_name,
            target_parameter_name="break_loop_signal",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node10_name,
            source_parameter_name="output",
            target_node_name=node11_name,
            target_parameter_name="items",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node11_name,
            source_parameter_name="current_item",
            target_node_name=node13_name,
            target_parameter_name="asset_code",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node14_name,
            source_parameter_name="output",
            target_node_name=node15_name,
            target_parameter_name="prompt",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node11_name,
            source_parameter_name="current_item",
            target_node_name=node14_name,
            target_parameter_name="input_2",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node15_name,
            source_parameter_name="image_url",
            target_node_name=node13_name,
            target_parameter_name="thumbnail_image",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node11_name,
            source_parameter_name="current_item",
            target_node_name=node16_name,
            target_parameter_name="additional_context",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node16_name,
            source_parameter_name="output",
            target_node_name=node14_name,
            target_parameter_name="input_3",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node16_name,
            source_parameter_name="output",
            target_node_name=node13_name,
            target_parameter_name="asset_description",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node13_name,
            source_parameter_name="asset_url",
            target_node_name=node12_name,
            target_parameter_name="new_item_to_add",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node12_name,
            source_parameter_name="results",
            target_node_name=node17_name,
            target_parameter_name="items",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node11_name,
            source_parameter_name="exec_out",
            target_node_name=node16_name,
            target_parameter_name="exec_in",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node16_name,
            source_parameter_name="exec_out",
            target_node_name=node14_name,
            target_parameter_name="exec_in",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node14_name,
            source_parameter_name="exec_out",
            target_node_name=node15_name,
            target_parameter_name="exec_in",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node15_name,
            source_parameter_name="exec_out",
            target_node_name=node13_name,
            target_parameter_name="exec_in",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node13_name,
            source_parameter_name="exec_out",
            target_node_name=node12_name,
            target_parameter_name="add_item",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node28_name,
            source_parameter_name="project_id",
            target_node_name=node4_name,
            target_parameter_name="project_id",
            initial_setup=True,
        )
    )
    GriptapeNodes.handle_request(
        CreateConnectionRequest(
            source_node_name=node28_name,
            source_parameter_name="project_id",
            target_node_name=node13_name,
            target_parameter_name="project_id",
            initial_setup=True,
        )
    )
    with GriptapeNodes.ContextManager().node(node0_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node0_name,
                value=top_level_unique_values_dict["8adec450-bc0c-4bcb-a599-d77b4d042a3e"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node1_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node1_name,
                value=top_level_unique_values_dict["ca114065-d664-46d7-8a77-19d6cad4f9cb"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node2_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="input_1",
                node_name=node2_name,
                value=top_level_unique_values_dict["4bc98aee-212c-420d-8bc1-12c65d1556bf"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="input_2",
                node_name=node2_name,
                value=top_level_unique_values_dict["264031c2-4d9e-4654-9df7-bdbfd921a626"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="merge_string",
                node_name=node2_name,
                value=top_level_unique_values_dict["0fff65fc-b4ef-44b7-8298-c646c9d5c572"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="whitespace",
                node_name=node2_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output",
                node_name=node2_name,
                value=top_level_unique_values_dict["18e1442b-0973-40c2-8cce-210be417536a"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output",
                node_name=node2_name,
                value=top_level_unique_values_dict["18e1442b-0973-40c2-8cce-210be417536a"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node3_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="api_key_provider",
                node_name=node3_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="model",
                node_name=node3_name,
                value=top_level_unique_values_dict["59e7d59d-a238-4e04-be92-597c47cfc17c"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="prompt",
                node_name=node3_name,
                value=top_level_unique_values_dict["18e1442b-0973-40c2-8cce-210be417536a"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="aspect_ratio",
                node_name=node3_name,
                value=top_level_unique_values_dict["0d85767e-a7ef-4c37-86be-c0736f69df8e"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="randomize_seed",
                node_name=node3_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="seed",
                node_name=node3_name,
                value=top_level_unique_values_dict["cf743287-ff47-4258-bd68-fc9bf17cefff"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="prompt_upsampling",
                node_name=node3_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output_format",
                node_name=node3_name,
                value=top_level_unique_values_dict["8dbb56e0-5370-4062-bdb1-2ac510711b47"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="safety_tolerance",
                node_name=node3_name,
                value=top_level_unique_values_dict["a208f3c6-cfe7-4420-bd35-b90de660c0ab"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="generation_id",
                node_name=node3_name,
                value=top_level_unique_values_dict["9a6c0db2-046f-4dc4-a35c-6c6276d1e9ef"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="provider_response",
                node_name=node3_name,
                value=top_level_unique_values_dict["46375d4f-e1ad-4549-af43-538523257502"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="image_url",
                node_name=node3_name,
                value=top_level_unique_values_dict["3b7f625b-d44c-42bc-abc5-9998b2b2f651"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="was_successful",
                node_name=node3_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="was_successful",
                node_name=node3_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="result_details",
                node_name=node3_name,
                value=top_level_unique_values_dict["f0f5060e-07af-43a4-9c09-82aa66854709"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="result_details",
                node_name=node3_name,
                value=top_level_unique_values_dict["f0f5060e-07af-43a4-9c09-82aa66854709"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node4_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_code",
                node_name=node4_name,
                value=top_level_unique_values_dict["264031c2-4d9e-4654-9df7-bdbfd921a626"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_type",
                node_name=node4_name,
                value=top_level_unique_values_dict["c8c83190-e339-4b1b-a19a-f830b605563e"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_description",
                node_name=node4_name,
                value=top_level_unique_values_dict["36ec5401-d5a5-4f00-aef6-fc4d87e141e0"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="use_template",
                node_name=node4_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="task_template_id",
                node_name=node4_name,
                value=top_level_unique_values_dict["afb6ad84-7967-4f85-8c75-3fc79825f726"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="thumbnail_image",
                node_name=node4_name,
                value=top_level_unique_values_dict["3b7f625b-d44c-42bc-abc5-9998b2b2f651"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_id",
                node_name=node4_name,
                value=top_level_unique_values_dict["a4ec59f9-35d8-46dc-a19a-f7d30d13bbc0"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_url",
                node_name=node4_name,
                value=top_level_unique_values_dict["8faac5c5-8c2a-492f-8a7b-43d5926f8036"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_url",
                node_name=node4_name,
                value=top_level_unique_values_dict["8faac5c5-8c2a-492f-8a7b-43d5926f8036"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="created_asset",
                node_name=node4_name,
                value=top_level_unique_values_dict["e5d46b0d-5329-4ac8-b86f-4863564669ae"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node5_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node5_name,
                value=top_level_unique_values_dict["264031c2-4d9e-4654-9df7-bdbfd921a626"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node5_name,
                value=top_level_unique_values_dict["264031c2-4d9e-4654-9df7-bdbfd921a626"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node6_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node6_name,
                value=top_level_unique_values_dict["36ec5401-d5a5-4f00-aef6-fc4d87e141e0"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node6_name,
                value=top_level_unique_values_dict["36ec5401-d5a5-4f00-aef6-fc4d87e141e0"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node7_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node7_name,
                value=top_level_unique_values_dict["dc45cef0-b7bd-4de1-9d45-35f8041de7e3"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node8_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node8_name,
                value=top_level_unique_values_dict["d6c5fc14-23ce-4e37-9d0d-83b50cddf481"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node9_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node9_name,
                value=top_level_unique_values_dict["76b86360-8c12-4358-b015-8ac376f851c8"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node9_name,
                value=top_level_unique_values_dict["264031c2-4d9e-4654-9df7-bdbfd921a626"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node10_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="text",
                node_name=node10_name,
                value=top_level_unique_values_dict["264031c2-4d9e-4654-9df7-bdbfd921a626"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="split_mode",
                node_name=node10_name,
                value=top_level_unique_values_dict["e580eedf-f42e-4792-b105-447a91816857"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="delimiter_type",
                node_name=node10_name,
                value=top_level_unique_values_dict["d5ce5408-1cab-41c1-b3f6-83a8c9edea0d"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="include_delimiter",
                node_name=node10_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="trim_whitespace",
                node_name=node10_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output",
                node_name=node10_name,
                value=top_level_unique_values_dict["719bdb4d-b0dd-497d-9448-a30df3e44fe5"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node11_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="index",
                node_name=node11_name,
                value=top_level_unique_values_dict["d4cb2615-c977-4467-acaa-454b5a224b8e"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="items",
                node_name=node11_name,
                value=top_level_unique_values_dict["719bdb4d-b0dd-497d-9448-a30df3e44fe5"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="run_in_order",
                node_name=node11_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node12_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="new_item_to_add",
                node_name=node12_name,
                value=top_level_unique_values_dict["8faac5c5-8c2a-492f-8a7b-43d5926f8036"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node13_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_code",
                node_name=node13_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_type",
                node_name=node13_name,
                value=top_level_unique_values_dict["c8c83190-e339-4b1b-a19a-f830b605563e"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_description",
                node_name=node13_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="use_template",
                node_name=node13_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="task_template_id",
                node_name=node13_name,
                value=top_level_unique_values_dict["10ce1eb6-7869-4a33-9f03-4909e4a5b80b"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="thumbnail_image",
                node_name=node13_name,
                value=top_level_unique_values_dict["50fbf820-ca67-4cda-a2df-facb9679961c"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_id",
                node_name=node13_name,
                value=top_level_unique_values_dict["a4ec59f9-35d8-46dc-a19a-f7d30d13bbc0"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_url",
                node_name=node13_name,
                value=top_level_unique_values_dict["8faac5c5-8c2a-492f-8a7b-43d5926f8036"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="asset_url",
                node_name=node13_name,
                value=top_level_unique_values_dict["8faac5c5-8c2a-492f-8a7b-43d5926f8036"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="created_asset",
                node_name=node13_name,
                value=top_level_unique_values_dict["658c1944-082c-443c-8cb1-1c42cc150a6f"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node14_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="input_1",
                node_name=node14_name,
                value=top_level_unique_values_dict["4bc98aee-212c-420d-8bc1-12c65d1556bf"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="input_2",
                node_name=node14_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="input_3",
                node_name=node14_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="merge_string",
                node_name=node14_name,
                value=top_level_unique_values_dict["0fff65fc-b4ef-44b7-8298-c646c9d5c572"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="whitespace",
                node_name=node14_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output",
                node_name=node14_name,
                value=top_level_unique_values_dict["4bc98aee-212c-420d-8bc1-12c65d1556bf"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output",
                node_name=node14_name,
                value=top_level_unique_values_dict["4bc98aee-212c-420d-8bc1-12c65d1556bf"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node15_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="api_key_provider",
                node_name=node15_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="model",
                node_name=node15_name,
                value=top_level_unique_values_dict["59e7d59d-a238-4e04-be92-597c47cfc17c"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="prompt",
                node_name=node15_name,
                value=top_level_unique_values_dict["18e1442b-0973-40c2-8cce-210be417536a"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="aspect_ratio",
                node_name=node15_name,
                value=top_level_unique_values_dict["0d85767e-a7ef-4c37-86be-c0736f69df8e"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="randomize_seed",
                node_name=node15_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="seed",
                node_name=node15_name,
                value=top_level_unique_values_dict["cf743287-ff47-4258-bd68-fc9bf17cefff"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="prompt_upsampling",
                node_name=node15_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output_format",
                node_name=node15_name,
                value=top_level_unique_values_dict["8dbb56e0-5370-4062-bdb1-2ac510711b47"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="safety_tolerance",
                node_name=node15_name,
                value=top_level_unique_values_dict["a208f3c6-cfe7-4420-bd35-b90de660c0ab"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="generation_id",
                node_name=node15_name,
                value=top_level_unique_values_dict["9a6c0db2-046f-4dc4-a35c-6c6276d1e9ef"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="provider_response",
                node_name=node15_name,
                value=top_level_unique_values_dict["d1c7c00b-bd78-44ab-9a22-36213f8066dd"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="image_url",
                node_name=node15_name,
                value=top_level_unique_values_dict["50fbf820-ca67-4cda-a2df-facb9679961c"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="was_successful",
                node_name=node15_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="was_successful",
                node_name=node15_name,
                value=top_level_unique_values_dict["6f275bad-e844-4c94-8055-0efa963db3c2"],
                initial_setup=True,
                is_output=True,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="result_details",
                node_name=node15_name,
                value=top_level_unique_values_dict["f0f5060e-07af-43a4-9c09-82aa66854709"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="result_details",
                node_name=node15_name,
                value=top_level_unique_values_dict["f0f5060e-07af-43a4-9c09-82aa66854709"],
                initial_setup=True,
                is_output=True,
            )
        )
    with GriptapeNodes.ContextManager().node(node16_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="model",
                node_name=node16_name,
                value=top_level_unique_values_dict["b8cd49bf-4802-4d1a-ac47-3b1f05281073"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="agent_memory",
                node_name=node16_name,
                value=top_level_unique_values_dict["79abc8c0-3263-453c-83ca-d59a754908ed"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="prompt",
                node_name=node16_name,
                value=top_level_unique_values_dict["746a8fa8-bed7-4647-98fc-49cf2af29cd2"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="additional_context",
                node_name=node16_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="tools",
                node_name=node16_name,
                value=top_level_unique_values_dict["ae78389b-1186-4fc1-b7b4-31b76386282f"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="rulesets",
                node_name=node16_name,
                value=top_level_unique_values_dict["96886147-549f-4ca1-864c-a8c3ef972cf3"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="output",
                node_name=node16_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="include_details",
                node_name=node16_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node18_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node18_name,
                value=top_level_unique_values_dict["676bb48e-f5b0-4408-99a2-46ef2bdef4f2"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node19_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node19_name,
                value=top_level_unique_values_dict["1415e3ea-b2d6-4692-b48c-78893dc4e6d0"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node20_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node20_name,
                value=top_level_unique_values_dict["4da5e7a8-43a6-40f0-9ce9-9136dedd1fb3"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node21_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node21_name,
                value=top_level_unique_values_dict["ef3d113d-5dcd-498f-9a30-80dc7bcb1594"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node22_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node22_name,
                value=top_level_unique_values_dict["cbf867b5-9a43-4060-a31b-222a324c0d0f"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node23_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node23_name,
                value=top_level_unique_values_dict["eb7fe00d-e8b2-471d-966b-12646ee5b842"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node24_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node24_name,
                value=top_level_unique_values_dict["a906dd37-556c-4770-9f5e-a909870eb8b3"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node25_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node25_name,
                value=top_level_unique_values_dict["cced66f9-f9cd-4b40-95c7-14ba383e8251"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node26_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node26_name,
                value=top_level_unique_values_dict["bef92170-3c3c-4f08-adc5-fc3c7c22728e"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node27_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="note",
                node_name=node27_name,
                value=top_level_unique_values_dict["3bf276b0-07fc-4338-8c76-9b8336f0d649"],
                initial_setup=True,
                is_output=False,
            )
        )
    with GriptapeNodes.ContextManager().node(node28_name):
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="projects_url",
                node_name=node28_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="show_templates",
                node_name=node28_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="show_only_templates",
                node_name=node28_name,
                value=top_level_unique_values_dict["f17c0f0b-307c-49e0-9d12-54301ae072d6"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="project",
                node_name=node28_name,
                value=top_level_unique_values_dict["c985ffc0-ffec-4332-97b0-e22cf7ec0532"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="project_url",
                node_name=node28_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="project_id",
                node_name=node28_name,
                value=top_level_unique_values_dict["8cb0aa39-391e-42b9-a5ac-01feefc7d300"],
                initial_setup=True,
                is_output=False,
            )
        )
        GriptapeNodes.handle_request(
            SetParameterValueRequest(
                parameter_name="project_data",
                node_name=node28_name,
                value=top_level_unique_values_dict["b3059f79-de83-48ab-810c-c5a74139c333"],
                initial_setup=True,
                is_output=False,
            )
        )
