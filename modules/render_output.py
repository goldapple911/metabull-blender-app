import os.path
import pathlib

import bpy
import shutil
from . import utils
from .args_handler import args_handler


class Renderer:
    def __init__(self, data: dict):
        # Get render settings
        render_settings = data["render_sequence"]
        self.render_quality = render_settings["quality"]
        self.render_res_x = render_settings["resolution"]["x"]
        self.render_res_y = render_settings["resolution"]["y"]
        self.render_max_frames = render_settings["max_frames"]

        # Define output paths
        render_name = args_handler.json_path.stem
        self.output_dir = utils.assets_dir.parent / "output" / render_name
        self.output_file_video = self.output_dir / f"{render_name}.mp4"
        self.output_file_image = self.output_dir / f"{render_name}.png"
        self.output_file_audio = self.output_dir / f"{render_name}.wav"
        self.output_file_blend = self.output_dir / f"{render_name}.blend"
        self.output_folder_jpg_sequence = self.output_dir / "jpg"
        self.output_folder_exr_sequence = self.output_dir / "exr" / f"Image"

        self._render()

    def _setup_settings(self):
        # Limit max frames
        if bpy.context.scene.frame_end > self.render_max_frames:
            print(f"Force limiting frames to {self.render_max_frames}..")
            bpy.context.scene.frame_end = self.render_max_frames

        # Set render settings
        render = bpy.context.scene.render
        render.resolution_percentage = self.render_quality
        render.resolution_x = self.render_res_x
        render.resolution_y = self.render_res_y
        render.image_settings.file_format = 'FFMPEG'
        render.ffmpeg.format = 'MPEG4'
        render.ffmpeg.constant_rate_factor = 'HIGH'
        render.ffmpeg.audio_codec = 'AAC'

        if not args_handler.use_mp4:
            # Set EXR video output settings
            render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
            render.image_settings.use_preview = True
            output_file_video = self.output_folder_exr_sequence

            # Delete the output folder
            shutil.rmtree(output_file_video.parent, ignore_errors=True)
        else:
            # Set MP4 video output settings
            # Delete the jpg folder in the output folder
            shutil.rmtree(self.output_folder_jpg_sequence, ignore_errors=True)

            # Create compositor nodes for exporting MP4 and a JPEG sequence simultaneously
            bpy.context.scene.use_nodes = True
            tree = bpy.context.scene.node_tree
            links = tree.links

            # Clear default nodes
            for node in tree.nodes:
                tree.nodes.remove(node)

            # Create render layer node
            render_layers = tree.nodes.new('CompositorNodeRLayers')
            render_layers.location = 0, 0

            # Create composite node
            composite = tree.nodes.new('CompositorNodeComposite')
            composite.location = 400, 0

            # Create output node
            output = tree.nodes.new('CompositorNodeOutputFile')
            output.location = 400, -200
            output.base_path = str(self.output_folder_jpg_sequence)
            output.format.file_format = 'JPEG'
            output.format.quality = 100

            # Link nodes
            links.new(render_layers.outputs[0], composite.inputs[0])
            links.new(render_layers.outputs[0], output.inputs[0])

    def _render_video(self):
        # Render the full animation
        output_file = self.output_file_video
        bpy.context.scene.render.filepath = str(output_file)

        utils.logger.log(f"Rendering animation..")
        print(f"Rendering {output_file} ...")
        bpy.ops.render.render(animation=True)

        # Export the audio alone
        # Create directory if it doesn't exist
        self.output_file_audio.parent.mkdir(parents=True, exist_ok=True)

        # Export the audio
        print(f"Rendering audio {self.output_file_audio} ...")
        bpy.ops.sound.mixdown(
            "EXEC_DEFAULT",
            filepath=str(self.output_file_audio),
            container='WAV',
            codec='PCM'
        )

    def _render_image(self):
        utils.logger.log(f"Rendering first image..")
        # Render only a single image
        output_file = self.output_file_image
        bpy.context.scene.render.filepath = str(output_file)
        bpy.context.scene.render.image_settings.file_format = 'PNG'

        print(f"Rendering {output_file} ...")
        bpy.ops.render.render(write_still=True)

    def _save_blend(self):
        utils.logger.log(f"Saving blend file..")
        # Create the output dir if it doesn't exist, Blender won't create it automatically when saving blend files
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Purge unused assets
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        # Unpack all assets
        print("Unpacking textures..")
        bpy.ops.file.unpack_all(method='WRITE_LOCAL')

        # Update all image paths to the unpacked textures
        for img in bpy.data.images:
            # Get the new unpacked texture path
            img_file = img.filepath[2:]
            image_path = utils.assets_dir.parent / img_file

            # Check if the image exists
            # If the image is a UDIM tile, check if the first tile exists
            image_tile_path = str(image_path).replace("<UDIM>", "1001")
            if not os.path.exists(image_tile_path):
                print(f"Image '{img_file}' not found, removing..")
                bpy.data.images.remove(img)
                continue

            # Set the new filepath
            img.filepath = str(image_path)

        # Pack all textures and save the blend file
        print("Packing textures..")
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(self.output_file_blend))
        print(f"Saved blend file to: {self.output_file_blend}")

        # Delete the textures folder
        textures_dir = utils.assets_dir.parent / "textures"
        shutil.rmtree(textures_dir, ignore_errors=True)

    def _upload_folder(self):
        utils.logger.log(f"Uploading output..")
        # Create a small file to indicate when the render is complete, it gets uploaded last
        (self.output_dir / ".render_complete.txt").touch()

        utils.upload_to_s3(self.output_dir, self.output_dir.parent)

    def _trigger_deadline(self):
        utils.logger.log(f"Uploading blend file to deadline..")
        if not self.output_file_blend.exists():
            print(f"ERROR: No blend file for upload to Deadline found. Use '--save-blend' to save the blend file.")
            return

        # Export the audio
        print(f"Rendering audio {self.output_file_audio} ...")
        bpy.ops.sound.mixdown(
            "EXEC_DEFAULT",
            filepath=str(self.output_file_audio),
            container='WAV',
            codec='PCM'
        )

        utils.upload_to_s3(self.output_file_audio, self.output_dir, bucket_name="metabull-deadline-blend-files")
        utils.upload_to_s3(self.output_file_blend, self.output_dir, bucket_name="metabull-deadline-blend-files")

    def _render(self):
        self._setup_settings()

        # Rendering of the scene
        if args_handler.render:
            self._render_video()
        elif args_handler.render_image:
            self._render_image()
        else:
            print(f"Skipped rendering..")

        if args_handler.save_blend:
            self._save_blend()

        # If the output folder exists, add the json file to it
        if self.output_dir.exists():
            shutil.copy(args_handler.json_path, self.output_dir)

        # Upload the whole output folder
        if args_handler.upload:
            self._upload_folder()

        # Upload only the blend and audio file to the deadline bucket
        if args_handler.trigger_deadline:
            self._trigger_deadline()

        # After the upload, delete the output folder
        if args_handler.upload or args_handler.trigger_deadline:
            if not args_handler.keep_files:
                shutil.rmtree(self.output_dir, ignore_errors=True)

