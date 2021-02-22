FROM python:3.9.2-buster
RUN apt-get update && apt-get install -y postgresql
WORKDIR /app/
COPY requirements.txt /app/
RUN pip install -U pip && pip install -r requirements.txt
COPY *.py /app/
COPY ./app /app/app
