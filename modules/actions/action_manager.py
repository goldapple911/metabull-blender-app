
from . import retargeting, lipsync, emotions, attach, transform, blinking
from ..camera_movement import camera_movement
from .. import utils


def handle_actions(actors: dict, data: dict):
    # Sort the actions by their start time
    actions: list[dict] = data["actions"]
    actions.sort(key=lambda x: x.get("start_time"))

    # Attach objects to the armature
    attach.attach(actors, data)
    
    # Add animations to actors
    utils.logger.log("Retargeting..")
    retargeting.retarget(actors, actions, data)

    # Add lip sync to the actors
    utils.logger.log("Adding lip sync and emotions..")
    lipsync.add_lip_sync(actors, actions)

    # Add emotions
    emotions.add_emotions(actors, actions)

    # Add random blinking
    blinking.add_blinking(actors)

    # Add camera animations
    camera_movement.set_camera_movement(actions)

    # Add object transform animations
    transform.transform(actors, actions)
