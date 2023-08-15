
import bpy
import os
import time
from .. import utils


# def copy_keyframes(source, target, start_frame, end_frame):
#     if not source.animation_data:
#         raise Exception("Source armature has no animation data.")
#     source_action = source.animation_data.action
#
#     if not target.animation_data:
#         target.animation_data_create()
#         # Create new action if target has no action
#     target_action = bpy.data.actions.new(name=source_action.name)
#     target.animation_data.action = target_action
#
#     for source_fcurve in source_action.fcurves:
#         data_path = source_fcurve.data_path
#         array_index = source_fcurve.array_index
#
#         # Check if FCurve already exists in the target action
#         target_fcurve = target_action.fcurves.find(data_path, index=array_index)
#
#         if target_fcurve is None:
#             # Create a new FCurve in the target action
#             target_fcurve = target_action.fcurves.new(data_path, index=array_index)
#
#         if not source_fcurve.keyframe_points:
#             continue
#
#         # Copy keyframes from source to target
#         for source_keyframe in source_fcurve.keyframe_points:
#             frame = source_keyframe.co.x
#             current_length = frame - source_fcurve.keyframe_points[0].co.x
#             if current_length >= end_frame:
#                 break
#
#             target_keyframe = target_fcurve.keyframe_points.insert(frame + start_frame, source_keyframe.co.y)
#             target_keyframe.interpolation = source_keyframe.interpolation
#             target_keyframe.handle_left = source_keyframe.handle_left
#             target_keyframe.handle_right = source_keyframe.handle_right
#
#
# def copy_keyframes2(source, target, start_frame, end_frame):
#     for bone in source.pose.bones:
#         if not bone.name.startswith("mix"):
#             continue
#         # print("Copying bone", bone.name)0
#
#         target_bone = target.pose.bones.get(bone.name)
#         if not target_bone:
#             print(f"Target bone '{bone.name}' not found")
#             continue
#
#         # Add a rotation constraint to the target bone
#         constraint = target_bone.constraints.new(type='COPY_ROTATION')
#         constraint.target = source
#         constraint.subtarget = bone.name
#
#     # Move the keyframes back a few frames
#     action = source.animation_data.action
#     for curve in action.fcurves:
#         for kf in reversed(curve.keyframe_points):
#             kf.co[0] += start_frame
#
#
# def find_armature_and_parent_to_bone(fbx_file, acc_child=None):
#     # Import the FBX object
#     bpy.ops.import_scene.fbx(filepath=fbx_file)
#     fbx_object = bpy.context.selected_objects[0]
#
#     # Find the first ARMATURE object
#     armature_obj = None
#     for obj in bpy.data.objects:
#         if obj.type == 'ARMATURE':
#             armature_obj = obj
#             break
#
#     if armature_obj is None:
#         print("No ARMATURE object found.")
#         return
#
#     # Extract the substring from the fbx_file string
#     file_name = os.path.splitext(os.path.basename(fbx_file))[0]
#     acc_name = file_name.rsplit("_", 2)[-2]
#
#     print(f"Accessory '{acc_name}' found.")
#     time.sleep(1)
#
#     # Find the bone containing the specified string
#     bone_name = None
#     for bone in armature_obj.pose.bones:
#         if acc_name in bone.name:
#             bone_name = bone.name
#             break
#
#     if bone_name is None:
#         print(f"No bone containing '{bone_name}' found.")
#         return
#
#     bone = armature_obj.pose.bones.get(bone_name)
#
#     if bone is not None:
#         # Get the FBX object
#
#         # Parent the FBX object to the bone
#         fbx_object.parent = armature_obj
#         fbx_object.parent_type = 'BONE'
#         fbx_object.parent_bone = bone_name
#
#         # Clear any existing parent-child relationships
#         fbx_object.matrix_parent_inverse.identity()
#
#         # Set the child object's position to match the parent bone's head position
#         fbx_object.location = armature_obj.matrix_world @ bone.head
#
#         # Set the child object's rotation to match the parent bone's orientation
#         fbx_object.rotation_euler = bone.matrix.to_euler()
#
#         # Set the child object's scale to match the parent bone's scale
#         #fbx_object.scale = bone.scale


