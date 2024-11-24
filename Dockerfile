FROM python:3.12
LABEL authors="fernando"

RUN apt-get update && apt-get install -y chromium \
    chromium-driver\
    && apt-get clean

RUN chmod +x /usr/bin/chromedriver

# Definir diretório de trabalho
WORKDIR /code

# Copiar dependências e código da aplicação
COPY ./requirements.txt /code/requirements.txt
COPY ./settings.py /code/settings.py
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./src /code/src

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
