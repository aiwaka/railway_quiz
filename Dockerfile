FROM python:3.9

ARG PROJECT_DIR=/app/

ADD app/requirements.txt ${PROJECT_DIR}

WORKDIR $PROJECT_DIR

RUN pip install -r requirements.txt