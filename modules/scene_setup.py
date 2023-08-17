from math import radians

import bpy
import bpy.ops
from . import utils


def setup_scene(data: dict) -> dict:
    # Setup scene
    utils.clear_scene()
    # _setup_render_template()  # Todo: Enable this
    _setup_scene_settings()
    _setup_view_layers()
    _setup_world(data)
    _setup_lights(data)
    _setup_camera(data)
    objects = _setup_objects(data)
    actors = _setup_actors(data)

    # Combine objects and actors dicts
    actors.update(objects)
    return actors


def _setup_render_template():
    # Download the latest render templates and load that blend file
    render_template_path = "s3://metabull3dassets/Blender_TestAssets/PHC_Scene_RenderTemplate_001.blend"
    file_path = utils.get_resource(render_template_path)

    # Load the render template blend file
    bpy.ops.wm.open_mainfile(filepath=file_path)


def _setup_scene_settings():
    # Set up some settings
    bpy.context.preferences.view.show_developer_ui = True
    bpy.context.preferences.view.show_tooltips_python = True
    bpy.context.preferences.view.show_statusbar_stats = True
    bpy.context.preferences.view.show_splash = False

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.feature_set = "SUPPORTED"
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "OPTIX"

    bpy.context.scene.render.use_persistent_data = True
    bpy.context.scene.render.film_transparent = True

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 100
    bpy.context.scene.render.fps = 24

    bpy.context.scene.use_audio_scrub = True
    bpy.context.scene.sync_mode = 'FRAME_DROP'

    # Bernardo's settings
    bpy.context.scene.cycles.samples = 250
    bpy.context.scene.cycles.preview_samples = 2
    bpy.context.scene.cycles.max_bounces = 24
    bpy.context.scene.cycles.transparent_max_bounces = 24
    bpy.context.scene.render.use_simplify = True
    bpy.context.scene.cycles.texture_limit = '512'
    bpy.context.scene.cycles.texture_limit_render = '4096'
    bpy.context.scene.cycles.use_camera_cull = True

    # Speed Render settings (for testing)
    # bpy.context.scene.cycles.samples = 2
    # bpy.context.scene.cycles.max_bounces = 2
    # bpy.context.scene.cycles.transparent_max_bounces = 2
    # bpy.context.scene.cycles.adaptive_threshold = 0.2
    # bpy.context.scene.cycles.texture_limit_render = '512'

    print(f"INFO: Samples: {bpy.context.scene.cycles.samples}, "
          f"Threshold: {round(bpy.context.scene.cycles.adaptive_threshold, 4)}, "
          f"Max Bounces: {bpy.context.scene.cycles.max_bounces}")


def _setup_view_layers():
    # Delete default collection
    bpy.data.collections.remove(bpy.data.collections["Collection"])

    # Create actor and object collections
    coll_scene = bpy.data.collections.new("Scene")
    coll_objects = bpy.data.collections.new("Objects")
    coll_actors = bpy.data.collections.new("Actors")
    bpy.context.scene.collection.children.link(coll_scene)
    bpy.context.scene.collection.children.link(coll_objects)
    bpy.context.scene.collection.children.link(coll_actors)

    # Add new view layers
    # vl_objects = bpy.context.scene.view_layers.new("Objects")
    # vl_actors = bpy.context.scene.view_layers.new("Actors")

    # Link collections to view layers
    # vl_objects.collection = coll_objects
    # vl_actors.collection = coll_actors

    # # Set up view layers
    #
    # bpy.data.scenes["Scene.001"].name = "Background"
    # bpy.context.view_layer.layer_collection.children["Background"].exclude = False
    # bpy.context.view_layer.layer_collection.children["Background"].hide_viewport = False
    #
    # bpy.data.scenes["Scene.002"].name = "Foreground"
    # bpy.context.view_layer.layer_collection.children["Foreground"].exclude = False
    # bpy.context.view_layer.layer_collection.children["Foreground"].hide_viewport = False


def _setup_world(data: dict):
    worlds = [world for world in bpy.data.worlds]

    world_file = data["scene"]["time"]
    if not world_file or not world_file.lower().endswith(".blend"):  # TODO
        world_file = "s3://metabull3dassets/Blender_TestAssets/TestVersion1/SunnyMorning_Mix_001.blend"

    try:
        file_path = utils.get_resource(world_file)
    except Exception as e:
        print(f"Error loading world: {e}")
        return
    utils.import_blend_file(file_path, link=False, import_types=["worlds"], link_scene="Scene")

    # Get the new world and set it as active
    new_worlds = [world for world in bpy.data.worlds if world not in worlds]
    if new_worlds:
        print(f"INFO: Changing world from {bpy.context.scene.world.name} to {new_worlds[0].name}")
        bpy.context.scene.world = new_worlds[0]


