FROM alpine:latest as dev-env
RUN apk add --no-cache \
    python \
    python-dev \
    py-pip \
    bash \
    curl
WORKDIR /service
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 5000

FROM python:3-alpine
WORKDIR /service
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . ./
EXPOSE 5000
ENTRYPOINT ["python3", "qotm/qotm.py"]