def retarget(actors: dict, actions: list[dict]):
    # Filter the animations per actor down to one
    actions_tmp = []
    for actor_name in actors.keys():
        action_tmp = None
        # Search for the drinking animation and use only that
        for action in actions:
            if action["type"] != "ANIM" or actor_name.lower() != action["actor"].lower():
                continue
            if "drinking" in action["file"].lower():
                action["file"] = "/animations/Idle_cup_holding.fbx"  # TODO: Remove this
                action_tmp = action
                break

        # If no drinking anim was found, only use the first anim
        if not action_tmp:
            for action in actions:
                if action["type"] != "ANIM" or actor_name.lower() != action["actor"].lower():
                    continue
                action_tmp = action
                break

        if action_tmp:
            actions_tmp.append(action_tmp)

    # Retarget each action
    for action in actions_tmp:
        action_type = action["type"]
        action_actor = action["actor"]
        if action_type != "ANIM" or not action_actor:
            continue

        action_start_frame = action["start_time"]
        action_end_frame = action["end_time"]

        # get the actor objects, ignoring upper and lower case
        asset = utils.find_actor(actors, action_actor)
        if not asset:
            raise Exception(f"Actor '{action_actor}' from actions not found.")

        # Get the armature object
        armature = utils.find_armature(asset)
        if not armature:
            raise Exception("No armature found in imported file.")

        # If the armature is v4, skip it currently TODO
        # if armature.name.endswith("rig_v4"):
        #     print("Skipping retargeting v4 armature:", action_actor)
        #     continue

        # Get the animations file
        anim_file = utils.get_resource(action["file"])
        print(f"Adding animation '{anim_file.name}' to actor '{action_actor}', armature: '{armature.name}'")
        anim = utils.import_file(anim_file)
        anim.name = "Anim Armature"

        # Get the data for the current actor
        anim.location = asset.location
        # anim.rotation_euler[0] = asset.rotation_euler[0]
        # anim.rotation_euler[1] = asset.rotation_euler[1]
        # anim.rotation_euler[2] = asset.rotation_euler[2]
        dimension_comparison = anim.dimensions[1] * armature.dimensions[1]
        if dimension_comparison < 0.2 or dimension_comparison > 20:
            anim.scale = asset.scale

        # Retarget animation to the actor
        # copy_keyframes(source=anim, target=armature, start_frame=action_start_frame, end_frame=action_end_frame)
        retarget_arp(source=anim, target=armature)

        # Delete anim object
        utils.delete_hierarchy(anim)


def retarget_arp(source, target):
    # Get the top parent of the target and reset its rotation
    target_parent = utils.get_top_parent(target)
    rot_tmp = target_parent.rotation_euler.copy()
    target_parent.rotation_euler = (0, 0, 0)

    # Set the armature to a t-pose with ARP
    utils.set_active(target, select=True, deselect_others=True)
    bpy.ops.arp.set_pose("EXEC_DEFAULT", pose_type="TPOSE")

    # Setup ARP for retargeting
    bpy.context.scene.source_rig = source.name
    bpy.context.scene.target_rig = target.name

    bpy.ops.arp.build_bones_list()

    # Loop over the bone list items to set the root as root
    for i, item in enumerate(bpy.context.scene.bones_map.values()):
        if "root" in item.name:
            bpy.context.scene.bones_map_index = i
            item.set_as_root = True
            break

    # Redefine rest pose
    bpy.ops.arp.redefine_rest_pose("EXEC_DEFAULT")
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.arp.copy_bone_rest()
    bpy.ops.arp.save_pose_rest()

    # Retarget animation
    frame_start = int(source.animation_data.action.frame_range[0])
    frame_end = int(source.animation_data.action.frame_range[1])
    bpy.ops.arp.retarget("EXEC_DEFAULT",
                         frame_start=frame_start,
                         frame_end=frame_end,
                         freeze_source="YES",
                         freeze_target="YES")

    # Leave pose mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Restore the rotation of the top parent
    target_parent.rotation_euler = rot_tmp

