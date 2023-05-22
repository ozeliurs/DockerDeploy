FROM python:latest

WORKDIR /app
ADD . /app

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]