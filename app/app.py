from io import BytesIO
import json
from flask import Flask, request , send_file
from flask import render_template, make_response
import tasks
APP = Flask(__name__)

@APP.route('/')
def index():
    return render_template('index.html')


@APP.route('/predict', methods = ['POST'])
def predict():
    data = request.form.to_dict()
    data.pop('Submit')
    print(request.form)
    job = tasks.get_prediction.delay(data)
    return render_template('home.html', JOBID=job.id)


@APP.route('/result')
def result():
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        pdf_output = job.get()
        return send_file('./' + pdf_output,attachment_filename=str(jobid)+'.pdf')
    else:
        return 404


@APP.route('/progress')
def progress():
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state=job.state,
                progress=job.result['current'],
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
        elif job.state == 'FAILURE':
            return json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
    return '{}'




if __name__ == '__main__':
    APP.run(host='0.0.0.0')
