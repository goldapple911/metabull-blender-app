
import bpy
import pathlib
import soundfile
from allosaurus.app import read_recognizer
from .. import utils

arkit_to_visemes = {
    "A": [
            {"name": "jawOpen", "weight": 0.4},
            {"name": "mouthClose", "weight": 0.1},
        ],
    "E": [
            {"name": "jawOpen", "weight": 0.27},
            {"name": "mouthClose", "weight": 0.1},
            {"name": "mouthDimpleLeft", "weight": 0.5},
            {"name": "mouthDimpleRight", "weight": 0.5},
            {"name": "mouthShrugLower", "weight": -1},
            {"name": "mouthShrugUpper", "weight": 0.4}
        ],
    "I": [
            {"name": "jawOpen", "weight": 0.2},
            {"name": "mouthClose", "weight": 0.1},
            {"name": "mouthDimpleLeft", "weight": 0.7},
            {"name": "mouthDimpleRight", "weight": 0.7},
            {"name": "mouthShrugLower", "weight": -1},
            {"name": "mouthShrugUpper", "weight": 0.4}
        ],
    "O": [
            {"name": "jawOpen", "weight": 0.3},
            {"name": "mouthClose", "weight": 0.1},
            {"name": "mouthFunnel", "weight": 1},
            {"name": "mouthShrugUpper", "weight": 0.4}
        ],
    "U": [
            {"name": "jawOpen", "weight": 0.15},
            {"name": "mouthClose", "weight": 0.1},
            {"name": "mouthPucker", "weight": 1},
            {"name": "mouthShrugUpper", "weight": 0.4}
        ],
    "M": [
            {"name": "jawOpen", "weight": 0.05},
            {"name": "mouthShrugUpper", "weight": 1}
        ],
    "P": [
            {"name": "jawOpen", "weight": 0.05},
            {"name": "mouthShrugLower", "weight": 0},
        ],
    "F": [
            {"name": "jawOpen", "weight": 0.25},
            {"name": "mouthShrugUpper", "weight": 0.6}
        ],
    "R": [
            {"name": "jawOpen", "weight": 0.1},
            {"name": "mouthShrugUpper", "weight": 0.8}
        ],
    "Y": [
            {"name": "jawOpen", "weight": 0.3},
            {"name": "mouthClose", "weight": 0.1},
            {"name": "mouthDimpleLeft", "weight": 0.7},
            {"name": "mouthDimpleRight", "weight": 0.7},
            {"name": "mouthShrugLower", "weight": -1},
            {"name": "mouthShrugUpper", "weight": 0.4}
        ],
    "Z": [
            {"name": "jawOpen", "weight": 0.1},
            {"name": "mouthShrugLower", "weight": -1},
        ],
    "H": [],
    "X": [],
}

flag = []

