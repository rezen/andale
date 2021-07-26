FROM python:3.9-buster
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN mkdir -p /app
WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt  

COPY ./src /app

CMD ['ls', '-lah']