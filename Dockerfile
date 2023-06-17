FROM python:3.8-slim

## install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc

## create virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

## set working directory
WORKDIR /app

## copy requirements.txt
COPY requirements.txt .

## install requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

## copy the rest of the application code
COPY . .

## set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

## run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
