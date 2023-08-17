
import bpy
from .. import utils

arkit_to_emotion = {
    "HAPPY": [{"name": "mouthSmileLeft", "weight": 0.7},  # TODO: Change both back to 0.6
              {"name": "mouthSmileRight", "weight": 0.7},
              {"name": "eyeSquintLeft", "weight": 1},
              {"name": "eyeSquintRight", "weight": 1},
              {"name": "cheekSquintLeft", "weight": 1},
              {"name": "cheekSquintRight", "weight": 1},
              ],
    "SAD": [{"name": "mouthFrownRight", "weight": 0.7},
            {"name": "mouthFrownLeft", "weight": 0.7},
            {"name": "browDownLeft", "weight": 1},
            {"name": "browDownRight", "weight": 1},
            {"name": "browInnerUp", "weight": 1},
            ],
    "ANGRY": [{"name": "mouthUpperUpLeft", "weight": 1},
              {"name": "browInnerUp", "weight": -2},
              ],
    "LESS_ANGRY": [{"name": "mouthUpperUpLeft", "weight": 0.3},
        {"name": "mouthUpperUpRight", "weight": 0.3},
              {"name": "browInnerUp", "weight": -1},
              ],
    "DISGUST": [{"name": "mouthFrownLeft", "weight": 1},
                {"name": "mouthFrownRight", "weight": 1},
                {"name": "mouthShrugLower", "weight": -1},
                {"name": "mouthShrugUpper", "weight": 0.6},
                {"name": "browDownLeft", "weight": 1.5},
                {"name": "browDownRight", "weight": 1.7},
                ],
    "FEARFUL": [{"name": "eyeWideLeft", "weight": 1},
                {"name": "eyeWideRight", "weight": 1},
                {"name": "jawOpen", "weight": 0.5},
                {"name": "mouthFrownLeft", "weight": 1},
                {"name": "mouthFrownRight", "weight": 1},
                {"name": "browInnerUp", "weight": 1},
                ],
    "SURPRISED": [{"name": "eyeWideLeft", "weight": 1},
                  {"name": "eyeWideRight", "weight": 1},
                  {"name": "jawOpen", "weight": 0.6},
                  {"name": "mouthSmileLeft", "weight": 0.2},
                  {"name": "mouthSmileRight", "weight": 0.2},
                  {"name": "browInnerUp", "weight": 1},
                  {"name": "browOuterUpLeft", "weight": 1},
                  {"name": "browOuterUpRight", "weight": 1},
                  ],
}


def add_emotions(actors: dict, actions: list[dict]):
    # Go over all emotion actions
    for action in actions:
        action_type = action["type"]
        if action_type != "EMOTION":
            continue

        action_actor = action["actor"]
        action_start_frame = action["start_time"]
        action_end_frame = action["end_time"]
        action_emotion = action["emotion"]

        if not action_actor or not action_emotion:
            return

        # get the actor objects, ignoring upper and lower case
        asset = utils.find_actor(actors, action_actor)
        if not asset:
            raise Exception(f"Actor '{action_actor}' from actions not found.")

        # Get the armature containing all the meshes
        armature = utils.find_armature(asset)
        if not armature:
            raise Exception("No armature found in imported file.")

        for mesh in armature.children_recursive:
            if mesh.type != "MESH" or not mesh.data.shape_keys:
                continue
            if mesh.name not in bpy.context.view_layer.objects:
                continue

            # Generate missing shapekeys if the model has the ARKit blendshapes
            shapekey = generate_emotion_shapekey(mesh, action_emotion)
            if not shapekey:
                continue

            # Add the emotion as a shapekey to the animation
            # Set the shapekey values and save them as keyframes
            shapekey.value = 0
            shapekey.keyframe_insert(data_path="value", frame=action_start_frame)
            shapekey.value = 1
            shapekey.keyframe_insert(data_path="value", frame=action_start_frame + 2)
            shapekey.value = 1
            shapekey.keyframe_insert(data_path="value", frame=action_end_frame - 2)
            shapekey.value = 0
            shapekey.keyframe_insert(data_path="value", frame=action_end_frame)

            # # Set frame_end in the scene
            action_end = action_end_frame + 10
            if bpy.context.scene.frame_end < action_end:
                bpy.context.scene.frame_end = action_end


def generate_emotion_shapekey(mesh: bpy.types.Object, emotion: str):
    # If the character is using the ARKit blendshapes, mix them into visemes
    if "mouthFunnel" not in mesh.data.shape_keys.key_blocks \
            or "mouthRollLower" not in mesh.data.shape_keys.key_blocks:
        return
    # If the character already has the generated shapekey, return
    if emotion in mesh.data.shape_keys.key_blocks:
        return mesh.data.shape_keys.key_blocks[emotion]

    if emotion not in arkit_to_emotion:
        print(f"Emotion '{emotion}' not supported currently.")

    print(f"Generating emotion shapekey {emotion} from ARKit blendshapes..")

    utils.set_active(mesh, select=True)

    # Set the shapekey values for the emotion
    for item in arkit_to_emotion[emotion]:
        name = item["name"]
        weight = item["weight"]
        for sk in mesh.data.shape_keys.key_blocks:
            if sk.name == name:
                sk.slider_min = -5
                sk.slider_max = 5
                sk.value = weight
                break

    # Save the mix of current shapekeys as a new shapekey
    bpy.ops.object.shape_key_add(from_mix=True)
    shapekey = mesh.data.shape_keys.key_blocks[-1]

    # Rename this shapekey
    shapekey.name = emotion

    # Clear the shapekeys
    for sk in mesh.data.shape_keys.key_blocks:
        if sk.value != 0:
            sk.value = 0

    return shapekey
