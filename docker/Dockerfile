FROM python:3.11.3-alpine

RUN apk update
RUN apk add --no-cache git postgresql-dev gcc libc-dev
RUN apk add --no-cache gcc g++ make libffi-dev python3-dev build-base
RUN apk add py3-pip py3-pillow py3-cffi py3-brotli gcc musl-dev python3-dev pango
RUN apk add chromium
RUN apk add chromium-chromedriver
RUN apk add gettext

RUN pip install gunicorn
RUN pip install ipdb
RUN pip install ipython

WORKDIR /app

RUN git clone https://github.com/gonmarfer2/fundacion-reinicias.git .
RUN git checkout -b develop origin/develop
RUN git pull
RUN pip install -U pip

RUN pip install -r requirements.txt

ADD docker-settings.py reinicias/reinicias/settings.py
ADD docker-env reinicias/reinicias/.env

#CMD ["gunicorn", "-w 5", "decide.wsgi", "--timeout=500", "-b 0.0.0.0:5000"]