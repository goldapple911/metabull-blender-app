
from .. import utils


def transform(actors, actions):
    
    # check for all the actions
    for action in actions:
        if action['type'] != "TRANSFORM":
            continue
            
        # Get the action data
        actor = utils.find_actor(actors, action['actor'])
        start_time = action['start_time']
        end_time = action['end_time']

        # set the initial keyframe
        # enter the starting keyframe for the current transforms
        actor.keyframe_insert(data_path='location', frame=start_time)
        actor.keyframe_insert(data_path='scale', frame=start_time)
        actor.keyframe_insert(data_path='rotation_euler', frame=start_time)

        # set the new transforms on the given frame
        actor.location = utils.get_3d_vec(action.get("location"))
        actor.scale = utils.get_3d_vec(action.get("scale"), default=(1, 1, 1))
        actor.rotation_euler = utils.get_3d_vec(action.get("rotation"), use_rad=True)

        # enter the ending keyframe for the current transforms
        actor.keyframe_insert(data_path='location', frame=end_time)
        actor.keyframe_insert(data_path='scale', frame=end_time)
        actor.keyframe_insert(data_path='rotation_euler', frame=end_time)

