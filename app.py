import os
import sys
import subprocess
import shlex
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


def convert(url):


    errors = []
    job = get_current_job()
    print("Current job: {}".format(job.id))
    print("Output filename: {}".format(os.path.splitext(url)[0]))

    vidcon_root = app.config['VIDCON_ROOT']

    input_dir = 'input/'
    output_dir = 'output/'
    exc = ""

    input_file, input_file_extension = os.path.splitext(url)
    output_file = input_file + "_converted.mp4"

    input_path = os.path.join(vidcon_root + input_dir, input_file + input_file_extension)
    output_path = os.path.join(vidcon_root + output_dir, output_file)

     ffmpeg_cmd = """
        ffmpeg -i {0} -codec:v libx264 -profile:v high -preset slow -b:v 500k -maxrate 500k 
               -bufsize 1000k -vf scale=854:trunc(ow/a/2)*2 -threads 0 
               -codec:a mp3 -b:a 64k {1}""".format(input_path, output_path)



    std_err = ""
    std_in = ""
    output =""

    try:
        output = subprocess.check_output(shlex.split(ffmpeg_cmd))

        # p = subprocess.Popen(shlex.split(ffmpeg_cmd), bufsize=2048,
        #                                stdout=subprocess.PIPE,
        #                                stderr=subprocess.PIPE)    

        # std_in, std_err = map(lambda b: b.decode('utf-8').replace(os.linesep, '\n'),
        #                 p.communicate((os.linesep).encode('utf-8')))

        # err, output = p.communicate()

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
        # raise subprocess.CalledProcessError(ex.returncode, ffmpeg_cmd, output="---start---{}---end---".format(std_err))

    # err, output = map(lambda b: b.decode('utf-8').replace(os.linesep, '\n'),
    #            p.communicate((os.linesep).encode('utf-8')))
    # print(output)
    # print(err)

    # return_code = p.returncode
    # print(return_code)

    # result = Result(
    #     file_to_convert=url, 
    #     return_code=return_code,
    #     output1=output, 
    #     output2=err)
    # db.session.add(result)
    # db.session.commit()
    # return return_code


    #ffmpeg -i "F:\FFMPEG\Others\wmv.wmv" -codec:v libx264 -profile:v high -preset slow -b:v 300k -maxrate 350k -bufsize 1000k -vf scale=trunc(oh/a/2)*2:280 -threads 0 -codec:a mp3 -b:a 64k "F:\FFMPEG\Others\wmv.mp4





##########
# routes #
##########


@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    if request.method == "POST":
        # get url that the person has entered
        url = request.form['url']
        job = q.enqueue_call(
            func=convert, args=(url,), result_ttl=5000, timeout=10800
        )
        print(job.get_id())

    return render_template('index.html', results=results)

@app.route('/api/jobs', methods=['POST'])
def create_job():

    # vidcon_root = '/Volumes/EdulearnNetUpload/asknlearn/vidcon/'
    # input_dir = "input/"
    # input_file = os.path.join(vidcon_root + input_dir, filepath)

    # Request will be in this format:
    # {
    #     "input_file":"/Volumes/EdulearnNetUpload/asknlearn/vidcon/input/test1.ogg",
    #     "output_dir":"/Volumes/EdulearnNetUpload/asknlearn/vidcon/output"
    # }
    if not request.json or not 'input_file' in request.json:
        abort(400)


    input_file = request.json
    return jsonify({'filepath': input_file})

    # Verify that file exists before sending it to the queue

    # if os.path.isfile(input_file):
    #     return jsonify({'filepath': filepath})
    # else:
    #     return jsonify({'Error': "File does not exist."})


# @app.route("/results/<job_key>", methods=['GET'])
# def get_results(job_key):

#     job = Job.fetch(job_key, connection=conn)

#     if job.is_finished:
#         result = Result.query.filter_by(id=job.result).first()
#         results = sorted(
#             result.result_no_stop_words.items(),
#             key=operator.itemgetter(1),
#             reverse=True
#         )[:10]
#         return jsonify(results)
#     else:
#         return job.get_status(), 202

class GazzaThinksItFailedError(Exception):
    pass


if __name__ == '__main__':
    app.run()


