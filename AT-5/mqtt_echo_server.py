# mqtt_echo_server.py
import json
import os
import paho.mqtt.client as mqtt

# ===================== Config =====================
BROKER_HOST = os.getenv("MQTT_HOST", "broker.emqx.io")  # alternativas: test.mosquitto.org, broker.hivemq.com
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))       # TLS? use 8883 e veja nota no final
BASE_TOPIC  = os.getenv("MQTT_BASE", "ufam/ceteli/mqttlab/grupo01")
QOS         = int(os.getenv("MQTT_QOS", "1"))           # 0, 1, 2 (2 pode não ser suportado)
CLIENT_ID   = os.getenv("MQTT_ID", "echo-server")
REQ_TOPIC   = f"{BASE_TOPIC}/echo/req"
RESP_TOPIC  = f"{BASE_TOPIC}/echo/resp"
# ====================================================

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[echo] conectado ao broker {BROKER_HOST}:{BROKER_PORT} rc={reason_code}")
    client.subscribe(REQ_TOPIC, qos=QOS)
    print(f"[echo] assinando: {REQ_TOPIC} (QoS={QOS})")
    print(f"[echo] respondendo em: {RESP_TOPIC} (QoS={QOS})")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        # Reenvia o mesmo JSON (eco)
        client.publish(RESP_TOPIC, json.dumps(data), qos=min(QOS, msg.qos or 0))
    except Exception:
        # Se não for JSON válido, ecoa como veio (binário/bytes)
        client.publish(RESP_TOPIC, msg.payload, qos=min(QOS, msg.qos or 0))

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID, clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message

    # Para TLS público (porta 8883), descomente:
    # import ssl
    # client.tls_set(cert_reqs=ssl.CERT_REQUIRED)  # certificado raiz padrão do sistema
    # client.tls_insecure_set(False)

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    client.loop_forever()

if __name__ == "__main__":
    main()
