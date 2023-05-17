FROM python:3.11-slim-bullseye

WORKDIR /code

COPY shovel/requirements.txt .
RUN pip install -r requirements.txt
COPY shovel/requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY shovel/ shovel/
COPY integration_tests/ integration_tests/
CMD ["pytest", "--junitxml=/artifacts/test-results.xml", "integration_tests"]
