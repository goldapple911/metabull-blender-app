import os.path
import pathlib

import bpy
import shutil
from . import utils
from .args_handler import args_handler


def render(data: dict):
    # Get render settings
    render_settings = data["render_sequence"]
    # render_name = render_settings["output_name"]
    render_quality = render_settings["quality"]
    # render_frame_rate = render_settings["frame_rate"]
    render_res_x = render_settings["resolution"]["x"]
    render_res_y = render_settings["resolution"]["y"]
    render_max_frames = render_settings["max_frames"]

    # Limit max frames
    if bpy.context.scene.frame_end > render_max_frames:
        bpy.context.scene.frame_end = render_max_frames

    # Set render settings
    render = bpy.context.scene.render
    render.resolution_percentage = render_quality
    render.resolution_x = render_res_x
    render.resolution_y = render_res_y
    render.image_settings.file_format = 'FFMPEG'
    render.ffmpeg.format = 'MPEG4'
    render.ffmpeg.constant_rate_factor = 'HIGH'
    render.ffmpeg.audio_codec = 'AAC'

    # Set output path
    render_name = args_handler.json_path.stem
    output_dir = utils.assets_dir.parent / "output" / render_name
    output_file_video = output_dir / f"{render_name}.mp4"
    output_file_image = output_dir / f"{render_name}.png"
    output_file_audio = output_dir / f"{render_name}.wav"
    output_file_blend = output_dir / f"{render_name}.blend"
    output_folder_jpg_sequence = output_dir / "jpg"
    output_folder_exr_sequence = output_dir / "exr" / f"Image"

    output_file = None

    # Set EXR video output settings
    if not args_handler.use_mp4:
        render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
        render.image_settings.use_preview = True
        output_file_video = output_folder_exr_sequence

        # Delete the output folder
        shutil.rmtree(output_file_video.parent, ignore_errors=True)
    else:
        # Delete the output folder
        shutil.rmtree(output_folder_jpg_sequence, ignore_errors=True)

        # Create compositor nodes
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
        output.base_path = str(output_folder_jpg_sequence)
        output.format.file_format = 'JPEG'
        output.format.quality = 100

        # Link nodes
        links.new(render_layers.outputs[0], composite.inputs[0])
        links.new(render_layers.outputs[0], output.inputs[0])

    # Rendering of the scene
    if args_handler.render:
        # Render the full animation
        output_file = output_file_video
        render.filepath = str(output_file)

        print(f"Rendering {output_file} ...")
        bpy.ops.render.render(animation=True)

        # Export the audio alone
        # Create directory if it doesn't exist
        output_file_audio.parent.mkdir(parents=True, exist_ok=True)

        # Export the audio
        print(f"Rendering audio {output_file_audio} ...")
        bpy.ops.sound.mixdown(
            "EXEC_DEFAULT",
            filepath=str(output_file_audio),
            container='WAV',
            codec='PCM'
        )

    elif args_handler.render_image:
        # Render only a single image
        output_file = output_file_image
        render.filepath = str(output_file)
        render.image_settings.file_format = 'PNG'

        print(f"Rendering {output_file} ...")
        bpy.ops.render.render(write_still=True)
    else:
        print(f"Skipped rendering..")

    if args_handler.save_blend:
        # Create the output dir if it doesn't exist, Blender won't create it automatically when saving blend files
        output_dir.mkdir(parents=True, exist_ok=True)

        # Purge unused assets, pack all assets and save the blend file
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        # Unpack all assets
        bpy.ops.file.unpack_all(method='WRITE_LOCAL')

        # Check all images if their paths exist
        for img in bpy.data.images:
            print("Packing", img.filepath)
            image_file = utils.assets_dir.parent / img.filepath[2:]
            if not image_file.exists():
                print(f"Image '{img.filepath}' not found, removing..")
                bpy.data.images.remove(img)
                continue

            # Set the new filepath
            img.filepath_raw = str(image_file)
            try:
                img.pack()
            except RuntimeError:
                print(f"Image '{image_file}' failed packing, removing..")
                bpy.data.images.remove(img)
        bpy.ops.file.pack_all()

        # Delete the textures folder
        textures_dir = utils.assets_dir.parent / "textures"
        shutil.rmtree(textures_dir, ignore_errors=True)

        bpy.ops.wm.save_as_mainfile(filepath=str(output_file_blend))
        print(f"Saved blend file to: {output_file_blend}")

    # If the output folder exists, add the json file to it
    if output_dir.exists():
        shutil.copy(args_handler.json_path, output_dir)

    if args_handler.upload:
        # Create a small file to indicate when the render is complete, it gets uploaded last
        (output_dir / ".render_complete.txt").touch()

        utils.upload_to_s3(output_dir, output_dir.parent)

    if args_handler.trigger_deadline:
        if not output_file_blend.exists():
            print(f"ERROR: No blend file for upload to Deadline found. Use '--save-blend' to save the blend file.")
            return

        utils.upload_to_s3(output_file_blend, output_dir, bucket_name="metabull-deadline-blend-files")

    # After the upload, delete the output folder
    if args_handler.upload or args_handler.trigger_deadline:
        if not args_handler.keep_files:
            shutil.rmtree(output_dir, ignore_errors=True)

    




