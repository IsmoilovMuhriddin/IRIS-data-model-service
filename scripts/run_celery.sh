#!/bin/sh
cd app  
su -m app -c "celery -A tasks worker --loglevel INFO" 