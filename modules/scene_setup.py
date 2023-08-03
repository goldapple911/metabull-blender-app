
import bpy
import bpy.ops
from . import utils


def setup_scene(data: dict) -> dict:
    # Setup scene
    utils.clear_scene()
    _setup_scene_settings()
    _setup_lights(data)
    _setup_camera(data)
    objects = _setup_objects(data)
    actors = _setup_actors(data)

    # Combine objects and actors dicts
    actors.update(objects)
    return actors


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
    bpy.context.scene.cycles.samples = 2
    bpy.context.scene.cycles.adaptive_threshold = 0.1
    bpy.context.scene.cycles.max_bounces = 4

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 160
    bpy.context.scene.render.fps = 24


def _setup_lights(data: dict):
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
    camera = bpy.data.cameras.new("Camera")
    camera_obj = bpy.data.objects.new("Camera", camera)
    bpy.context.collection.objects.link(camera_obj)

    cam_data = data["scene"]["camera"]
    camera_obj.location = utils.get_3d_vec(cam_data.get("location"))
    camera_obj.rotation_euler = utils.get_3d_vec(cam_data.get("rotation"), use_rad=True)
    camera_obj.scale = utils.get_3d_vec(cam_data.get("scale"), default=(1, 1, 1))

    camera_obj.data.lens = 50  # adjust the focal length to zoom out
    bpy.context.scene.camera = camera_obj  # make this the active camera


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
        obj_imported = utils.import_file(obj_file, allow_link=True)

        obj_imported.location = obj_pos
        obj_imported.rotation_euler = obj_rot
        obj_imported.scale = obj_scale
        obj_imported.name = obj_name

        objects[obj_name] = obj_imported

    return objects


def _setup_actors(data: dict) -> dict:
    actors = {}

    character_data = data["scene"]["actors"]
    for obj in character_data:
        obj_name = obj["name"]
        obj_file = utils.get_resource(obj["file"])
        obj_pos = utils.get_3d_vec(obj.get("location"))
        obj_rot = utils.get_3d_vec(obj.get("rotation"), use_rad=True)
        obj_scale = utils.get_3d_vec(obj.get("scale"), default=(1, 1, 1))

        # importing the object
        obj_imported = utils.import_file(obj_file)

        # Set up the imported character
        _setup_character(obj_imported, bpy.context.view_layer.layer_collection)

        obj_imported.location += obj_pos
        obj_imported.rotation_euler[0] += obj_rot[0]
        obj_imported.rotation_euler[1] += obj_rot[1]
        obj_imported.rotation_euler[2] += obj_rot[2]
        obj_imported.scale *= obj_scale
        obj_imported.name = obj_name

        actors[obj_name] = obj_imported

    return actors


def _setup_character(asset: bpy.types.Object, collection: bpy.types.LayerCollection):
    print("Setting up character:", asset.name)

    # Check if the collection has a child collection called "Faceit_Collection"
    collection_faceit = utils.find_layer_collection("Faceit_Collection", collection)
    if not collection_faceit:
        print("No Faceit_Collection found in character:", asset.name)
        return

    # Delete the full faceit collection and all its children
    utils.delete_hierarchy(collection_faceit)

    # Delete faceit actions
    for action in bpy.data.actions:
        if action.name.startswith("faceit"):
            bpy.data.actions.remove(action, do_unlink=True)

    # Look for the armature
    armature = None
    for obj in asset.children_recursive:
        if obj.type == "ARMATURE":
            if obj.name.startswith("cs"):
                continue
            armature = obj
            break

    if not armature:
        print("No armature found in character:", asset.name)
        return

    # Rename armature
    armature.name = f"metabull_{asset.name}_rig"

    for obj in armature.children:
        if obj.type != "MESH":
            continue

        # Delete the expression control panel
        if obj.name.startswith("expression_controlpanel"):
            utils.delete_hierarchy(obj)
            continue

        # Transfer shapekeys from the deformer mesh to the child meshes
        if obj.name.endswith("_deformer"):
            _deformer_to_shapekeys(obj)
            continue

    # If any child meshes of the armature have no armature modifier,
    # weight paint the mesh to the head bone and add an armature modifier
    for obj in armature.children:
        if not [mod for mod in obj.modifiers if mod.type == "ARMATURE"]:
            utils.weight_paint_obj_to_bone(obj, armature, "head.x")

    # Join all child meshes of the armature
    bpy.ops.object.select_all(action='DESELECT')
    for obj in armature.children:
        if obj.type != "MESH" or obj.children:
            continue

        # Rename all UVMaps to the same name to they are merged correctly
        for uv_layer in obj.data.uv_layers:
            uv_layer.name = "UVMap"

        utils.set_active(obj, select=True)

    bpy.ops.object.join()
    body_mesh = utils.get_active()
    body_mesh.name = f"metabull_{asset.name}_body"


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






