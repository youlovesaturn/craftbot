FROM python:slim AS builder
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:slim
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]