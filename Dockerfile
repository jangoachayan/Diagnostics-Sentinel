ARG BUILD_FROM
FROM $BUILD_FROM

# Install pip requirements
RUN pip3 install --no-cache-dir \
    aiohttp \
    paho-mqtt

# Copy data for add-on
COPY src /app/src
COPY run.py /app/run.py

CMD [ "python3", "/app/run.py" ]
