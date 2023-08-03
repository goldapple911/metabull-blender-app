
import os
import re
import bpy
import json
import openai
import traceback

# prompt_test = "Place 10 large cubes in a circle"
# prompt_test = "Place Cliff on top of one of the tables and place the camera in front of him pointing at Cliff"
# prompt_test = "Delete Cliffs animation and create a new animation which makes him walk to the table and sit down"
prompt_test = "Create two cubes. Animate them to collide with each other."
# prompt_test = "Find the armature of Cliff, which is a child of the object called Cliff. Animate the hand of Cliffs armature to move in a circle"


max_error_retries = 5

gpt_model = "gpt-3.5-turbo-16k"
# gpt_model = "gpt-4"
api_key = "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"
# api_key = "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"
chat_history = []

system_prompt = """You are an assistant made for the purposes of helping the user with Blender, the 3D software. 
- Respond with your answers in markdown (```). 
- Preferably import entire modules instead of bits. 
- Do not perform destructive operations on the meshes. 
- Do not use cap_ends. Do not do more than what is asked (setting up render settings, adding cameras, etc)
- Do not respond with anything that is not Python code.

Example:

user: create 10 cubes in random locations from -10 to 10
assistant:
```
import bpy
import random
bpy.ops.mesh.primitive_cube_add()

# how many cubes you want to add
count = 10

for c in range(0, count):
    x = random.randint(-10, 10)
    y = random.randint(-10, 10)
    z = random.randint(-10, 10)
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
```
"""


def generate(self):
    openai.api_key = api_key
    # if null then set to env key
    if not openai.api_key:
        openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise Exception("No API key detected")

    print("Available models:")
    print(sorted([model["id"] for model in openai.Model.list()["data"] if "gpt" in model["id"]]))

    print()
    print("INFO: GPT Prompt:")
    print(f"  {prompt_test}")

    # Push the prompt to ChatGPT and get the response as blender code
    blender_code = generate_blender_code(prompt_test)
    blender_code_formatted = blender_code.split("\n")

    # Print the code
    print("Executing code...")
    print("---------------------------")
    for i, line in enumerate(blender_code_formatted):
        print(f"{i+1:3}:  {line}")
    print("---------------------------")

    # Create two restore points, because using undo will delete the second one and goes back to the first one
    bpy.ops.ed.undo_push(message="Pre Pre Generated Code")
    bpy.ops.ed.undo_push(message="Pre Generated Code")

    # print undo history
    # bpy.context.window_manager.print_undo_steps()

    # Try executing the blender code
    error = None
    try:
        exec(blender_code)
    except Exception:
        error = clean_error(traceback.format_exc(), blender_code_formatted)
        print(error)
        print("---------------------------")
        # bpy.context.window_manager.print_undo_steps()
        print("FIRST UNDO")
        bpy.ops.ed.undo()
        # bpy.context.window_manager.print_undo_steps()

    # If there was an error, send the error to ChatGPT and execute the new code
    for i in range(max_error_retries):
        if not error:
            break
        # Send the error to ChatGPT and get the response as blender code
        blender_code = fix_blender_code(error)
        blender_code_formatted = blender_code.split("\n")

        # Print the newly fixed code
        print(f"Executing fixed code attempt #{i + 1} ...")
        print("---------------------------")
        for j, line in enumerate(blender_code_formatted):
            print(f"{j + 1:3}:  {line}")
        print("---------------------------")

        # Create another restore point
        bpy.ops.ed.undo_push(message=f"Pre Generated Code {i+1}")

        # Try executing the blender code again, if it fails, repeat up to a max number of retries
        try:
            exec(blender_code)
            error = None
        except Exception:
            error = clean_error(traceback.format_exc(), blender_code_formatted)
            print(error)
            print("---------------------------")
            bpy.ops.ed.undo()


    if not error:
        print("Executed successfully!")
    else:
        print(f"Execution failed even after {max_error_retries} attempts.")


def generate_blender_code(prompt):
    global chat_history

    # Collect data about the current blender scene
    blender_scene_data = []
    for obj in bpy.data.objects:
        if obj.type not in ["MESH", "EMPTY", "CAMERA", "LIGHT", "ARMATURE"]:
            continue
        item = {
            "name": obj.name,
            "loc": [round(pos, 2) for pos in obj.location],
            # "type": obj.type,
        }

        # If the object is an armature, add every bone name to the item
        if obj.type == "ARMATURE":
            item["bones"] = [bone.name for bone in obj.data.bones]

        blender_scene_data.append(item)
        # blender_scene_data.append(obj.name)
    scene_data_str = json.dumps(blender_scene_data)

    # print("Using System Prompt:")
    # print(system_prompt)
    chat_history = [{"role": "system",
                   "content": system_prompt}]

    user_prompt = f"Can you please write Blender code for me that accomplishes the following task: " \
                  f"\n" \
                  f"\n{prompt}" \
                  f"\n" \
                  f"\nDo not respond with anything that is not Python code. Do not provide explanations." \
                  f"\nHere are all objects currently in the scene. Whenever you reference objects by name, make sure to only use the object names in the following JSON." \
                  f"\nAlso if you have to use bones, only use the bone names found in the following JSON that belong to the corresponding object:" \
                  f"\n" \
                  f"\n {scene_data_str}"

    # print("Using User Prompt:")
    # print(user_prompt)
    # print()

    # Add the current user message
    chat_history.append(
        {"role": "user",
         "content": user_prompt})

    print("Generating response...")
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=chat_history,
    )

    choices = response['choices']
    if not choices:
        return None
    message = choices[0]["message"]["content"]

    # Add the response to the chat history
    chat_history.append(
        {"role": "assistant",
         "content": message})

    # Crop the response message
    message = clean_response(message)

    return message


def fix_blender_code(error_str):
    user_prompt = f"This code resulted in the following error:" \
                  f"\n" \
                  f"\n{error_str}" \
                  f"\n" \
                  f"Please fix the code. Do not respond with anything that is not Python code. Do not provide explanations." \
                  f"Whenever you reference objects by name, only use above object names."
    # print("Using Error Prompt:")
    # print(user_prompt)

    # Add the current user message
    chat_history.append(
        {"role": "user",
         "content": user_prompt})

    print("Generating fixed response...")
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=chat_history,
    )

    # Extract the response
    choices = response['choices']
    if not choices:
        return None
    message = choices[0]["message"]["content"]

    # Add the response to the chat history
    chat_history.append(
        {"role": "assistant",
         "content": message})

    # Crop the response message
    message = clean_response(message)

    return message


def clean_response(response: str):
    # Find the code block
    try:
        response = re.findall(r'```(.*?)```', response, re.DOTALL)[0]
    except IndexError:
        print("Could not find code block in response, using full response as code")
        return response

    # Remove python string
    if response.lower().startswith("python"):
        response = response[6:]

    # Remove empty lines at the beginning and end
    response = response.strip()

    return response


def clean_error(error: str, code_lines: [str]):
    error = error.strip()
    error_lines = error.split("\n")

    error_result = []
    for i, line in enumerate(error_lines):
        if i == 0 or i == len(error_lines) - 1:
            error_result.append(line)

        if 'File "<string>"' in line:
            error_result.append(line)

            # Find the line number and add the corresponding code line to the error
            line_number = int(re.findall(r'line (\d+)', line)[0])
            error_result.append(f"    {code_lines[line_number - 1]}")

    return "\n".join(error_result)




