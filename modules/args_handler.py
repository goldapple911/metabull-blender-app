
import os
import pathlib
import sys
from . import utils


class ArgsHandler:
    _arg_help = ["--help", "-h"]
    _index_json_path = 0
    _arg_open_blender = "--open"
    _arg_render = "--render"
    _arg_render_image = "--render-image"
    _arg_save_blend = "--save-blend"
    _arg_use_gpt = "--gpt"
    _arg_use_mp4 = "--use-mp4"
    _arg_upload = "--upload"
    _arg_trigger_deadline = "--trigger-deadline"
    _arg_keep_files = "--keep-files"
    _arg_cloud_logger = "--cloud-logger"
    _arg_check_asset_updates = "--check-asset-updates"

    def __init__(self):
        self.args = []
        self.json_path: pathlib.Path | None = None
        self.launched_in_background = False
        self.open_blender = False
        self.render = False
        self.render_image = False
        self.save_blend = False
        self.use_gpt = False
        self.use_mp4 = False
        self.upload = False
        self.trigger_deadline = False
        self.keep_files = False
        self.cloud_logger = False
        self.check_asset_updates = False

    def handle_args(self):
        print(f"INFO: Launched using arguments: {' '.join(sys.argv)}")

        # This argument needs to be there in order to pass arguments to this script instead of to Blender
        if "--" not in sys.argv:
            print("\nERROR: Invalid command. Use '--' to add parameters for this script.\n")
            return False

        # Get the arguments for this script
        index_start = sys.argv.index("--")
        self.args = sys.argv[index_start + 1:]

        # Check background state
        if "-b" in sys.argv[:index_start] or "--background" in sys.argv[:index_start]:
            self.launched_in_background = True

        # Handle all arguments
        self.open_blender = self._check_arg_bool(self._arg_open_blender)
        self.render = self._check_arg_bool(self._arg_render)
        self.render_image = self._check_arg_bool(self._arg_render_image)
        self.save_blend = self._check_arg_bool(self._arg_save_blend)
        self.use_gpt = self._check_arg_bool(self._arg_use_gpt)
        self.use_mp4 = self._check_arg_bool(self._arg_use_mp4)
        self.upload = self._check_arg_bool(self._arg_upload)
        self.trigger_deadline = self._check_arg_bool(self._arg_trigger_deadline)
        self.keep_files = self._check_arg_bool(self._arg_keep_files)
        self.cloud_logger = self._check_arg_bool(self._arg_cloud_logger)
        self.check_asset_updates = self._check_arg_bool(self._arg_check_asset_updates)

        self.json_path = self._check_arg_path_index(self._index_json_path)
        if self.json_path is None:
            return False

        # Check for help argument
        if self._check_arg_bool(self._arg_help):
            self._print_help()
            return False

        # Check for args with a typo after all correct args have been removed
        for arg in self.args:
            if arg.startswith("-"):
                print(f"\nERROR: Invalid argument '{arg}'. Please check the info.txt for valid arguments.\n")
                return False

        if self.args:
            print("WARNING: Unused arguments remaining:", self.args)

        return True

    def _check_arg_bool(self, args):
        if isinstance(args, str):
            args = [args]

        found = False
        for arg in args:
            if arg in self.args:
                self.args.remove(arg)
                found = True
        return found

    def _check_arg_int(self, arg, default_value):
        if arg not in self.args:
            return default_value

        index = self.args.index(arg)

        try:
            value = self.args[index + 1]
        except IndexError:
            print(f"\nERROR: Value for '{arg}' not found. Use '{arg} <value>' to set the value.\n")
            return None

        try:
            value = int(round(float(value)))
        except ValueError:
            print(f"\nERROR: The value in '{arg} {value}' is not an integer. Use '{arg} <value>' to set the value.\n")
            return None

        # Remove argument and its value in reversed order to avoid index error
        self.args.pop(index + 1)
        self.args.pop(index)

        return value

    def _check_arg_float(self, arg, default_value):
        if arg not in self.args:
            return default_value

        index = self.args.index(arg)

        try:
            value = self.args[index + 1]
        except IndexError:
            print(f"\nERROR: Value for '{arg}' not found. Use '{arg} <value>' to set the value.\n")
            return None

        try:
            value = float(value)
        except ValueError:
            print(f"\nERROR: The value in '{arg} {value}' is not a valid number. Use '{arg} <value>' to set the value.\n")
            return None

        # Remove argument and its value in reversed order to avoid index error
        self.args.pop(index + 1)
        self.args.pop(index)

        return value

    def _check_arg_path(self, arg, ignore_error=False):
        if arg not in self.args:
            return ""

        index = self.args.index(arg)

        try:
            value = self.args[index + 1]
        except IndexError:
            self.args.pop(index)
            if not ignore_error:
                print(f"\nERROR: Path for '{arg}' not found. Use '{arg} <path>' to set the path.\n")
            return None

        if not os.path.isfile(value):
            self.args.pop(index)
            if not ignore_error:
                print(f"\nERROR: The path in '{arg} {value}' is not a valid file.\n")
            return None

        # Remove argument and its value in reversed order to avoid index error
        self.args.pop(index + 1)
        self.args.pop(index)

        return value

    def _check_arg_path_index(self, index) -> pathlib.Path:
        try:
            value = self.args[index]
        except IndexError as e:
            raise Exception(f"ERROR: Path to JSON at position {index} not found.") from e

        path = utils.get_resource(value)

        # Remove argument
        self.args.pop(index)

        return path

    def _print_help(self):
        # Print all available commands
        print("\nAvailable commands:")
        for key, val in ArgsHandler.__dict__.items():
            if key.startswith("_arg_"):
                commands = val
                if not isinstance(commands, str):
                    commands = ", ".join(commands)
                print(f"  {key.replace('_arg_', '').replace('_', ' ').capitalize() + ':':<20} {commands}")
        print("")


args_handler: ArgsHandler = ArgsHandler()
