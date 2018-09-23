FROM python:3.6.5

RUN export PIP_DEFAULT_TIMEOUT=100

ADD requirements.txt /app/requirements.txt

WORKDIR /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN adduser --disabled-password --gecos '' app 