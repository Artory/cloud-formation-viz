FROM python:3.6-alpine

RUN apk add --no-cache graphviz

COPY . /app/
WORKDIR /app

RUN ["python", "setup.py", "install"]