def _setup_lights(data: dict):
    bpy.context.view_layer.active_layer_collection = utils.find_layer_collection("Scene")

    lights = data["scene"]["lighting"]
    for light in lights:
        light_type = light["type"].upper().replace("LIGHT", "")
        light_data = bpy.data.lights.new(name='Light', type=light_type)
        light_obj = bpy.data.objects.new(name=light_data.name, object_data=light_data)
        bpy.context.collection.objects.link(light_obj)

        light_obj.location = utils.get_3d_vec(light.get("location"))
        # light_obj.rotation_euler = utils.get_3d_vec(light["rotation"], use_rad=True)
        # light_obj.scale = utils.get_3d_vec(light["scale"])
        # light_obj.rotation_euler = (0, 0, 0)
        # light_data.energy = 5.0  # light intensity


def _setup_camera(data: dict):
    bpy.context.view_layer.active_layer_collection = utils.find_layer_collection("Scene")

    camera = bpy.data.cameras.new("Camera")
    camera_obj = bpy.data.objects.new("Camera", camera)
    bpy.context.collection.objects.link(camera_obj)

    cam_data = data["scene"]["camera"]
    camera_obj.location = utils.get_3d_vec(cam_data.get("location"))
    camera_obj.rotation_euler = utils.get_3d_vec(cam_data.get("rotation"), use_rad=True)
    camera_obj.scale = utils.get_3d_vec(cam_data.get("scale"), default=(1, 1, 1))

    camera_obj.data.lens = 50  # adjust the focal length to zoom out
    bpy.context.scene.camera = camera_obj  # make this the active camera

    # TODO: Temp solution, remove this when JSON can achieve this
    # camera_obj.location = (0.328782, -1.91114, 1.91264)
    # camera_obj.rotation_euler = (radians(77.8), 0, radians(19.4))
    camera_obj.data.lens = 37


def _setup_objects(data: dict) -> dict:
    objects = {}

    obj_data = data["scene"]["objects"]
    for obj in obj_data:
        obj_name = obj["name"]
        obj_file = utils.get_resource(obj["file"])
        obj_pos = utils.get_3d_vec(obj.get("location"))
        obj_rot = utils.get_3d_vec(obj.get("rotation"), use_rad=True)
        obj_scale = utils.get_3d_vec(obj.get("scale"), default=(1, 1, 1))

        # importing the object
        obj_imported = utils.import_file(obj_file)

        obj_imported.location = obj_pos
        obj_imported.rotation_euler = obj_rot
        obj_imported.scale = obj_scale
        obj_imported.name = obj_name

        # TODO: Temp solution, remove this when JSON can achieve this
        if "pie_hole_cafe" in str(obj_file).lower():
            obj_imported.location = (-0.6, 4.54, -0.309)
            obj_imported.rotation_euler = (0, 0, radians(141))

        objects[obj_name.lower()] = obj_imported

    return objects


def _setup_actors(data: dict) -> dict:
    actors = {}

    character_data = data["scene"]["actors"]
    for obj in character_data:
        obj_name = obj["name"]

        # TODO: REMOVE THIS after version 2 test
        file_name = obj["file"]
        if file_name.endswith("Sarge_rigged_packed.blend"):
            file_name = "s3://metabull3dassets/Blender_TestAssets/TestVersion1/Sarge_rigged_packed_v5.blend"

        obj_file = utils.get_resource(file_name)
        obj_pos = utils.get_3d_vec(obj.get("location"))
        obj_rot = utils.get_3d_vec(obj.get("rotation"), use_rad=True)
        obj_scale = utils.get_3d_vec(obj.get("scale"), default=(1, 1, 1))

        # importing the object
        obj_imported = utils.import_file(obj_file, is_actor=True)

        # Set up the imported character
        _setup_character(obj_imported, bpy.context.view_layer.layer_collection)

        obj_imported.location += obj_pos
        obj_imported.rotation_euler[0] += obj_rot[0]
        obj_imported.rotation_euler[1] += obj_rot[1]
        obj_imported.rotation_euler[2] += obj_rot[2]
        obj_imported.scale *= obj_scale
        obj_imported.name = obj_name

        actors[obj_name.lower()] = obj_imported

    return actors


