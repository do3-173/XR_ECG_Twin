FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator files
COPY ecg_processor.py .
COPY smartwatch_simulator.py .
COPY config.py .
COPY simulator/entrypoint.sh .

# Copy dataset
COPY dataset/ ./dataset/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
