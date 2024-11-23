FROM python:3.12
LABEL authors="fernando"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./settings.py /code/settings.py
COPY ./src /code/src

RUN apt-get update && apt-get install -y \
    libglib2.0-0=2.50.3-2 \
    libnss3=2:3.26.2-1.1+deb9u1 \
    libgconf-2-4=3.2.6-4+b1 \
    libfontconfig1=2.11.0-6.7+b1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["uvicorn", "src.api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]

#ENTRYPOINT ["top", "-b"]