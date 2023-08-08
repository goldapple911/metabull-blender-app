import bpy
import math

def transform(actors, actions):
    
    # check for all the actions
    for action in actions:
        if action['type'] == "TRANSFORM":
            
            # get the actor
            actor = actors.get(action['actor'])
            
            # set the initial keyframe
            # enter the first keyframe for the current location
            actor.keyframe_insert(data_path='location',frame=action['start_time'])
            actor.keyframe_insert(data_path='scale',frame=action['start_time'])
            actor.keyframe_insert(data_path='rotation_euler',frame=action['start_time'])

            # set the new locations on the given frame
            actor.location = (action["location"]["x"],action["location"]["y"],action["location"]["z"])
            actor.scale = (action["scale"]["x"],action["scale"]["y"],action["scale"]["z"])

            # now for rotation
            rotation_degrees = (action["rotation"]["x"],action["rotation"]["y"],action["rotation"]["z"])
            rotation_radians = tuple(math.radians(deg) for deg in rotation_degrees)
            actor.rotation_euler = rotation_radians

            actor.keyframe_insert(data_path='location',frame=action['end_time'])
            actor.keyframe_insert(data_path='scale',frame=action['end_time'])
            actor.keyframe_insert(data_path='rotation_euler',frame=action['end_time'])