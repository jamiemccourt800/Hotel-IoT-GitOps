FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy operator code
COPY operator.py /app/

# Run as non-root user
RUN useradd -m -u 1000 operator && \
    chown -R operator:operator /app

USER operator

CMD ["python", "-u", "operator.py"]
