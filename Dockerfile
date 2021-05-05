FROM python:3-alpine

COPY requirements.txt tgrssbot.py ./

RUN apk add musl-dev build-base \
 && pip install -r /requirements.txt \
 && apk del musl-dev build-base

ENTRYPOINT ["python", "/tgrssbot.py"]
