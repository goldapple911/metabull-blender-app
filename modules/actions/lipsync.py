
import bpy
import pathlib
import soundfile
from allosaurus.app import read_recognizer
from .. import utils

# 
arkit_to_visemes = {
    "A": [{"name": "jawOpen", "weight": 0.4}],
    "Ch": [{"name": "mouthFunnel", "weight": 0.8}],
    "E": [{"name": "jawOpen", "weight": 0.2},
          {"name": "mouthClose", "weight": 0.1},
          {"name": "mouthDimpleLeft", "weight": 0.5},
          {"name": "mouthDimpleRight", "weight": 0.5},
          {"name": "mouthShrugLower", "weight": -1},
          {"name": "mouthShrugUpper", "weight": 0.4}],
    "F": [{"name": "jawOpen", "weight": 0.25},
          {"name": "mouthClose", "weight": 0.1},
          {"name": "mouthRollLower", "weight": 0.7},
          {"name": "mouthRollUpper", "weight": 0.1}],
    "P": [{"name": "jawOpen", "weight": 0.3},
          {"name": "mouthClose", "weight": 0.35},
          {"name": "mouthPucker", "weight": -0.8}],
    "L": [{"name": "jawOpen", "weight": 0.4}],
    "O": [{"name": "jawOpen", "weight": 0.35},
          {"name": "mouthClose", "weight": 0.25},
          {"name": "mouthFunnel", "weight": 0.8}],
    "U": [{"name": "jawOpen", "weight": 0.15},
          {"name": "mouthClose", "weight": 0.25},
          {"name": "mouthFunnel", "weight": 0.8}],
    "X": [],
}


def add_lip_sync(actors: dict, actions: list[dict]):
    # Load lip sync model
    model = read_recognizer()

    fps = bpy.context.scene.render.fps
    prev_dialogue_end = 0

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

        # Reread the audio file
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

        # Turn results fro mthe audio file voice recognition into a phoneme list (start, duration, phoneme)
        phonemes = []
        for phoneme_item in results.split("\n"):
            items = phoneme_item.split(" ")
            item = (float(items[0]), float(items[1]), items[2])
            phonemes.append(item)
        # print(phonemes)

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
            for item in phonemes:
                # Get the shapekey
                shapekey = get_shapekey_from_phoneme(mesh, item[2])
                start_frame = int(item[0] * fps) + action_start_frame - 2
                # end_frame = int((item[0] + item[1]) * 24)
                end_frame = start_frame + 6

                # print(shapekey, start_frame, end_frame, item)
                if not shapekey:
                    continue

                # End the animation of the previous shapekey
                if prev_shapekey:
                    prev_shapekey.value = 0.6
                    prev_shapekey.keyframe_insert(data_path="value", frame=start_frame + 2)
                    prev_shapekey.value = 0
                    prev_shapekey.keyframe_insert(data_path="value", frame=start_frame + 4)

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


def get_shapekey_from_phoneme(mesh: bpy.types.Object, phoneme: str) -> bpy.types.ShapeKey | None:
    phoneme_dict = {
        "A": ["a", "ɒ", "ʌ", "x", "ɾ", "ɾʲ", "ɛ", "h", "ɑ"],
        "Ch": ["ch", "k", "d", "n", "ŋ", "ɡ", "d͡ʒ", "ɴ", "kʰ", "ɳ", "dʒ", "k̟ʲ", "ɲ", "ŋ̟", "dʲ", "t", "tʰ"],
        "E": ["e", "i", "j", "s", "ʃ", "z", "iː", "c", "zʲ", "s̪", "ʂ", "ʒ", "ɨ", "ʐ", "ə", "ɪ", "æ"],
        "F": ["f", "v", "ɯ", "y", "ʏ"],
        "P": ["p", "b", "m", "p", "mʲ", "b̞", "b̤", "pʲ"],
        "L": ["l", "ð", "ɔ", "lʲ", "l̪"],
        "O": ["o"],
        "U": ["u", "w", "uː", "uə", "œ"],
        "X": ["X"],  # X means silent
    }
    shapekey_dict = {
        "A": "Ah",
        "Ch": "Ch",
        "E": "E",
        "F": "U",
        "P": "Mouth wo Upper",
        "L": "E",
        "O": "Oh",
        "U": "U",
        "X": "Silent",
    }

    # Find the parent phoneme
    parent_phoneme = None
    for key, value in phoneme_dict.items():
        if phoneme in value:
            parent_phoneme = key
            break

    # Get the shapekey name from the parent phoneme
    shapekey_names = [parent_phoneme, shapekey_dict.get(parent_phoneme)]
    if not shapekey_names:
        return None

    # Get the shapekey
    shapekey = None
    for sk in mesh.data.shape_keys.key_blocks:
        if sk.name in shapekey_names:
            shapekey = sk
            break

    return shapekey


def generate_shapekeys(mesh: bpy.types.Object):
    """If the character is using the ARKit blendshapes, mix them into visemes (mouth shapes)"""

    # Return if the character doesn't have the ARKit shapekeys
    if "mouthFunnel" not in mesh.data.shape_keys.key_blocks \
            or "mouthRollLower" not in mesh.data.shape_keys.key_blocks:
        return
    # If the character already has the generated visemes, return
    if "Ch" in mesh.data.shape_keys.key_blocks \
            or "L" in mesh.data.shape_keys.key_blocks:
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

