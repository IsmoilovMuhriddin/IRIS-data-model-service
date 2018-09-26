""" Celery Tasks for the predicting and result progress"""
from celery import Celery, current_task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from sklearn.externals import joblib
from fpdf import FPDF

MODEL_FILENAME = 'finalized_model.sav'
LOADED_MODEL = joblib.load(MODEL_FILENAME)
REDIS_URL = 'redis://redis:6379/0'
BROKER_URL = 'amqp://admin:mypass@rabbit//'
LOGGER = get_task_logger(__name__)
CELERY = Celery('tasks',
                backend=REDIS_URL,
                broker=BROKER_URL)


CELERY.conf.accept_content = ['json', 'msgpack']
CELERY.conf.result_serializer = 'msgpack'

def get_job(job_id):
    """ returns task of the given id"""
    return AsyncResult(job_id, app=CELERY)

KEYS = ['Sepal length', 'Sepal width', 'Petal length', 'Petal width']
@CELERY.task()
def get_prediction(data):
    """ input sample data input- predicts result and creates pdf """
    jobid = current_task.request.id
    current_task.update_state(state='PROGRESS', meta={'current':0.1})
    LOGGER.info('JobId: %s, Status: PROGRESS, Meta: prediction started', jobid)

    verified_data = True
    for i in KEYS:
        verified_data = verified_data and (i in data)
    LOGGER.info('JobId: %s, Status: PROGRESS, Meta: data verified', jobid)
    current_task.update_state(state='PROGRESS', meta={'current': 0.2})
    if verified_data:
        result = LOADED_MODEL.predict([[float(data[x]) for x in KEYS]])
        LOGGER.info('JobId: {%s}, Status: PROGRESS, Meta: model predicted = %s ', jobid, result)
        string_result = ''
        current_task.update_state(state='PROGRESS', meta={'current': 0.6})
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        line = 1
        LOGGER.info('JobId: %s, Status: PROGRESS, Meta: starting to write to pdf', jobid)
        for key, val in data.items():
            data_line = key + ' = ' + str(val)
            string_result += data_line + '\n'
            pdf.cell(50, 10, txt=data_line, ln=line, align="C")
            line += 1
        current_task.update_state(state='PROGRESS', meta={'current': 0.8})
        pdf.cell(50, 10, txt='Predicted:' + result[0], ln=line, align="C")
        result_filename = 'results_data/'+str(jobid)+'.pdf'
        pdf.output(result_filename)
        LOGGER.info('JobId: %s, Status: PROGRESS, Meta: written to pdf', jobid)
        current_task.update_state(state='PROGRESS', meta={'current': 0.9})
        return result_filename
    current_task.update_state(state='FAILURE', meta={'current': 1})
    LOGGER.info('JobId: %s, Status: FAILURE, Meta: data format is wrong', jobid)
    return "error: data type is wrong"
