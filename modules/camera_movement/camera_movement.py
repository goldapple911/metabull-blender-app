import pathlib
import sys
import bpy
import os
from .camera_defination import camera_def, camera_details
from .. import utils


def append_camera_collection(context, path, cam_name, camera_focus):
        link = False
        filepath = path

        #import saved scene collection
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
            data_to.collections = [c for c in data_from.collections if c  == 'Camera']
        
        for coll in data_to.collections:
            if coll is not None:
                name = f'CAMERA - {cam_name}'
                coll.name = name
                camera = next(obj for obj in coll.objects if obj.type == 'CAMERA')
                camera.name = name #object name
                camera.data.name = name #camera datablock name
                context.scene.collection.children.link(coll)
                context.scene.camera = camera
                camera.data.lens = camera_focus
                #camera.data.is_cinepack = True
                if cam_name in camera_def:
                    camera.data.cinepack_expose_targe = camera_def[cam_name]['expose_target']
                    camera.data.cinepack_use_range = camera_def[cam_name]['use_range']
                    
        return camera, coll.name
    

def set_target(target, collection_name, cameraname, filename, scale = None):
    
    # set the camera angle to the defined target
    obj_check = False
    if isinstance(target, str):
        obj_check = True
        target = bpy.context.scene.objects[target]
    # get the camera collection
    coll = bpy.data.collections.get(collection_name)
    
    for obj in coll.objects:
        if obj.type != 'CAMERA':
            obj.name = f'{obj.name} - {filename}'
        
        if (obj.type == 'CURVE') and (scale is not None):
            obj.scale = [scale,scale,scale]
            
    # Get the control object for the camera
    camera_info = camera_details[cameraname]
    
    control_name = f'{camera_info["control"]} - {filename}'
    control_obj = bpy.data.objects[control_name] # gets the object from the scene
    
    # Get the value at which the objects needs to move
    if obj_check:
        position = target.location.copy()
    else:
        position = target
        
    # Now check if there is a lock for camera available or not
    if "lock" in camera_info:
        # get the lock infrmation
        lock_name = f'{camera_info["lock"]} - {filename}'
        lock_obj = bpy.data.objects[lock_name]
        
        # get the position for the target
        position_dif_x = control_obj.location[0] - lock_obj.location[0]
        position_dif_y = control_obj.location[1] - lock_obj.location[1]
        position_dif_z = control_obj.location[2] - lock_obj.location[2]
        
        # Add the correction terms
        position[0] += position_dif_x
        position[1] += position_dif_y
        position[2] += position_dif_z
    
    # update the location
    control_obj.location = position
    

def adjust_animation(camera, new_start_frame, new_end_frame):

    # Get the camera animation data
    anim_data = camera.animation_data
    if anim_data is None or anim_data.action is None:
        return  # No animation data found

    # Get the action containing the keyframe animation
    action = anim_data.action

    # Calculate the scale factor based on the frame ranges
    current_start_frame, current_end_frame = action.frame_range
    current_frame_range = current_end_frame - current_start_frame
    new_frame_range = new_end_frame - new_start_frame

    if current_frame_range == 0:
        return  # Avoid division by zero

    scale_factor = new_frame_range / current_frame_range

    # Shift and scale the keyframes
    for fcurve in action.fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframe.co.x = new_start_frame + (keyframe.co.x - current_start_frame) * scale_factor

    # Update the frame range
    action.frame_range = (new_start_frame, new_end_frame)

    # Update the animation data
    anim_data.action = action
                

def bind_camera_to_frame(camera,frame):
    
    # create the marker for the current camera
    marker = bpy.context.scene.timeline_markers.new(camera.name, frame=frame)
    marker.camera = camera

                
def set_camera_movement(actions: list[dict]):
    
    camera_number = 0 # set the current camera number
    
    for action in actions:
        if action["type"] == "CAMERA_MOVEMENT":
            camera_number += 1
            # camera movement is required in this scene, hence, will remove the initial camera
            if camera_number == 1:
                
                # Create the camera collection
                camera_all_collection = bpy.data.collections.new("Cameras")
                bpy.context.scene.collection.children.link(camera_all_collection)
                
                for obj in bpy.context.scene.objects:
                    if obj.type == 'CAMERA':
                        bpy.data.objects.remove(obj, do_unlink=True)
            
            # Get the target actor
            if "actor" in action:
                target = action["actor"]
            elif "target_location" in action:
                target = utils.get_3d_vec(action["target_location"])
            else:
                target = (0,0,0)
                
            file = str(utils.get_resource(action["file"]))
            
            if "focal_length" in action:
                focal_length = action["focal_length"]
            else:
                focal_length = 50
            
            
            if "name" in action:
                cameraname = action["name"]
                cameraname = filename.replace(" ","_")
            else:
                cameraname = "Idle"
            filename = f'{cameraname} - {camera_number}'
             
             
            if "scale" in action:
                scale = action["scale"]
            else:
                scale = None
                
            start_time = action["start_time"]
            end_time = action["end_time"]
            
            # append the camera to the collection
            camera, collection_name = append_camera_collection(bpy.context, file, filename, focal_length)
            camera_all_collection.children.link(bpy.data.collections.get(collection_name))
            bpy.context.scene.collection.children.unlink(bpy.data.collections.get(collection_name))
            
            # check location
            if "location" in action:
                camera.location = utils.get_3d_vec(action["location"])
            
            # set to the target
            set_target(target, collection_name, cameraname, filename, scale)
            # scale the animation
            adjust_animation(camera, start_time, end_time)
            
            # bind the camera
            bind_camera_to_frame(camera, start_time)