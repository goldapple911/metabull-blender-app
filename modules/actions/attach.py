from math import radians

import bpy
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

        print(f"Attaching '{obj['name']}' to {target}'s bone '{bone_name}'")

        # Get objects
        asset = actors.get(obj["name"])
        target_asset = None
        for name, actor in actors.items():
            if name.lower() == target.lower():
                target_asset = actor
                break
        if not asset:
            raise Exception(f"Actor '{target}' from actions not found.")
        armature = utils.find_armature(target_asset)

        # Set the assets as active
        utils.set_active(asset, select=True, deselect_others=True)

        # Save the armatures rotation and reset it
        armature_rotation = target_asset.rotation_euler.copy()
        target_asset.rotation_euler = Euler((0, 0, 0))

        # Move and rotate the coffe cup to fit the hand
        asset.location = target_asset.location
        asset.location += Vector((0.444931, -0.099295, 0.883269))
        asset.rotation_euler = Euler((
            radians(74.157),
            radians(-10.4915),
            radians(-19.8468)
        ))

        # Add constraint to the asset to keep it on the bone
        constraint = asset.constraints.new(type='CHILD_OF')
        constraint.target = armature
        constraint.subtarget = bone_name
        bpy.ops.constraint.childof_set_inverse(constraint=constraint.name)

        # Restore the armatures rotation
        target_asset.rotation_euler = armature_rotation

