FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt
COPY ./app /app
COPY ./data /data
COPY ./main.py ./main.py


EXPOSE 8080


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
