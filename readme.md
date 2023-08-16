Download Blender from link below:
https://www.blender.org/download/

MacOS: Add path to path file:
export PATH=/Applications/Blender.app/Contents/MacOS/blender:$PATH

Run blender in headless mode (example):

`blender -b -P main.py -- beta_scene2.json --open --render`

### Documentation:
`blender -b -P main.py -- <json file> [arguments]`

All arguments:
- `json file`: file path to json, this can either be an absolute path or a relative one (relative to the assets folder)
- `--render`: fully render the scene as a video
- `--render-image`: render the first frame of the scene as an image (useful for testing)
- `--save-blend`: save the generated .blend file to the output folder
- `--use-mp4`: use the MP4 format for the rendered video (default is EXR, only effective if rendering a video)
- `--upload`: upload the full output folder to the S3 bucket "metabull-blender-output" and delete the local files after upload
- `--trigger-deadline`: upload the generated .blend file to the S3 bucket "metabull-deadline-blend-files"
                        to trigger the deadline job and delete the local files after upload
- `--keep-files`: keep the generated files after the upload instead of deleting them
- `--cloud-logger`: log the progress in the AWS cloud, only use on the AWS server
- `--check-asset-updates`: check for asset updates on S3 and re-download if a newer version is available
- `--open`: view the generated .blend file in Blender after the process (useful for testing, only use this on a local machine installed)

### Info:
- Blender version: 3.5+
- Store all assets in the 'assets' folder
- All file paths in the json file have to be either absolute or relative to the 'assets' folder
  - Example: `\audio\scene1.wav` or `E:\metabullweb\commons_file\metabull_blender_app\assets\audio\scene1.wav`


