
import sys
import bpy
import json
import pathlib
import pkgutil
import logging
import subprocess
import addon_utils

# Add the whole blender app folder to the system path, so all modules in it can be loaded by the script
main_dir = pathlib.Path(__file__).parent
sys.path.append(str(main_dir))

# Create packages directory and add it to the sys path
python_ver_str = "".join([str(ver) for ver in sys.version_info[:2]])
libs_dir = pathlib.Path(__file__).parent / "packages" / f"python{python_ver_str}"
sys.path.append(str(libs_dir))

# Try loading the library allosaurus. If it fails, try installing it
try:
    from allosaurus.app import read_recognizer
    import openai
    import boto3
    import soundfile
except ImportError:
    print("Some libraries not found (allosaurus, openai, boto3, soundfile). Installing...")
    missing = ["allosaurus", "openai", "boto3", "soundfile"]

    # Install allosaurus to the packages dir
    # print("Installing to path:", libs_dir)
    command = [sys.executable, '-m', 'pip', 'install', *missing]
    # command = [sys.executable, '-m', 'pip', 'install', "allosaurus", f"--target={str(libs_dir)}"]
    subprocess.check_call(command, stdout=subprocess.DEVNULL)

    # Find newly added modules
    # print("Newly added modules:")
    # print(sys.path)
    # for mod in pkgutil.iter_modules():
    #     if str(mod.module_finder).startswith("E"):
    #         print(mod.module_finder, "         ", mod.name)

    from allosaurus.app import read_recognizer

from modules import utils
from modules.args_handler import args_handler
from modules.actions import action_manager
from modules import render_output
from modules import gpt
from modules import scene_setup

# Run the script:
# blender --factory-startup -P "E:\Development\Python\metabullweb\commons_file\metabull_blender_app\modules\dialogue_integration\lipsync.py" -- samp2.json --open


def handle_files():
    # Read the json data
    with open(args_handler.json_path, "r") as f:
        data = json.load(f)

    # Check if the json data is valid
    if not data:
        raise Exception(f"Invalid json file: {args_handler.json_path}")

    if "result" in data:
        data = data["result"][0]

    # Setup cloud logger
    if args_handler.cloud_logger:
        utils.logger.enable(args_handler.json_path)

    # Setup scene and import all assets
    utils.logger.log("Setting up scene..")
    actors = scene_setup.setup_scene(data)

    # handle all the actions like animations, lip sync, emotions, etc.
    action_manager.handle_actions(actors, data)

    # Render the result
    render_output.render(data)

    # Test ChatGPT
    if args_handler.use_gpt:
        gpt.generate(data)

    utils.logger.log(f"Done!")
    print("Done!")


def enable_addons():
    # Get the plugins dir
    plugins_dir = utils.assets_dir / "plugins"

    # Set the plugins dir as the scripts path in Blender
    if bpy.app.version >= (3, 6, 0):
        bpy.ops.preferences.script_directory_add("EXEC_DEFAULT", directory=str(plugins_dir))
    else:
        bpy.context.preferences.filepaths.script_directory = str(plugins_dir)

    # Add the new addons folder to the system path, because the plugins won't be found otherwise
    sys.path.append(str(plugins_dir / "addons"))

    # Enable all required addons
    addon_utils.enable("rigify", default_set=True)
    addon_utils.enable("auto_rig_pro-metabull", default_set=True)


def main():
    logging.getLogger().setLevel(logging.INFO)

    args_handler.handle_args()
    enable_addons()
    handle_files()

    if args_handler.open_blender:
        if args_handler.launched_in_background:
            utils.open_in_blender(args_handler.json_path.parent)
    else:
        quit()


if __name__ == '__main__':
    main()
