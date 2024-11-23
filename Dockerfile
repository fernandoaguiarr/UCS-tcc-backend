FROM selenium/standalone-chrome:latest
LABEL authors="fernando"

USER root

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./settings.py /code/settings.py
COPY ./src /code/src

# Criar ambiente virtual e instalar dependências
RUN python3 -m venv /code/venv && \
    /code/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /code/venv/bin/pip install --no-cache-dir -r /code/requirements.txt

# Adicionar o venv ao PATH
ENV PATH="/code/venv/bin:$PATH"

#RUN #pip install --no-cache-dir --upgrade -r /code/requirements.txt

USER seluser

CMD ["uvicorn", "src.api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]

#ENTRYPOINT ["top", "-b"]