def _setup_character(asset: bpy.types.Object, collection: bpy.types.LayerCollection):
    print("Setting up character:", asset.name)

    # Check if the collection has a child collection called "Faceit_Collection"
    collection_faceit = utils.find_layer_collection("Faceit_Collection", collection)
    if not collection_faceit:
        print("No Faceit_Collection found in character:", asset.name)
    else:
        # Delete the full faceit collection and all its children
        utils.delete_hierarchy(collection_faceit)

    # Delete faceit actions
    for action in bpy.data.actions:
        if action.name.startswith("faceit"):
            bpy.data.actions.remove(action, do_unlink=True)

    is_actor_v4 = False

    # Delete all "cs" objects
    for obj in asset.children_recursive:
        try:
            if obj.name.lower().startswith("cs_"):
                utils.delete_hierarchy(obj)
        except ReferenceError:
            pass

    # Look for the armature
    armature = None
    for obj in asset.children_recursive:
        if obj.type != "ARMATURE":
            continue
        if obj.name.lower().startswith("cs"):
            continue

        # Check if obj is in view layer
        if obj.name not in bpy.context.view_layer.objects:
            continue

        # If the armature ends with rigify, use that, otherwise use the first one found
        if obj.name.lower().endswith("rigify"):
            armature = obj
            is_actor_v4 = True
            break

        # If the armature ends with rigify, use that, otherwise use the first one found
        if obj.name.lower().endswith("_rig"):
            armature = obj
            is_actor_v4 = True
            break

        if not armature:
            armature = obj

    if not armature:
        print("No armature found in character:", asset.name)
        return

    print("Found Armature:", armature.name)
    # Rename armature
    armature.name = f"metabull_{asset.name}_rig"

    # If the actor is v4, don't do anything else currently
    if is_actor_v4:
        armature.name = f"metabull_{asset.name}_rig_v4"

    # Delete not needed elements
    for obj in armature.children:
        if obj.type != "MESH":
            continue
        # Delete the expression control panel
        if obj.name.startswith("expression_controlpanel"):
            utils.delete_hierarchy(obj)
            continue

    return

    # for obj in armature.children:
    #     if obj.type != "MESH":
    #         continue
    #
    #     # Delete the expression control panel
    #     if obj.name.startswith("expression_controlpanel"):
    #         utils.delete_hierarchy(obj)
    #         continue
    #
    #     # Transfer shapekeys from the deformer mesh to the child meshes
    #     if obj.name.endswith("_deformer"):
    #         _deformer_to_shapekeys(obj)
    #         continue
    #
    # # If any child meshes of the armature have no armature modifier,
    # # weight paint the mesh to the head bone and add an armature modifier
    # for obj in armature.children:
    #     # bpy.context.object.parent_bone = ""
    #
    #     # Get the list of armature mods
    #     armature_mods = [mod for mod in obj.modifiers if mod.type == "ARMATURE"]
    #     if not armature_mods:
    #         utils.weight_paint_obj_to_bone(obj, armature, "head.x")
    #
    #     # Remove the armature modifier if the mesh is controlled by bone parenting
    #     if obj.parent_type == "BONE" and obj.parent_bone:
    #         for mod in obj.modifiers:
    #             if mod.type == "ARMATURE":
    #                 obj.modifiers.remove(mod)
    #
    # # Join all child meshes of the armature
    # bpy.ops.object.select_all(action='DESELECT')
    # # for obj in armature.children:
    # #     if obj.type != "MESH" or obj.children:
    # #         continue
    # #
    # #     # Rename all UVMaps to the same name to they are merged correctly
    # #     for uv_layer in obj.data.uv_layers:
    # #         uv_layer.name = "UVMap"
    # #     # Rename all the curves UV data to UVMap
    # #     # for child in obj.children:
    # #     #     if child.type == "CURVES":
    # #     #         child.data.surface_uv_map = "UVMap"
    # #
    # #     utils.set_active(obj, select=True)
    #
    # # This is specific for the new character sarge
    # # for obj in armature.children:
    # #     if obj.type == "MESH" and obj.children:
    # #         utils.set_active(obj, select=True)
    #
    # # bpy.ops.object.join()
    # body_mesh = utils.get_active()
    # body_mesh.name = f"metabull_{asset.name}_body"


def _deformer_to_shapekeys(obj: bpy.types.Object):
    """ Transfer all shapekeys of the deformer mesh to the child meshes """

    if not obj or obj.type != "MESH" or not obj.children or not obj.data.shape_keys:
        print("Invalid deformer mesh:", obj.name)
        return

    # Apply all modifiers of the child meshes
    for child in obj.children:
        if child.type != "MESH":
            continue

        utils.set_active(child, select=True)
        for mod in child.modifiers:
            if mod.type != "MESH_DEFORM":
                # Apply the modifier. If it fails, delete it
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except RuntimeError:
                    bpy.ops.object.modifier_remove(modifier=mod.name)

    # Loop over all shapekeys
    for i, sk in enumerate(obj.data.shape_keys.key_blocks):
        if i == 0:
            continue

        sk.value = 1

        # Create a new shapekey from the mix in each child mesh
        for child in obj.children:
            if child.type != "MESH":
                continue

            # Apply the mesh deformer modifier as a shape key
            utils.set_active(child, select=True)
            for mod in child.modifiers:
                if mod.type == "MESH_DEFORM":
                    bpy.ops.object.modifier_apply_as_shapekey(modifier=mod.name, keep_modifier=True)

            # Rename the shapekey
            child.data.shape_keys.key_blocks[-1].name = sk.name

        sk.value = 0

    # Delete the deformer mesh and place the children in its place
    for child in obj.children:
        # Parent the obj to the deformer's parent and keep transform
        child.parent = obj.parent
        child.matrix_parent_inverse = obj.matrix_parent_inverse

    bpy.data.objects.remove(obj, do_unlink=True)






