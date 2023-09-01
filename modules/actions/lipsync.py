import bpy
import pathlib
import soundfile
from allosaurus.app import read_recognizer
from .. import utils

import math

arkit_to_visemes = {
    "A": [
        {"name": "Jaw_Open", "weight": 0.35},
        {"name": "Mouth_Close", "weight": 0.1},
    ],
    "E": [
        {"name": "Jaw_Open", "weight": 0.35},
        {"name": "Mouth_Close", "weight": 0.1},
        {"name": "Mouth_Dimple_L", "weight": 0.5},
        {"name": "Mouth_Dimple_R", "weight": 0.5},
        {"name": "Mouth_Shrug_Lower", "weight": -1},
        {"name": "Mouth_Shrug_Upper", "weight": 0.4}
    ],
    "I": [
        {"name": "Jaw_Open", "weight": 0.25},
        {"name": "Mouth_Close", "weight": 0.1},
        {"name": "Mouth_Dimple_L", "weight": 0.8},
        {"name": "Mouth_Dimple_R", "weight": 0.8},
        {"name": "Mouth_Shrug_Lower", "weight": -1},
        {"name": "Mouth_Shrug_Upper", "weight": 0.4}
    ],
    "O": [
        {"name": "Jaw_Open", "weight": 0.4},
        {"name": "Mouth_Close", "weight": 0.1},
        {"name": "Mouth_Funnel_Up_R", "weight": 0.6},
        {"name": "Mouth_Funnel_Up_L", "weight": 0.6},
        {"name": "Mouth_Funnel_Down_R", "weight": 0.6},
        {"name": "Mouth_Funnel_Down_L", "weight": 0.6},
        {"name": "Mouth_Roll_In_Lower_L", "weight": 0.5},
        {"name": "Mouth_Roll_In_Lower_R", "weight": 0.5},
        {"name": "Mouth_Roll_In_Upper_L", "weight": 0.5},
        {"name": "Mouth_Roll_In_Upper_R", "weight": 0.5},
        {"name": "Mouth_Shrug_Upper", "weight": 0.4}
    ],
    "U": [
        {"name": "Jaw_Open", "weight": 0.2},
        {"name": "Mouth_Pucker_Up_R", "weight": 1},
        {"name": "Mouth_Pucker_Up_L", "weight": 1},
        {"name": "Mouth_Pucker_Down_R", "weight": 1},
        {"name": "Mouth_Pucker_Down_L", "weight": 1},
        {"name": "Mouth_Shrug_Upper", "weight": 0.4}
    ],
    "W": [
        {"name": "Jaw_Open", "weight": 0.2},
        {"name": "Mouth_Pucker_Up_R", "weight": 1},
        {"name": "Mouth_Pucker_Up_L", "weight": 1},
        {"name": "Mouth_Pucker_Down_R", "weight": 1},
        {"name": "Mouth_Pucker_Down_L", "weight": 1},
        {"name": "Mouth_Shrug_Upper", "weight": 0.4}
    ],
    "M": [
        {"name": "Mouth_Close", "weight": 0.1},
    ],
    "P": [
        {"name": "Jaw_Open", "weight": 0.1},
        {"name": "Mouth_Pucker_Up_R", "weight": 0.2},
        {"name": "Mouth_Pucker_Up_L", "weight": 0.2},
        {"name": "Mouth_Pucker_Down_R", "weight": 0.2},
        {"name": "Mouth_Pucker_Down_L", "weight": 0.2},
    ],
    "F": [
        {"name": "Jaw_Open", "weight": 0.2},
        {"name": "Mouth_Roll_In_Lower_L", "weight": 0.5},
        {"name": "Mouth_Roll_In_Lower_R", "weight": 0.5},
        {"name": "Mouth_Push_Upper_L", "weight": 0.8},
        {"name": "Mouth_Push_Upper_R", "weight": 0.8},
        {"name": "Mouth_Pull_Upper_L", "weight": 0.4},
        {"name": "Mouth_Pull_Upper_R", "weight": 0.4},
        {"name": "Mouth_Shrug_Upper", "weight": -1.3},
    ],
    "R": [
        {"name": "Jaw_Open", "weight": 0.1},
        {"name": "Mouth_Shrug_Upper", "weight": 0.8}
    ],
    "Y": [
        {"name": "Jaw_Open", "weight": 0.2},
        {"name": "Mouth_Close", "weight": 0.1},
        {"name": "Mouth_Dimple_L", "weight": 0.8},
        {"name": "Mouth_Dimple_R", "weight": 0.8},
        {"name": "Mouth_Shrug_Lower", "weight": -1},
        {"name": "Mouth_Shrug_Upper", "weight": 0.4}
    ],
    "Z": [
        {"name": "Jaw_Open", "weight": 0.1},
        {"name": "Mouth_Pucker_Up_R", "weight": 0.2},
        {"name": "Mouth_Pucker_Up_L", "weight": 0.2},
        {"name": "Mouth_Pucker_Down_R", "weight": 0.2},
        {"name": "Mouth_Pucker_Down_L", "weight": 0.2},
    ],
    "H": [],
    "X": [],
}

