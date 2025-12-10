# KNX Sentinel

**High-Fidelity Home Assistant Add-on for Distributed KNX Monitoring**

![Logo](https://brands.home-assistant.io/_/knx/logo.png)

KNX Sentinel is a professional-grade monitoring agent designed to run as a Home Assistant Add-on. It transforms a standard Home Assistant installation into an intelligent edge-computing node, capable of analyzing KNX bus traffic in real-time and transmitting enriched telemetry to a central MQTT broker.

## Key Features

- **Zero-Hardware**: Runs entirely within the Home Assistant Supervisor ecosystem.
- **Edge Intelligence**: Implements local anomaly detection (Z-Score) and diagnostic logic (Linear Regression) to reduce cloud bandwidth and latency.
- **Robust Ingestion**: Uses asynchronous WebSockets with exponential backoff to ingest data accurately from Home Assistant Core.
- **Reliable Egress**: Buffers and transmits data via MQTT with QoS 1, ensuring no data loss during network interruptions.
- **Secure**: Zero inbound ports required; fully compatible with TLS-encrypted MQTT brokers (AWS IoT, HiveMQ).

## Architecture

```mermaid
graph TD
    subgraph "Home Assistant Host"
        Core[Home Assistant Core] -- WebSocket API --> Ingestion[Ingestion Layer]
        Ingestion -- Filtered Events --> MathKernel[Math Kernel\n(Z-Score / Linear Reg)]
        MathKernel -- Enriched Telemetry --> Egress[MQTT Egress]
    end
    
    Egress -- MQTT (TLS) --> CloudBroker[Remote MQTT Broker\n(e.g., HiveMQ)]
    CloudBroker --> Dashboard[Central Dashboard\n(Grafana)]
```

## Installation

### Prerequisites
- Home Assistant OS or Supervised installation.
- A working KNX integration in Home Assistant.

### Local Development Installation
1. Copy this repository to your Home Assistant `addons/` directory.
2. Navigate to **Settings > Add-ons > Add-on Store**.
3. Click **Check for updates** in the top right.
4. "KNX Sentinel" should appear in the "Local Add-ons" section.
5. Click **Install**.

## Configuration

Configure the Add-on via the **Configuration** tab in the Home Assistant UI.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `client_id` | string | `default_client` | Unique identifier for your organization (e.g., `client_acme`). |
| `site_id` | string | `default_site` | Unique identifier for the location (e.g., `site_london`). |
| `mqtt_broker` | string | `localhost` | IP or Hostname of the MQTT Broker. |
| `mqtt_port` | int | `1883` | MQTT Port (typically 1883 for TCP, 8883 for TLS). |
| `mqtt_username` | string | - | MQTT Username. |
| `mqtt_password` | string | - | MQTT Password. |
| `mqtt_use_tls` | bool | `false` | Enable TLS/SSL encryption. |
| `target_entities` | list | `["sensor.knx*"]` | List of entities or glob patterns to monitor. |

## Quick Start: Connecting to HiveMQ Cloud

KNX Sentinel supports secure cloud brokers like HiveMQ out of the box.

1. **Create HiveMQ Cluster**:
   - Sign up at [HiveMQ Cloud](https://console.hivemq.cloud/).
   - Create a free Serverless cluster.
   - Note your **Cluster URL** (e.g., `ClusterID.s1.eu.hivemq.cloud`).

2. **Create Credentials**:
   - Go to **Access Management**.
   - Create a new username and password for the Sentinel agent.

3. **Configure Add-on**:
   - `mqtt_broker`: `ClusterID.s1.eu.hivemq.cloud`
   - `mqtt_port`: `8883`
   - `mqtt_use_tls`: `true`
   - `mqtt_username`: `your_user`
   - `mqtt_password`: `your_password`

4. **Start & Verify**:
   - Start the Add-on.
   - Check the **Log** tab. You should see:
     ```
     INFO - Connecting to MQTT Broker...
     INFO - Enabling TLS for MQTT connection
     INFO - Connected to MQTT Broker!
     ```

## Troubleshooting

- **"Connection Refused"**: Check if the Home Assistant Core is running and accepting WebSocket connections.
- **"Auth Error"**: Ensure the Add-on has `homeassistant_api: true` in `config.yaml`.
- **"MQTT TLS Error"**: Ensure you are using the correct port (usually 8883 for TLS) and that `mqtt_use_tls` is set to `true`.

## License

MIT License.
