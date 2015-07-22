import os
import sys
import subprocess
import shlex
import json
from flask import Flask, render_template, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask import jsonify
from rq import Queue, get_current_job
from rq.job import Job
from worker import conn

#################
# configuration #
#################

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)

q = Queue(connection=conn)

from models import *

##########
# helper #
##########
def convert(instance,input_file,output_folder,priority,encoding_profile):

    errors = []

    profiles = { 
                "240p": 
                    { 
                        "width":    426, 
                        "vb":       300,
                        "mb":       300,
                        "bs":       600
                    }, 
                "360p": 
                    { 
                        "width":    640, 
                        "vb":       350,
                        "mb":       350,
                        "bs":       700
                    }, 
                "480p": 
                    { 
                        "width":    854, 
                        "vb":       500,
                        "mb":       500,
                        "bs":       1000
                    }, 
                "720p": 
                    { 
                        "width":    1280, 
                        "vb":       1000,
                        "mb":       1000,
                        "bs":       2000
                    }, 
                "1080p": 
                    { 
                        "width":    1920, 
                        "vb":       2000,
                        "mb":       2000,
                        "bs":       4000
                    }
                }

    job = get_current_job()
    print("Current job: {}".format(job.id))

    # Points to 'EdulearnNetUpload' folder
    vidcon_root = app.config['VIDCON_ROOT']

    # E.g /Volumes/EdulearnNETUpload/asknlearn/vidcon/input/small_Sample.mp4
    input_file_absolute_path = os.path.join(vidcon_root + instance + '/' + input_file)

    # E.g /Volumes/EdulearnNETUpload/asknlearn/vidcon/output/
    output_folder_absolute_path = os.path.join(vidcon_root + instance + '/' + output_folder)

    # E.g small_Sample.mp4, derived from the given input filename
    output_filename = os.path.split(input_file)[1]

    # Split a filename into its name and extension:
    # E.g output_file = small_Sample, output_file_extension = .mp4
    output_file, output_file_extension = os.path.splitext(output_filename)
    # Force extension to be ".mp4"
    output_file_extension = ".mp4"

    # Rename the file to include the profile that it was encoded under
    # E.g small_Sample_240p.mp4
    new_output_filename = output_file + "_" + encoding_profile + output_file_extension

    new_output_file = os.path.join(output_folder_absolute_path + "/" + new_output_filename)

    profile = profiles[encoding_profile]

    ffmpeg_cmd = """
        ffmpeg -i '{0}' -codec:v libx264 -profile:v high -preset slow -b:v {1}k -maxrate {2}k 
               -bufsize {3}k -vf scale={4}:trunc(ow/a/2)*2 -threads 0 
               -codec:a mp3 -b:a 64k -y '{5}'""".format(input_file_absolute_path, str(profile['vb']), str(profile['mb']), str(profile['bs']), str(profile['width']), new_output_file)

    std_err = ""
    std_in = ""
    output =""

    try:
        output = subprocess.check_output(shlex.split(ffmpeg_cmd))
        print("Success: {}", output)
    except subprocess.CalledProcessError as ex:

        p = subprocess.Popen(shlex.split(ffmpeg_cmd), bufsize=2048,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)    

        std_in, std_err = map(lambda b: b.decode('utf-8').replace(os.linesep, '\n'),
                        p.communicate((os.linesep).encode('utf-8')))

        print("std_in: {}".format(std_in))
        print("std_err: {}".format(std_err))


        raise GazzaThinksItFailedError("""
                                        \n\nreturn_code: \n{}\n\nffmpeg_cmd: \n{}\n\noutput: \n{}\n\n
                                        """
                                        .format(ex.returncode, ffmpeg_cmd.strip(), std_err.strip()))
    finally:
        print("{}".format(input_file_absolute_path))
        print("{}".format(new_output_file))

##########
# routes #
##########


@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    if request.method == "POST":
        # get url that the person has entered
        filename = request.form['url']
        instance = "asknlearn"
        input_file = "vidcon/input/" + filename 
        output_folder = "vidcon/output"
        priority = "normal"
        encoding_profile = ["360p"]


        for profile in encoding_profile:
            job = q.enqueue_call(func=convert, args=(instance,input_file,output_folder,priority,profile,), result_ttl=5000, timeout=10800)

    return render_template('index.html', results=results)


@app.route('/api/v1/job', methods=['POST'])
def create_job():

    job_ids = []

    instance = request.json['job']['instance']
    input_file = request.json['job']['input_file']
    output_folder = request.json['job']['output_folder']
    priority = request.json['job']['priority']

    for profile in request.json['job']['encoding_profile']:
        job = q.enqueue_call(func=convert, args=(instance,input_file,output_folder,priority,profile,), result_ttl=5000, timeout=10800)
        job_ids.append(job.get_id())

    return json.dumps(job_ids)

class GazzaThinksItFailedError(Exception):
    pass

if __name__ == '__main__':
    app.run()


