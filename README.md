# Using Celery with Flask for predicting class of IRIS data and reporting it as a pdf

This tutorial explains how to configure Flask, Celery, RabbitMQ and Redis, together with Docker to build a web service that predicts iris class by trained model and dynamically generates pdf and loads this contend when it is ready to be displayed. We'll focus mainly on Celery and the servies that surround it. Docker is a bit more straightforward.

## Contents

1. [Part 1 - Project Structure](https://github.com/IsmoilovMuhriddin/IRIS-data-model-service/tree/readme#part-1---project-structure)
1. [Part 2 - Creating the Flask application](https://github.com/IsmoilovMuhriddin/IRIS-data-model-service/tree/readme#part-2---creating-the-flask-application)
1. [Part 3 - Expanding our web app to use Celery](https://github.com/IsmoilovMuhriddin/IRIS-data-model-service/tree/readme#part-3---expanding-our-web-app-to-use-celery)
1. [Part 4 - Using Docker to package our application](https://github.com/IsmoilovMuhriddin/IRIS-data-model-service/tree/readme#part-4---using-docker-to-package-our-application)

## Part 1 - Project Structure

The finished project structure will be as follows:
```
.
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── .dockerignore
├── README.md
├── app
│   ├── app.py
│   ├── tasks.py
│   └── templates
│       ├── home.html
│       └── index.html
├── scripts
│   ├── run_celery.sh
│   └── run_web.sh
└── requirements.txt
```

## Part 2 - Creating the Flask application

First we create an folder for our app. For this example, our folder is simply called `app`. Within this folder, create an `app.py` file and an empty folder named `templates` where our HTML templates will be stored.

For our app, we first include some basic Flask libraries and create an instance of the app:

```python
from flask import Flask, request
from flask import render_template, make_response

APP = Flask(__name__)
```

We define three routes for Flask to implement: a landing page, a secondary page that embeds and result, and a route for the this result as a pdf. Our pdf result route generates a pdf dynamically. For this example, it generates a pdf using `fpdf` and some delays are also included so that the time taken to create the pdf is more apparent.

```python
@APP.route('/')
def index():
    return render_template('index.html')
```

```python
@APP.route('/predict')
def predict():
    data = request.form.to_dict()
    data.pop('Submit')
    print(request.form)
    job = tasks.get_prediction.delay(data)
    return render_template('home.html', JOBID=job.id)
```

```python
@APP.route('/result')
def result():
	jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        pdf_output = job.get()
        return send_file('./' + pdf_output,attachment_filename=str(jobid)+'.pdf')
    else:
        return 404
```

Next, we need to open our `templates` folder and create the following two templates:

#### home.html
```html
<h3>IRIS Data Prediction</h3>
<div id="imgpl">Prediction is not yet ready. Please wait...</div>
<div id="wrapper">
    <div id="prog">
        <div id="bar"></div>
    </div>
</div>
```

#### index.html
```html
<h1>Predicting IRIS Class by its attributes</h1>

<!-- 'Sepal length', 'Sepal width', 'Petal length','Petal width' -->

<form method="POST" action="{{ url_for('.predict')}}" style="background-color:#CCCCCC">
    <pre>
    Sepal length <input name="Sepal length"  type=number step=0.01 min="0.01" max="10.0" required /><br>
    Sepal width  <input name="Sepal width" type=number step=0.01 min="0.01" max="10.0" required/><br>
    Petal length <input name="Petal length" type=number step=0.01 min="0.01" max="10.0" required/><br>
    Petal width  <input name="Petal width" type=number step=0.01 min="0.01" max="10.0" required/><br>
    <input type="submit" name="Submit" value="Submit">
    </pre>
</form >
```


app.py
```python
if __name__ == '__main__':
    APP.run(host='0.0.0.0')
``` 

## Part 3 - Expanding our web app to use Celery

In our `app` directory, create the `tasks.py` file that will contain our Celery tasks. We add the neccessary Celery includes:

```python
from celery import Celery, current_task
from celery.result import AsyncResult
```

Assuming that our RabbitMQ service is on a host that we can reference by `rabbit` and our Redis service is on a host referred to by `redis` we can create an instance of Celery using the following:

```python
REDIS_URL = 'redis://redis:6379/0'
BROKER_URL = 'amqp://admin:mypass@rabbit//'

CELERY = Celery('tasks',
                backend=REDIS_URL,
                broker=BROKER_URL)
```



```python
CELERY.conf.accept_content = ['json', 'msgpack']
CELERY.conf.result_serializer = 'msgpack'
```

First, we'll implement a function that returns a jobs given an ID. This allows our app and the Celery tasks to talk to each other:

```python
def get_job(job_id):
    return AsyncResult(job_id, app=CELERY)
```

Next, we define the asynchronous function and add the function decorator that allows the method to be queued for execution:

```python
def get_job(job_id):
    return AsyncResult(job_id, app=CELERY)
```



```python
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
    current_task.update_state(state='PROGRESS',meta = {'current':0.1})
    verified_data = True
    for i in keys:
        verified_data = verified_data and (i in data) 
    current_task.update_state(state='PROGRESS', meta={'current': 0.2})
    if verified_data:
        result = loaded_model.predict([[float(data[x]) for x in keys]])
        string_result = ''
        current_task.update_state(state='PROGRESS', meta={'current': 0.6})
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        line = 1

        for k, v in data.items():
            data = k + ' = ' + str(v)
            string_result += data + '\n'
            pdf.cell(50, 10, txt=data, ln=line, align="C")
            line += 1
        current_task.update_state(state='PROGRESS', meta={'current': 0.8})
        jobid = current_task.request.id
        pdf.cell(50, 10, txt='Predicted:' + result[0], ln=line, align="C")
        result_filename = 'results_data/'+str(jobid)+'.pdf'
        pdf.output(result_filename)
        current_task.update_state(state='PROGRESS', meta={'current': 0.9})
        return result_filename
    current_task.update_state(state='FAILURE', meta={'current': 1})
    return "error: data type is wrong"

```

Instead of building a response, we return the path to the pdf which will be stored on Redis. We also update the task at various points with a progress indicator that can be queried from the Flask app.

We add a new route to `app.py` that checks the progress and returns the state as a JSON object so that we can write an ajax function that our client can query before loading the final pdf when it's ready.

```python
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
```

Extend our `templates/home.html` with the following Javascript code:

```JavaScript
<script src="//code.jquery.com/jquery-2.1.1.min.js"></script>
<script>
    function poll() {
        $.ajax("{{url_for('.progress', jobid=JOBID)}}", {
            dataType: "json"
            , success: function (resp) {
                $("#bar").css({ width: $("#prog").width() * resp.progress });
                if ((resp.progress >= 0.99)&&(resp.state !="FAILURE")) {
                    $("#wrapper").html('');
                    $("#imgpl").html('<a href="result?jobid={{JOBID}}"> <p>Here will be your pdf result {{resp}}</p></a>');

                    return;
                } 
                else if (resp.state == "FAILURE") {
                    $("#wrapper").html('');
                    $("#imgpl").html('<p>Some Error ocuured , Task ID = {{JOBID}}, STATE = FAILURE </p>');
                }
                else {
                    setTimeout(poll, 500.0);
                }
            }
        });
    }
    $(function () {
        var JOBID = "{{ JOBID }}";
        poll();
    });
</script>

```

The `poll` function repeatedly requires the `/progress` route of our web app and when it reports that the pdf has been generated, it replaces the HTML code within the placeholder with the URL of the pdf, which is then loaded dynamically from our modified `/result` route:

```python
@APP.route('/result')
def result():
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        pdf_output = job.get()
        return send_file('./' + pdf_output,attachment_filename=str(jobid)+'.pdf')
    else:
        return 404
```

At this stage we have a working web app with asynchronous pdf generation.

## Part 4 - Using Docker to package our application

Our app requires 4 separate containers for each of our servies:
* Flask
* Celery
* RabbitMQ
* Redis

Docker provides prebuilt containers for [RabbitMQ](https://hub.docker.com/_/rabbitmq/) and [Redis](https://hub.docker.com/_/redis/). These both work well and we'll use them as is.

For Flask and Celery, we'll build two identical containers from a simple `Dockerfile`.

```bash
# Pull the 3.6.5  version of the Python container.
FROM python:3.6.5

# Add the requirements.txt file to the image.
ADD requirements.txt /app/requirements.txt

# Set the working directory to /app/.
WORKDIR /app/

# Install Python dependencies.
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Create an unprivileged user for running our Python code.
RUN adduser --disabled-password --gecos '' app  
```

We pull all of this together with a Docker compose file, `docker-compose.yml`. While early versions of compose needed to expose ports for each service, we can link the services together using the `links` keyword. The `depends` keyword ensures that all of our services start in the correct order.

To create and run the container, use:

    docker-compose build
    docker-compose up

One of the major benefits of Docker is that we can run multiple instances of a container if required. To run multiple instances of our Celery consumers, do:

    docker-compose scale worker=N

where N is the desired number of backend worker nodes.

Visit http://localhost:5000 to view our complete application.