def add_lip_sync(actors: dict, actions: list[dict]):
    # Load lip sync model
    model = read_recognizer()

    fps = bpy.context.scene.render.fps
    prev_dialogue_end = 0
    
    shapekey_dict = {
        "A": "VW",
        "E": "VW",
        "I": "VW",
        "O": "VW",
        "U": "VW",
        "M": "CN",
        "P": "CN",
        "F": "CN",
        "R": "CN",
        "Y": "CN",
        "Z": "CN",
        "H": "CN",
        "X": "X",
    }
    phoneme_dict = {
        "A": ["a", "ɑ", "ɒ", "ʌ"],
        "E": ["e", "æ", "ɛ", "ɚ"],
        "I": ["i", "ɪ", "iː", "j"],
        "O": ["ɔ", "o", "ə", "ɜ"],
        "U": ["u", "uː", "ʊ", "w"],
        "M": ["m", "n"],
        "P": ["ɵ","p", "t", "d", "ð", "s", "z", "k", "ŋ", "ɡ", "tʰ"],
        "F": ["b", "f", "v"],
        "R": ["r", "l"],
        "Y": ["y"],
        "Z": ["ʃ", "ʧ", "dʒ", "ʒ", "ɹ", "θ", "ʔ", "x"],
        "H": ["h"],
        "X": ["X"],
    }

    for action in actions:
        action_type = action["type"]
        if action_type != "AUDIO":
            continue

        action_actor = action["actor"]
        action_start_frame = action["start_time"]
        audio_file = utils.get_resource(action["file"])

        # If the audio would overlay the previous dialogue, move it forward
        if action_start_frame < prev_dialogue_end:
            action_start_frame = prev_dialogue_end + 20

        # Place sound at the sequence strip
        se = bpy.context.scene.sequence_editor
        se.sequences.new_sound("Lip Sync Sound", str(audio_file), channel=1, frame_start=action_start_frame)

        if not action_actor:
            return

        # get the actor objects, ignoring upper and lower case
        asset = utils.find_actor(actors, action_actor)
        if not asset:
            raise Exception(f"Actor '{action_actor}' from actions not found.")

        # Get the armature containing all the meshes
        armature = utils.find_armature(asset)
        if not armature:
            raise Exception("No armature found in imported file.")

        # Read the audio file
        print("Reading audio:", audio_file)
        results = None
        try:
            results = model.recognize(audio_file, lang_id="eng", timestamp=True)
        except Exception as e:
            print("Couldn't reading audio, re-encoding file..")

        # If there was an error reading the audio, try again by reencoding the audio file
        if not results:
            # Read and rewrite the file with soundfile to make sure it's readable by the recognizer
            file_path = audio_file
            audio_file_2 = str(audio_file).replace(".wav", "_2.wav")
            data, samplerate = soundfile.read(file_path)
            soundfile.write(audio_file_2, data, samplerate)
            audio_file = pathlib.Path(audio_file_2)

            try:
                results = model.recognize(audio_file, lang_id="eng", timestamp=True)
            except Exception as e:
                # Read and rewrite the file with soundfile to make sure it's readable by the recognizer
                print("[ERROR] Error reading audio:", e)
                return

        # Turn results from the audio file voice recognition into a phoneme list (start, duration, phoneme)
        pre_phonemes = []
        phonemes = []
        split_array = results.split("\n")
        items_len = len(split_array)

        for i in range(items_len):
            items = split_array[i].split(" ")
            # Find the parent phoneme
            parent_phoneme = None
            for key, value in phoneme_dict.items():
                if items[2] in value:
                    parent_phoneme = key
                    break
            item = (float(items[0]), parent_phoneme, shapekey_dict[parent_phoneme], items[2])
            print(item)
            pre_phonemes.append(item)

        # Add the lip sync to every mesh in the armature
        for mesh in armature.children:
            if mesh.type != "MESH" or not mesh.data.shape_keys:
                continue
            if mesh.name not in bpy.context.view_layer.objects:
                continue

            # Generate missing face shapekeys if the mesh has the ARKit blendshapes
            generate_shapekeys(mesh)

            # Add every phoneme as a shapekey to the animation
            prev_shapekey = None
            start_frame = 0
            for item in pre_phonemes:
                # Get the shapekey
                shapekey = get_shapekey_from_phoneme(mesh, item[1])
                start_frame = int(item[0] * fps) + action_start_frame - 3
                end_frame = start_frame + 6

                if not shapekey:
                    continue

                # End the animation of the previous shapekey
                if prev_shapekey:
                    prev_shapekey.value = 0.6
                    prev_shapekey.keyframe_insert(data_path="value", frame=start_frame + 1)
                    prev_shapekey.value = 0
                    prev_shapekey.keyframe_insert(data_path="value", frame=start_frame + 2)

                # Set the shapekey values and save them as keyframes
                shapekey.value = 0
                shapekey.keyframe_insert(data_path="value", frame=start_frame)
                shapekey.value = 1
                shapekey.keyframe_insert(data_path="value", frame=start_frame + 2)
                prev_shapekey = shapekey

                # Set frame_end in the scene
                action_end = end_frame + 20
                if bpy.context.scene.frame_end < action_end:
                    bpy.context.scene.frame_end = action_end
                prev_dialogue_end = end_frame

            # End the animation of the last shapekey
            if prev_shapekey:
                prev_shapekey.value = 0.6
                prev_shapekey.keyframe_insert(data_path="value", frame=start_frame + 2)
                prev_shapekey.value = 0
                prev_shapekey.keyframe_insert(data_path="value", frame=start_frame + 4)


def get_shapekey_from_phoneme(mesh: bpy.types.Object, parent_phoneme: str) -> bpy.types.ShapeKey | None:
    # Get the shapekey name from the parent phoneme
    shapekey_names = parent_phoneme
    if not shapekey_names:
        return None

    # Get the shapekey
    shapekey = None
    for sk in mesh.data.shape_keys.key_blocks:
        if sk.name == shapekey_names:
            shapekey = sk
            break

    return shapekey


def generate_shapekeys(mesh: bpy.types.Object):
    """If the character is using the ARKit blendshapes, mix them into visemes (mouth shapes)"""

    # Return if the character doesn't have the ARKit shapekeys
    if "mouthClose" not in mesh.data.shape_keys.key_blocks \
            or "jawOpen" not in mesh.data.shape_keys.key_blocks:
        return
    # If the character already has the generated visemes, return
    if "A" in mesh.data.shape_keys.key_blocks \
            or "Z" in mesh.data.shape_keys.key_blocks:
        return

    print(f"Generating viseme shapekeys in {mesh.name} from ARKit blendshapes..")
    utils.set_active(mesh, select=True)

    # Set the shapekey values
    for key, items in arkit_to_visemes.items():
        for item in items:
            name = item["name"]
            weight = item["weight"]
            for sk in mesh.data.shape_keys.key_blocks:
                if sk.name == name:
                    sk.slider_min = -1
                    sk.value = weight
                    break

        # Save the current shapekeys as a new shapekey
        bpy.ops.object.shape_key_add(from_mix=True)

        # Rename this shapekey
        mesh.data.shape_keys.key_blocks[-1].name = key

        # Clear the shapekeys
        for sk in mesh.data.shape_keys.key_blocks:
            if sk.value != 0:
                sk.value = 0
