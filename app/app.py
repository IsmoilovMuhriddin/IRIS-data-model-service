""" Flask app for client configuation of routes """
import json
from flask import Flask, request, send_file
from flask import render_template
import tasks
APP = Flask(__name__)

@APP.route('/')
def index():
    """ index page of Client web app """
    return render_template('index.html')


@APP.route('/predict', methods=['POST'])
def predict():
    """ predicts route - creates new task and waits """
    data = request.form.to_dict()
    data.pop('Submit')
    job = tasks.get_prediction.delay(data)
    return render_template('home.html', JOBID=job.id)


@APP.route('/result')
def result():
    """ result route - return pdf result when ready """
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        pdf_output = job.get()
        return send_file('./' + pdf_output, attachment_filename=str(jobid)+'.pdf')
    return 404


@APP.route('/progress')
def progress():
    """ progress route - checks the progress of given task id """
    jobid = request.values.get('jobid')
    return_result = '{}'
    if jobid:
        job = tasks.get_job(jobid)
        if job.state == 'PROGRESS':
            return_result = json.dumps(dict(
                state=job.state,
                progress=job.result['current'],
            ))
        elif job.state == 'SUCCESS':
            return_result = json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
        elif job.state == 'FAILURE':
            return_result = json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
    return return_result




if __name__ == '__main__':
    APP.run(host='0.0.0.0')
