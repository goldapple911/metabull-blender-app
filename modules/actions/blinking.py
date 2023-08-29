import bpy
import random
from .. import utils

eye_keys = {
            "Eye_Squint_L": 1.5,
            "Eye_Squint_R": 1.5,
            "Eye_Wide_L": -1.5,
            "Eye_Wide_R": -1.5
            }

def add_blinking(actors: dict):
    
    # get the start frame and the end frame
    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end
    
    # run for all the actors
    for actor,obj in actors.items():
        
        # generate the frames where blinking would be applied
        frames = generate_frames(start_frame,end_frame)
        for mesh in obj.children_recursive:
            if mesh.type != "MESH" or not mesh.data.shape_keys:
                continue
            if mesh.name not in bpy.context.view_layer.objects:
                continue
            
            # for each frame, generate shape_keys and blinking
            generate_blinks(mesh, frames)
            

def generate_frames(start_frame, end_frame):
    difference = 8
    # calculate the number of blinking that would be needed
    max_number = round((end_frame - start_frame)/24)
    count = random.randint(1,max_number)
    
    if count <= 0:
        return []
    
    numbers = []
    
    while len(numbers) < count:
        new_number = random.randint(start_frame, end_frame)
        is_unique = all(abs(new_number - num) >= difference for num in numbers)
        
        if is_unique:
            # check for end frame as well
            if abs(new_number-end_frame) < difference:
                continue

            numbers.append(new_number)
            
    return numbers


def generate_blinks(mesh, frames):
    # loop for all the frames
    for frame in frames:
        shape_keys = mesh.data.shape_keys.key_blocks
        
        for shape_key in shape_keys:
            
            if shape_key.name in eye_keys:
                shape_key.value = 0
                shape_key.keyframe_insert(data_path="value",frame=frame)
                
                shape_key.value = eye_keys[shape_key.name]
                shape_key.keyframe_insert(data_path="value",frame=frame+3)
                shape_key.keyframe_insert(data_path="value",frame=frame+4)
                
                shape_key.value = 0
                shape_key.keyframe_insert(data_path="value",frame=frame+7)