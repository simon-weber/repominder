FROM python:3.7.3-slim-stretch

WORKDIR /app
EXPOSE 8000
ENV DJANGO_SETTINGS_MODULE=repominder.settings

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ADD docker-archive.tar ./

RUN groupadd --gid 499 repominder \
  && useradd --uid 497 --gid repominder --shell /bin/bash --create-home repominder
USER repominder:repominder
CMD ["gunicorn", "--worker-class", "gevent", "repominder.wsgi", "-b", "0.0.0.0:8000"]
