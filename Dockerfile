FROM python:3.7

WORKDIR /mycloud

COPY ./Pipfile ./Pipfile
COPY ./Pipfile.lock ./Pipfile.lock
RUN pip install pipenv && \
    pipenv install --system --deploy --ignore-pipfile 

COPY ./ ./

ENTRYPOINT ["python", "-m", "mycloud"]