shapekey_dict = {
    "A": "VW",
    "E": "VW",
    "I": "VW",
    "O": "VW",
    "U": "VW",
    "W": "CN",
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
    "U": ["u", "uː", "ʊ"],
    "W": ["w"],
    "M": ["m", "n"],
    "P": ["ɵ", "p", "t", "d", "ð", "s", "z", "k", "ŋ", "ɡ", "tʰ"],
    "F": ["b", "f", "v"],
    "R": ["r", "l"],
    "Y": ["y"],
    "Z": ["ʃ", "ʧ", "dʒ", "ʒ", "ɹ", "θ", "ʔ", "x"],
    "H": ["h"],
    "X": ["X"],
}

flag = []


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
        global flag
        flag = [0 for i in range(items_len)]

        for i in range(items_len):
            items = split_array[i].split(" ")
            # Find the parent phoneme
            parent_phoneme = None
            for key, value in phoneme_dict.items():
                if items[2] in value:
                    parent_phoneme = key
                    break
            item = [int(float(items[0]) * fps) + action_start_frame - 2,
                    parent_phoneme, shapekey_dict[parent_phoneme], items[2]]
            pre_phonemes.append(item)

        i = 0
        start_time = 0
        for i in range(items_len):
            if flag[i] == 1:
                continue
            item = pre_phonemes[i]
            if item[2] == "VW":
                out = checkPrevious(i, checkNext(
                    i, pre_phonemes, items_len), pre_phonemes, phonemes)
                during = out[0] - start_time
                out.append(during)
                start_time = out[0]
                phonemes.append(out)
            else:
                if (i + 1 < items_len and pre_phonemes[i + 1][2] == "CN" and pre_phonemes[i - 1][2] == "CN") or i + 1 == items_len:
                    phonemes.append(
                        [item[0], item[1], item[0] - phonemes[-1][0]])

        # Add the lip sync to every mesh in the armature
        for mesh in armature.children_recursive:
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
                # Shapekey anim values
                sk_windup = 4
                sk_min_hold = 5
                sk_winddown = 3

                # Get the shapekey
                shapekey = get_shapekey_from_phoneme(mesh, item[1])
                start_frame = item[0]
                end_frame = start_frame + 6
                if not shapekey:
                    continue
                # End the animation of the previous shapekey

                # Set the shapekey values and save them as keyframes
                if item[2] < 4 or shapekey_dict[item[1][0]] == "VW" or len(item[1]) == 1:
                    if prev_shapekey:
                        prev_shapekey.value = 0.6
                        prev_shapekey.keyframe_insert(
                            data_path="value", frame=start_frame + 2)
                        prev_shapekey.value = 0
                        prev_shapekey.keyframe_insert(
                            data_path="value", frame=start_frame + 4)
                    shapekey.value = 0
                    shapekey.keyframe_insert(
                        data_path="value", frame=start_frame)
                    shapekey.value = 1
                    shapekey.keyframe_insert(
                        data_path="value", frame=start_frame + 2)
                    prev_shapekey = shapekey
                else:
                    prev_shapekey.value = 0.6
                    prev_shapekey.keyframe_insert(
                        data_path="value", frame=start_frame)
                    prev_shapekey.value = 0
                    prev_shapekey.keyframe_insert(
                        data_path="value", frame=start_frame + 2)
                    word_shapekey = get_shapekey_array_from_phoneme(
                        mesh, item[1])
                    word_shapekey[0].value = 0
                    word_shapekey[0].keyframe_insert(
                        data_path="value", frame=start_frame)
                    word_shapekey[0].value = 1
                    word_shapekey[0].keyframe_insert(
                        data_path="value", frame=start_frame + 1)
                    word_shapekey[0].value = 0
                    word_shapekey[0].keyframe_insert(
                        data_path="value", frame=start_frame + 3)
                    word_shapekey[1].value = 0
                    word_shapekey[1].keyframe_insert(
                        data_path="value", frame=start_frame + 1)
                    word_shapekey[1].value = 1
                    word_shapekey[1].keyframe_insert(
                        data_path="value", frame=start_frame + 3)
                    prev_shapekey = word_shapekey[1]

                if mesh.name == "face":
                    print(item)
                # Set frame_end in the scene
                action_end = end_frame + 20
                if bpy.context.scene.frame_end < action_end:
                    bpy.context.scene.frame_end = action_end
                prev_dialogue_end = end_frame

            # End the animation of the last shapekey
            if prev_shapekey:
                prev_shapekey.value = 0.6
                prev_shapekey.keyframe_insert(
                    data_path="value", frame=start_frame + 2)
                prev_shapekey.value = 0
                prev_shapekey.keyframe_insert(
                    data_path="value", frame=start_frame + 4)


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


