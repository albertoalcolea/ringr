FROM python:3.12.0

WORKDIR /app

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y portaudio19-dev

RUN python -m pip install --upgrade pip

COPY . .

RUN python -m pip install .

CMD ["ringr"]
