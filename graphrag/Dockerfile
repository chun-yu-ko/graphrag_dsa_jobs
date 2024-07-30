FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl python3-pip

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install gsutil

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG GOOGLE_APPLICATION_CREDENTIALS
ENV GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}

RUN gsutil -m cp -r "gs://graphrag_dsa_jobs/artifacts" /app

COPY . .

EXPOSE 8012

CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8012"]