def get_shapekey_array_from_phoneme(mesh: bpy.types.Object, parent_phoneme: str) -> bpy.types.ShapeKey | None:
    # Get the shapekey name from the parent phoneme
    shapekey_names = parent_phoneme
    if not shapekey_names:
        return None

    # Get the shapekey
    consonant_shapekey = None
    for sk in mesh.data.shape_keys.key_blocks:
        if sk.name == shapekey_names[0]:
            consonant_shapekey = sk
            break

    shapekey_names = shapekey_names[1:]
    body_work_shapekey = None
    for sk in mesh.data.shape_keys.key_blocks:
        if sk.name == shapekey_names:
            body_work_shapekey = sk
            break

    return [consonant_shapekey, body_work_shapekey]


def generate_shapekeys(mesh: bpy.types.Object):
    """If the character is using the ARKit blendshapes, mix them into visemes (mouth shapes)"""

    print(f"Generating viseme shapekeys in {mesh.name} from ARKit blendshapes..")
    utils.set_active(mesh, select=True)

    # Set the shapekey values
    for key, items in arkit_to_visemes.items():
        for item in items:
            name = item["name"]
            weight = item["weight"]
            for sk in mesh.data.shape_keys.key_blocks:
                if sk.name == name:
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


def combine(viseme1, viseme2):
    vise1 = None
    for key, item in arkit_to_visemes.items():
        if key == viseme1:
            vise1 = item
    vise2 = None
    for key, item in arkit_to_visemes.items():
        if key == viseme2:
            vise2 = item

    result = {}
    for item in vise2:
        result[item["name"]] = item["weight"]
    for item in vise1:
        if item["name"] in result.keys():
            if viseme1 in shapekey_dict.keys() and shapekey_dict[viseme1] == "VW":
                result[item["name"]] = result[item["name"]] * \
                    0.2 + item["weight"] * 0.93
            else:
                result[item["name"]] = result[item["name"]] * \
                    0.93 + item["weight"] * 0.12
        else:
            result[item["name"]] = item["weight"]

    out = []
    for key in result:
        out.append({"name": key, "weight": result[key]})
    arkit_to_visemes[viseme1 + viseme2] = out
    return viseme1 + viseme2


# checkPrevious(i, checkNext(i, pre_phonemes, items_len), pre_phonemes, phonemes)
def checkPrevious(index, mouthFormat, pre_phonemes, phonemes):
    item = pre_phonemes[index]
    if index == 0:
        return [item[0], mouthFormat]

    pre_item = pre_phonemes[index - 1]
    if pre_item[2] != "CN":
        return [item[0], mouthFormat]

    if flag[index - 1] == 1:
        return [item[0], mouthFormat]

    flag[index - 1] = 1
    if item[0] - pre_item[0] > 2:
        phonemes.append([pre_item[0], pre_item[1],
                        pre_item[0] - phonemes[-1][0]])
        return [item[0], mouthFormat]

    flag[index] = 1
    return [pre_item[0], combine(pre_item[1], mouthFormat)]


def checkNext(index, pre_phonemes, items_len):
    item = pre_phonemes[index]
    if index + 2 > items_len:
        return item[1]

    next_item = pre_phonemes[index + 1]
    if next_item[2] != "CN":
        return item[1]

    if next_item[0] - item[0] > 2:
        return item[1]

    if flag[index + 1] == 1:
        return item[1]

    flag[index + 1] = 1
    return combine(item[1], next_item[1])
