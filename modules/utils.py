import bpy
import boto3
import pathlib
import subprocess
from math import radians
from mathutils import Vector, Euler
from datetime import timezone
from datetime import datetime as dt

assets_dir = pathlib.Path(__file__).parent.parent / "assets"

aws_object_url_identifier = ".s3.amazonaws.com"
check_asset_updates = False

s3 = boto3.client(
    's3',
    aws_access_key_id="AKIASWELGIRGDL3YZERT",
    aws_secret_access_key="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"
)


def set_active(obj, select=False, deselect_others=False):
    if deselect_others:
        bpy.ops.object.select_all(action='DESELECT')
    if select:
        set_select(obj, True)
    bpy.context.view_layer.objects.active = obj


def get_active():
    return bpy.context.view_layer.objects.active


def set_select(obj, select):
    obj.select_set(select)


def clear_scene():
    # Delete all objects
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)


def get_resource(path: str) -> pathlib.Path:
    logger.log(f"Importing resource {path}")
    # Download the S3 bucket paths first
    if path.lower().startswith("s3://") or aws_object_url_identifier in path.lower():
        path = str(download_from_s3(path))

    # Check if the path is absolute. If not, get the path relative to the assets folder
    path_abs = pathlib.Path(path)
    if not path_abs.exists():
        if path.startswith("/") or path.startswith("\\"):
            path = path[1:]
        path_abs = assets_dir / path

    # Check if the resource exists
    if not path_abs.exists():
        raise Exception(f"Resource does not exist: {path}")

    return path_abs


def download_from_s3(path: str) -> pathlib.Path:
    path_original = path
    # Check if the path is an object URL instead of an S3 url and convert it in that case
    if aws_object_url_identifier in path.lower():
        path = path.replace(aws_object_url_identifier, "")
        path = path.replace("https://", "s3://")

    path_abs = pathlib.Path(path)

    if "." not in path_abs.name:
        raise Exception(f"Invalid S3 path, not a file: {path_original}")

    # Dissect S3 url and create target path
    bucket_name = path_abs.parts[1]
    key = "/".join(path_abs.parts[2:])
    target_path = assets_dir / "s3" / bucket_name / key

    # If the file already exists locally, check for a newer version on S3
    if target_path.exists():
        if not check_asset_updates:
            print(f"INFO: Skipped S3 file download, already exists: {path_original}")
            return target_path

        # Get the file info from S3
        try:
            response = s3.head_object(Bucket=bucket_name, Key=key)
        except Exception as e:
            raise Exception(f"{e}\nUnable to find file on S3. Is the path correct? ('{path_original}')") from None

        last_modified_s3 = response["LastModified"]
        last_modified_s3 = dt.strptime(str(last_modified_s3), "%Y-%m-%d %H:%M:%S%z")

        last_modified_local = target_path.stat().st_mtime
        last_modified_local = dt.fromtimestamp(last_modified_local)
        last_modified_local = last_modified_local.astimezone(timezone.utc)

        # print(f"S3 Modified     : {last_modified_s3}        ({last_modified_s3.timestamp()})")
        # print(f"Locally modified: {last_modified_local} ({last_modified_local.timestamp()})")
        if last_modified_s3.timestamp() > last_modified_local.timestamp():
            print(f"INFO: File on S3 has been updated, re-downloading..")
        else:
            print(f"INFO: Skipped S3 file download, already exists and is up-to-date: {path_original}")
            return target_path

    # Create the target folder if it doesn't exist
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Download the file
    print(f"INFO: Downloading file from S3: {path_original} ...")
    try:
        s3.download_file(bucket_name, key, target_path)
    except Exception as e:
        raise Exception(f"{e}\nUnable to download file from S3. Is the path correct? ('{path_original}')") from None
    print(f"INFO: Downloaded file! Saved to: {target_path}")

    return target_path


def upload_to_s3(output_path: pathlib.Path, parent_folder: pathlib.Path, pattern="*.*", bucket_name="metabull-blender-output"):
    try:
        if output_path.is_dir():
            print(f"Uploading folder to S3: {output_path}")
            for file in reversed(list(output_path.rglob(pattern))):
                file_path_rel = str(file.relative_to(parent_folder)).replace("\\", "/")
                print(f"Uploading: {file_path_rel} ...")
                s3.upload_file(file, f"{bucket_name}", file_path_rel)
        elif output_path.is_file():
            file_path_rel = str(output_path.relative_to(parent_folder)).replace("\\", "/")
            print(f"Uploading file to S3: {file_path_rel} ...")
            s3.upload_file(output_path, bucket_name, file_path_rel)
        else:
            raise Exception(f"File/folder not found: {output_path}")
        file_path_rel = str(output_path.relative_to(parent_folder)).replace("\\", "/")
        print(f"Finished upload! Saved to: {bucket_name}/{file_path_rel}")
    except Exception as e:
        print(f"[ERROR] Unable to upload path to S3: {output_path}")
        print(f"[ERROR Message]: {e}")


