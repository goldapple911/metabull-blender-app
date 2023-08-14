from math import radians

import bpy
import numpy as np
from mathutils import Vector, Euler
from .. import utils


def attach(actors, data):
    # Attach objects to the armature

    # Loop over all objects to see if they should be attached
    obj_data = data["scene"]["objects"]
    for obj in obj_data:
        target = obj.get("actor")
        bone_name = "c_middle1_base.l"  # TODO: obj.get("bone_name")
        if not target or not bone_name:
            continue

        use_right_hand = False
        bone_name_actual = obj.get("bone_name")
        if bone_name_actual and "right" in bone_name_actual.lower():
            bone_name = "c_middle1_base.r"
            use_right_hand = True

        print(f"Attaching '{obj['name']}' to {target}'s bone '{bone_name}'")

        # Get objects
        asset = utils.find_actor(actors, obj["name"])
        target_asset = utils.find_actor(actors, target)
        if not target_asset:
            raise Exception(f"Actor '{target}' from actions not found.")
        armature = utils.find_armature(target_asset)

        # Set the assets as active
        utils.set_active(asset, select=True, deselect_others=True)

        # Save the armatures rotation and reset it
        armature_rotation = target_asset.rotation_euler.copy()
        target_asset.rotation_euler = Euler((0, 0, 0))

        # Get the global location of the bone
        # bone = armature.pose.bones[bone_name]
        # bone_location = get_global_bone_loc(armature, bone_name)
        # print("Bone location:", bone_location)
        # bone_location = armature.matrix_world @ bone.matrix @ Vector((0, 0, 0))
        # print("Bone location2:", bone_location)

        # Move and rotate the coffe cup to fit the hand

        # Find the actor in the data
        # TODO Remove this, it's a temp fix
        actor_data = None
        for actor in data["scene"]["actors"]:
            if actor["name"].lower() == target.lower():
                actor_data = actor
                break

        # Move the cup to the hand, very hacky
        # TODO Remove this, all chars should have the same pose
        if "sarge" not in actor_data["file"].lower():
            # A-pose cup holding
            asset.location = target_asset.location
            asset.location += Vector((0.444931, -0.099295, 0.883269))
            asset.rotation_euler = Euler((
                radians(74.157),
                radians(-10.4915),
                radians(-19.8468)
            ))
            if use_right_hand:
                asset.location[0] += 2 * -0.444931 + 0.01
                asset.rotation_euler[2] = -asset.rotation_euler[2]
        else:
            # T-pose cup holding
            asset.location = target_asset.location
            asset.location += Vector((0.834368, 0.133904, 1.45931))
            asset.rotation_euler = Euler((
                radians(91.558),
                radians(-3.82921),
                radians(-2.17623)
            ))

        # Add constraint to the asset to keep it on the bone
        constraint = asset.constraints.new(type='CHILD_OF')
        constraint.target = armature
        constraint.subtarget = bone_name
        bpy.ops.constraint.childof_set_inverse(constraint=constraint.name)

        # Restore the armatures rotation
        target_asset.rotation_euler = armature_rotation


def get_global_bone_loc(armature, bone_name):
    R = armature.matrix_world.to_3x3()
    R = np.array(R)

    t = armature.matrix_world.translation
    t = np.array(t)

    print(f"R = {R.shape}\n{R}")
    print(f"t = {t.shape}\n{t}")

    local_location = armature.data.bones[bone_name].head_local
    local_location = np.array(local_location)
    print(f"local position = {local_location.shape}\n{local_location}")

    loc = np.dot(R, local_location) + t
    print(f"final loc = {loc.shape}\n{loc}")

    return [loc[0], loc[1], loc[2]]