FROM python:3.7-alpine3.14

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
  gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
RUN pip install -r /requirements.txt
RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

# The directory vol helps to share those files with other containers
RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN adduser -D user
# give ownership of the directory vol to user
RUN chown -R user:user /vol/
# give write permission to owner, the rest can only read and excecute
# from the directory
RUN chmod -R 755 /vol/web
USER user