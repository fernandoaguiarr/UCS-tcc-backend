FROM selenium/standalone-chrome:latest
LABEL authors="fernando"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./settings.py /code/settings.py
COPY ./src /code/src

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["uvicorn", "src.api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]

#ENTRYPOINT ["top", "-b"]