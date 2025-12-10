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
COPY run.sh /etc/services.d/knx-sentinel/run

# Fix permissions
RUN chmod a+x /etc/services.d/knx-sentinel/run
