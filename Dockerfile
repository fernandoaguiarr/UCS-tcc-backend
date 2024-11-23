FROM selenium/standalone-chrome:latest
LABEL authors="fernando"

#USER root  # Garante permissões de superusuário
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./settings.py /code/settings.py
COPY ./src /code/src

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["uvicorn", "src.api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]

#ENTRYPOINT ["top", "-b"]