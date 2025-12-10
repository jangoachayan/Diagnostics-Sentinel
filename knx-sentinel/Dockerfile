ARG BUILD_FROM
FROM $BUILD_FROM

# Install pip requirements
RUN pip3 install --no-cache-dir \
    aiohttp \
    paho-mqtt

# Copy data for add-on
# Copy data for add-on
COPY src /app/src
COPY run.py /app/run.py

# Bypass S6 init and run python directly to ensure env vars are present
ENTRYPOINT [ "python3", "/app/run.py" ]
