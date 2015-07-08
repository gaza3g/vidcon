import os
import sys
import subprocess
import shlex
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask import jsonify
from rq import Queue, get_current_job
from rq.job import Job
from worker import conn

#################
# configuration #
#################

app = Flask(__name__)
#app.config.from_object(os.environ['APP_SETTINGS'])
app.config.from_object("config.DevelopmentConfig")
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

    # vidcon_root = '/Volumes/EdulearnNetUpload/asknlearn/vidcon/'

    vidcon_root = '/media/edulearnupload/'

    input_dir = 'input/'
    output_dir = 'output/'
    exc = ""

    input_file = url
    output_file = url + "_converted.mp4"

    input_path = os.path.join(vidcon_root + input_dir, input_file)
    output_path = os.path.join(vidcon_root + output_dir, output_file)

    ffmpeg_cmd = """
		ffmpeg 	-i {0} -c:v libx264 -crf 23 -profile:v baseline
    			-level 3.0 -pix_fmt yuv420p -c:a aac -ac 2 -strict experimental -b:a 128k
				-movflags faststart
 				{1} -y""".format(input_path, output_path)

    try:
        output = subprocess.check_output(shlex.split(ffmpeg_cmd))

        # p = subprocess.check_output(shlex.split(ffmpeg_cmd), bufsize=2048,
        #                                stdout=subprocess.PIPE,
        #                                stderr=subprocess.PIPE)
        print("Success: {}", output)
    except subprocess.CalledProcessError as ex:
        print("Error: {}".format(ex.output))
        raise subprocess.CalledProcessError(ex.returncode, ffmpeg_cmd, output=ex.output)
        # print("Error")

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


if __name__ == '__main__':
    app.run()