def open_in_blender(path: pathlib.Path):
    # Save current scene as blend file
    blend_file = path / "tmp" / "opened.blend"
    blend_file.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_file))

    # Open the blend file with Blender
    current_file = bpy.data.filepath
    subprocess.run(["blender", current_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def import_file(path: pathlib.Path, allow_link=False, is_actor=False):
    print(f"INFO: Importing file {path}")
    set_active(None, deselect_others=True)

    # Save this variable, since blend files doesn't need to have their transforms applied
    is_blend_file = False

    # Import the file using the different importers
    file_type = path.suffix.lower()[1:]
    if file_type == "fbx":
        bpy.ops.import_scene.fbx('EXEC_DEFAULT',
                                 filepath=str(path),
                                 ignore_leaf_bones=True,
                                 )
    elif file_type == "glb" or file_type == "gltf":
        bpy.ops.import_scene.gltf('EXEC_DEFAULT',
                                  filepath=str(path),
                                  )
    elif file_type == "obj" or file_type == "mtl":
        bpy.ops.wm.obj_import('EXEC_DEFAULT',
                              filepath=str(path),
                              )
    elif file_type == "blend":
        is_blend_file = True
        import_blend_file(path, allow_link)
    else:
        raise Exception(f"Unknown import file type: {file_type} in {path}")

    # If there are multiple imported top-level objects, create a parent for them
    imported_parent_objs = [obj for obj in bpy.context.selected_objects if not obj.parent]
    if len(imported_parent_objs) > 1:
        # Create a parent for all imported objects
        parent = bpy.data.objects.new(path.stem, None)

        # Set the parent and link it to the blend collection
        for obj in imported_parent_objs:
            obj.parent = parent

        # Set the parent as active
        set_active(parent, select=True, deselect_others=True)

    # Find the main imported object
    asset = bpy.context.object
    if not asset and not bpy.context.selected_objects:
        raise Exception(f"Error: No object was imported from: {path}")
    if not asset or not asset.select_get():
        asset = bpy.context.selected_objects[0]
        set_active(asset, select=True)
    print("Info: Imported Main object:", asset.name)

    # Move the asset into the actor or object collection
    coll_asset = bpy.data.collections["Objects"] if not is_actor else bpy.data.collections["Actors"]
    if is_blend_file:
        # Get the blend collection that was set during blend file import
        coll_blend = bpy.context.view_layer.active_layer_collection.collection
        if coll_blend.name not in coll_asset.children:
            coll_asset.children.link(coll_blend)
        bpy.context.scene.collection.children.unlink(coll_blend)
    else:
        coll_asset.objects.link(asset)

    if not asset.animation_data and not is_blend_file:
        # Apply transforms
        apply_transforms_hierarchy(asset, location=True, rotation=True, scale=True)

    # Set the rotation mode of each obj to XYZ
    asset.rotation_mode = 'XYZ'
    for child in asset.children_recursive:
        if child.rotation_mode != 'XYZ':
            child.rotation_mode = 'XYZ'

    return asset


def import_blend_file(path: pathlib.Path, link: bool, name: str = None, import_types: list = None, link_scene: str = None):
    if import_types is None:
        import_types = ["collections"]

    # Create new collection and link it to the specified scene
    collection_blend = bpy.data.collections.new(name if name else path.stem)
    main_collection = bpy.context.scene.collection
    if link_scene:
        main_collection = find_layer_collection(name=link_scene).collection
    main_collection.children.link(collection_blend)

    # Create a list of all objects before the import
    objs_before_import = [obj for obj in bpy.data.objects]

    # Load and append the collections from the blend file
    # link=True means that the objects remain in the other blend file and
    # are only linked to this one. This is much faster than copying the data.
    with bpy.data.libraries.load(str(path), link=link) as (data_from, data_to):
        for type_name in import_types:
            for data in getattr(data_from, type_name):
                getattr(data_to, type_name).append(data)

    # Link the collections to their blend collection
    for collection in bpy.data.collections:
        if collection.users < 1:
            collection_blend.children.link(collection)

    # Get all objects that were imported compared to the objects that existed beforehand
    imported_objs = [obj for obj in bpy.data.objects if obj not in objs_before_import]

    # Create a parent for all imported objects
    parent = bpy.data.objects.new(path.stem, None)
    collection_blend.objects.link(parent)

    # Set the parent and link it to the blend collection
    for obj in imported_objs:
        if not obj.parent:
            obj.parent = parent

    # Set the parent as active
    set_active(parent, select=True, deselect_others=True)

    # Set the main collection as active
    bpy.context.view_layer.active_layer_collection = find_layer_collection(collection_blend.name)


def get_3d_vec(data: dict, default=(0, 0, 0), use_rad=False) -> Vector | Euler:
    if not data:
        return Vector(default)
    if use_rad:
        vec = Euler((
            radians(data.get("x") if data.get("x") is not None else data.get("roll")),
            radians(data.get("y") if data.get("y") is not None else data.get("pitch")),
            radians(data.get("z") if data.get("z") is not None else data.get("yaw")),
        ))
    else:
        vec = Vector((data["x"], data["y"], data["z"]))
    return vec


def apply_transforms_hierarchy(obj, location=False, rotation=False, scale=False, single=False, is_first=True):
    if not location and not rotation and not scale:
        raise ValueError("Apply Transforms: At least one of the arguments must be True.")

    # Set new active object
    active_obj_tmp = get_active()
    set_active(obj, select=True, deselect_others=True)

    # Apply transforms
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)

    # Repeat the same for all children
    if not single:
        for obj in obj.children:
            apply_transforms_hierarchy(obj, location=location, rotation=rotation, scale=scale, is_first=False)

    # Set saved active obj back as active
    if is_first:
        set_active(active_obj_tmp, select=True, deselect_others=True)


def delete_hierarchy(parent: bpy.types.LayerCollection | bpy.types.Object):
    """ Delete all objects in a layer collection and its children,
        Or delete all children of an object and the object itself.
        Works just like the Blender UI button "Delete Hierarchy" """

    if isinstance(parent, bpy.types.LayerCollection):
        for obj in parent.collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        for child in parent.children:
            delete_hierarchy(child)

        bpy.data.collections.remove(parent.collection, do_unlink=True)

    elif isinstance(parent, bpy.types.Object):
        for obj in parent.children_recursive:
            bpy.data.objects.remove(obj, do_unlink=True)

        bpy.data.objects.remove(parent, do_unlink=True)

    else:
        raise TypeError(f"Invalid type '{type(parent)}' for parent '{parent.name if parent else None}'")


def find_layer_collection(name: str, layer_collection=None) -> bpy.types.LayerCollection | None:
    """ Recursively traverse layer_collection for a particular name """
    if layer_collection is None:
        layer_collection = bpy.context.view_layer.layer_collection

    if layer_collection.name == name:
        return layer_collection

    for layer in layer_collection.children:
        found = find_layer_collection(name, layer)
        if found:
            return found
    return None


def get_top_parent(obj: bpy.types.Object) -> bpy.types.Object:
    """ Get the top parent of an object """
    if obj.parent:
        return get_top_parent(obj.parent)
    else:
        return obj


def weight_paint_obj_to_bone(obj, armature, bone_name):
    bone = armature.pose.bones.get("head.x")
    if not bone:
        print(f"Warning: Weight Paint failed, bone '{bone_name}' not found in '{armature.name}'!")
        return

    set_active(obj, select=True, deselect_others=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.object.vertex_group_assign_new()
    obj.vertex_groups.active.name = "head.x"
    bpy.ops.object.mode_set(mode="OBJECT")

    # Remove any armature modifiers
    for mod in obj.modifiers:
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)

    # Add new armature modifier
    mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = armature


def find_armature(asset: bpy.types.Object) -> bpy.types.Object:
    # Find the armature object
    armature = None
    for obj in asset.children_recursive:
        if obj.type != "ARMATURE":
            continue
        if obj.name.startswith("rig") or obj.name.startswith("metabull_"):
            armature = obj
            break
    if not armature:
        armature = asset.children[0]
    if not armature:
        armature = asset
    return armature


def find_body_mesh(asset: bpy.types.Object) -> bpy.types.Object:
    mesh = None
    for obj in asset.children_recursive:
        if obj.type != "MESH":
            continue
        if obj.name.startswith("Cliff_body_wip") or obj.name.startswith("metabull_"):
            mesh = obj
            break
    if not mesh:
        mesh = asset.children[0]
    return mesh


def find_actor(actors: dict, name: str) -> bpy.types.Object:
    actor = actors.get(name.lower())
    if not actor:
        print(f"Warning: Actor '{name}' not found! Looking for object with that name instead")
        for obj in bpy.data.objects:
            if obj.name.lower() == name.lower():
                actor = obj
    return actor


class Logger:
    def __init__(self):
        self.logger_client = None
        self.log_group_name = None
        self.log_stream_name = None

    def enable(self, json_file: pathlib.Path):
        try:
            self.log_group_name = 'JSON-uploader-logs'
            self.log_stream_name = json_file.stem
            self.logger_client = boto3.client('logs', region_name='us-east-2')
            self.logger_client.create_log_stream(logGroupName=self.log_group_name, logStreamName=self.log_stream_name)
        except Exception as e:
            print(f"Warning: Failed to log to CloudWatch: {e}")
            self.logger_client = None

    def log(self, msg: str):
        '''
        This Module Writes logs to CloudWatch and prints in console as well
        '''
        # print("LOG: " + msg)

        if not self.logger_client:
            return

        timestamp = int(dt.utcnow().timestamp() * 1000)
        log_event = {
            'timestamp': timestamp,
            'message': msg
        }

        try:
            self.logger_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=[log_event]
            )
        except Exception as e:
            print(f"Warning: Failed to log to CloudWatch: {e}")
            self.logger_client = None


logger = Logger()
