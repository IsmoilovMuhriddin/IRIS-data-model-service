


import time
import random
import datetime
from flask import jsonify
from celery import Celery, current_task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from sklearn.externals import joblib
from fpdf import FPDF
import json

model_filename = 'finalized_model.sav'
loaded_model = joblib.load(model_filename)
REDIS_URL = 'redis://redis:6379/0'
BROKER_URL = 'amqp://admin:mypass@rabbit//'

CELERY = Celery('tasks',
                backend=REDIS_URL,
                broker=BROKER_URL)


CELERY.conf.accept_content = ['json', 'msgpack']
CELERY.conf.result_serializer = 'msgpack'


def get_job(job_id):
    return AsyncResult(job_id, app=CELERY)


"""
data = {
    "Sepal length" : "4.6",
    "Sepal width" : "3.1",
    "Petal length" : "1.5",
    "Petal width" : "0.2"
}
"""
keys = ['Sepal length', 'Sepal width', 'Petal length','Petal width']
@CELERY.task()
def get_prediction(data):
    jobid = current_task.request.id
    current_task.update_state(state='PROGRESS',meta = {'current':0.1})
    logger.info('JobId: {0}, Status: PROGRESS, Meta: prediction started'.format(jobid))

    verified_data = True
    for i in keys:
        verified_data = verified_data and (i in data) 
    logger.info('JobId: {0}, Status: PROGRESS, Meta: data verified = {1}'.format(jobid,data))
    
    current_task.update_state(state='PROGRESS', meta={'current': 0.2})
    if verified_data:
        result = loaded_model.predict([[float(data[x]) for x in keys]])
        logger.info('JobId: {0}, Status: PROGRESS, Meta: model predicted'.format(jobid))
    
        string_result = ''
        current_task.update_state(state='PROGRESS', meta={'current': 0.6})
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        line = 1
        logger.info('JobId: {0}, Status: PROGRESS, Meta: starting to write to pdf'.format(jobid))
    
        for k, v in data.items():
            data_line = k + ' = ' + str(v)
            string_result += data_line + '\n'
            pdf.cell(50, 10, txt=data_line, ln=line, align="C")
            line += 1
        
        current_task.update_state(state='PROGRESS', meta={'current': 0.8})
        
        pdf.cell(50, 10, txt='Predicted:' + result[0], ln=line, align="C")
        result_filename = 'results_data/'+str(jobid)+'.pdf'
        pdf.output(result_filename)
        logger.info('JobId: {0}, Status: PROGRESS, Meta: written to pdf'.format(jobid))
        current_task.update_state(state='PROGRESS', meta={'current': 0.9})
        return result_filename
    current_task.update_state(state='FAILURE', meta={'current': 1})
    logger.info('JobId: {0}, Status: FAILURE, Meta: data format is wrong'.format(jobid))
    return "error: data type is wrong"
