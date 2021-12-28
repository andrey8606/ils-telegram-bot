FROM python:3.8-slim-buster

WORKDIR /app
COPY . .
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

CMD python main.py