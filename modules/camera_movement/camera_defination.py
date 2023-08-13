camera_def = {
    "Dolly Shot": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Fast Pull": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Slow Pull": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Medium Pull": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Long Pull": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Fast Push": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Long": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Medium": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Slow": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Contra-Zoom": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Slow Zoom": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
    "Fast Zoom": {
        "expose_target":True,
        "include_empty":True,
        "use_range":True,
    },
}

camera_details = {
    "90_Degree_Pan": {
        "control": "Camera_Control",
        "lock": "Camera_Empty",
        "animation": "Camera_Action",
        "track": "Camera_Track"
    },
    "180_Degree_Pan": {
        "control": "Camera_Control",
        "animation": "Camera_Action",
        "track": "Camera_Track"
    },
    "360_Pan_and_Tilt": {
        "control": "Camera_Control",
        "animation": ["Camera_Action","Camera_Empty"],
        "track": "Camera_Track",
        "lock": "Camera_Empty"
    },
    "360_Track": {
        "control": "Camera_Control",
        "animation": "Camera_Action",
        "track": "Camera_Track",
        "lock": "Camera_Empty"
    },
    "Adjusting_Focal_Point": {
        "control": "Camera_Control",
        "animation": "Camera_Focus",
        "type": "Focus"
    },
    "Automatic_Gun_Fire": {
        "control": "Camera_Control",
        "animation": "Camera_Action"
    },
    "Backwards_Running": {
        "control": "Camera_Control",
        "animation": ["Camera_Empty","Camera_Action"],
        "lock": "Camera_Empty"
    },
    "Base_Jump_Fpv": {
        "control": "Camera_Control",
        "animation": "Camera_Action"
    },
    "Birds_Eye_Twist": {
        "control": "Camera_Control",
        "animation": ["Camera_Empty","Camera_Action"],
        "lock": "Camera_Empty"
    },
    "Bleeding_Out": {
        "control": "Camera_Control",
        "animation": "Camera_Action"
    },
    "Cable_Cam": {
        "control": "Camera_Control",
        "animation": "Camera_Animation"
    },
    "Contra_Zoom": {
        "control": "Camera_Control",
        "animation": "Camera_Action",
        "lock": "Camera_Empty"
    },
    "Contra_Zoom_2":{
        "control": "Camera_Control",
        "animation": "Camera_Action",
        "lock": "Camera_Empty"
    },
    "Crane_Shot_Side":{
        "control": "Camera_Control",
        "animation": "Camera_Action",
        "lock": "Camera_Empty"
    },
    "Crane_Shot_Sweep":{
        "control": "Camera_Control",
        "animation": ["Camera_Action","Camera_Empty"],
        "lock": "Camera_Empty"
    },
    "Curved_Missle_Strike":{
        "control": "Camera_Control",
        "animation": "Camera_Action"
    },
    "Idle": {
        "control": "Camera_Control",
        "animation": "Camera_Action"
    }
}