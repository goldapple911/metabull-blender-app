import os
import json
import boto3
import argparse
import subprocess
from datetime import datetime as dt


class TriggerBlenderJob:
    def __init__(self, filename) -> None:
        # Logger details
        self.log_group_name = 'JSON-uploader-logs'
        self.log_stream_name = filename.split('.json')[0]
        self.logger_client = boto3.client('logs', region_name='us-east-2')
        self.logger_client.create_log_stream(logGroupName=self.log_group_name, logStreamName=self.log_stream_name)

        # S3 Bucket details
        self.bucket_name = 'metabull-json-gen-input'
        self.filename = filename

        # Downloaded file Configs
        self.directory_path = r'C:\apps\OutputJson'  # JSON Output path
        self.path_to_output_file = os.path.join(self.directory_path, filename)  # Downloaded JSON can be found here
        self.file_list = []

        # Blender Configs, Make Tweaks here to change app location and stuff
        self.blender_app = r'"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"'
        self.metabull_blender_app = r'C:\apps\metabull_blender_app\main.py'
        self.temppath_to_outputfile = r'C:\apps\metabull_blender_app\assets\scene1-01.json'

    def upload_logs(self, log_message):
        '''
        This Module Writes logs to CloudWatch and prints in console as well
        '''
        print(log_message)

        timestamp = int(dt.utcnow().timestamp() * 1000)
        log_event = {
            'timestamp': timestamp,
            'message': log_message
        }

        self.logger_client.put_log_events(
            logGroupName=self.log_group_name,
            logStreamName=self.log_stream_name,
            logEvents=[log_event]
        )

    def download_file_on_remote(self):
        '''
        This module helps us download the S3 object to filepath specified
        '''
        try:
            s3 = boto3.client('s3')
            self.upload_logs('[INFO] S3 Client initialized successfully')
            self.upload_logs(f'[INFO] Downloading from S3 bucket name: {self.bucket_name}\nS3 Object Key: {self.filename}')

            s3.download_file(self.bucket_name, self.filename, self.path_to_output_file)
            self.upload_logs(f'[INFO] JSON file successfully downloaded into remote machine: {self.path_to_output_file}')

            return True

        except Exception as e:
            print(f"Error downloading file: {e}")
            self.upload_logs(f'[ERROR] Error in downloading S3 Object, Please check the error msg below {e}')
            return False

    def split_json_into_scene(self):
        try:
            with open(os.path.join(self.path_to_output_file), 'r') as f:
                data = json.load(f)
            file_index = 1
            output_dir = self.path_to_output_file
            scene_count = len(data['result'])
            self.upload_logs(f'There are {scene_count}')
            for scene_json in data['result']:
                scene_file_name = os.path.basename(self.filename.split('.json')[0] + '-scene-' + str(file_index) + '.json')
                self.upload_logs(f'Scene generated, its present in: {scene_file_name}')
                file_index = file_index + 1

                scene_json_path = os.path.join(os.path.dirname(output_dir), scene_file_name)
                self.file_list.append(scene_json_path)
                with open(scene_json_path, 'w') as outputJson:
                    outputJson.write(json.dumps(scene_json))
        except Exception as e:
            self.upload_logs(f'Exception has occured : \n{e}')
            self.upload_logs(f'Split JSON has failed, please check')

    def trigger_blender(self):
        self.upload_logs(f'[CAUTION] Blender Process started rendering, It will take an 30 mins to 45 mins to complete')

        '''
        command = f'{self.blender_app} -b -P {self.metabull_blender_app} -- {self.temppath_to_outputfile} --render --upload-render'
        self.split_json_into_scene()
        self.upload_logs(f'The list of files are : {self.file_list}')
        blender_output = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.upload_logs(f'[INFO] Blender Output: {blender_output.stdout}')
        self.upload_logs(f'[INFO] Blender Error: {blender_output.stderr}')  
        
        
        
        '''

        self.split_json_into_scene()
        self.upload_logs(f'The list of files are : {self.file_list}')

        # Uncomment this part of code once rendering is successfull
        self.upload_logs(f'[CAUTION] Blender Process started rendering, It will take an 30 mins to 45 mins to complete')
        for file_into_scenes in self.file_list:
            # Once the JSON rendering is fixed please update the command by uncommenting the below line
            command = f'{self.blender_app} -b -P {self.metabull_blender_app} -- {file_into_scenes} --render-image --upload-render --keep-files'
            command = f'{self.blender_app} -b -P {self.metabull_blender_app} -- {file_into_scenes} --render --use-mp4 --upload-render --keep-files'
            self.upload_logs(f'[INFO] Running Command : {command}, on remote machine')
            self.upload_logs(f'[CAUTION] The next set of log lines will be printed once Blender finishes processing')

            blender_output = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.upload_logs(f'[INFO] Blender Output: {blender_output.stdout}')
            self.upload_logs(f'[INFO] Blender Error: {blender_output.stderr}')

        # -------------Setting Up args parse -----------------#


parser = argparse.ArgumentParser()
# Add an argument
parser.add_argument('--filename', type=str, required=True)
# Parse the argument
args = parser.parse_args()

myapp = TriggerBlenderJob(args.filename)
is_download_successfull = myapp.download_file_on_remote()
if is_download_successfull:
    myapp.trigger_blender()
else:
    myapp.upload_logs('Did not trigger Blender as Download was not successfull')
