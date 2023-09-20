FROM debian:stable

WORKDIR /app
COPY ./app .
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv
ENV VIRTUAL_ENV=/app/env
RUN mkdir env && python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN . /app/env/bin/activate && pip install -r requirements.txt

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/config/pubsub-credential.json
CMD ["python3", "main.py"]
