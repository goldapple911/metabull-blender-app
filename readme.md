Download Blender from link below:
https://www.blender.org/download/

MacOS: Add path to path file:
export PATH=/Applications/Blender.app/Contents/MacOS/blender:$PATH

Run blender in headless mode (example):

`blender -b -P main.py -- scene1-01.json --open --render`

### Documentation:
`blender -b -P main.py -- <json file> [arguments]`

All arguments:
- `json file`: file path to json, this can either be an absolute path or a relative one (relative to the assets folder)
- `--render`: fully render the scene as a video
- `--render-image`: render the first frame of the scene as an image (useful for testing)
- `--upload_render`: save the rendered result to the output folder and it to the S3 bucket and delete the files after upload
- `--upload-blend`: save the generated blend file to the output folder and it to the S3 bucket and delete the files after upload
- `--use-mp4`: use the MP4 format for the rendered video (default is EXR, only effective if rendering a video)
- `--keep-files`: keep the generated files after the upload instead of deleting them
- `--open`: view the generated .blend file in Blender after the process (useful for testing, only use this on a local machine installed)

### Info:
- Blender version: 3.5+
- Store all assets in the 'assets' folder
- All file paths in the json file have to be either absolute or relative to the 'assets' folder
  - Example: `\audio\scene1.wav` or `E:\metabullweb\commons_file\metabull_blender_app\assets\audio\scene1.wav`


