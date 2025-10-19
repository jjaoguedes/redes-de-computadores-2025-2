# mqtt_rtt.py
import time, json, uuid, statistics, os
import paho.mqtt.client as mqtt

# ===================== Config =====================
BROKER_HOST = os.getenv("MQTT_HOST", "broker.emqx.io")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
BASE_TOPIC  = os.getenv("MQTT_BASE", "serverMQTT/")
QOS         = int(os.getenv("MQTT_QOS", "1"))
CLIENT_ID   = os.getenv("MQTT_ID", "rtt-client")

REQ_TOPIC = f"{BASE_TOPIC}/echo/req"
RESP_TOPIC = f"{BASE_TOPIC}/echo/resp"

N_MESSAGES = int(os.getenv("N", "50"))      # total de mensagens
BYTES      = int(os.getenv("BYTES", "32"))  # tamanho extra (além do JSON)
SLEEP_S    = float(os.getenv("SLEEP", "0.02"))
TIMEOUT_S  = float(os.getenv("TIMEOUT", "10"))
# ====================================================

pending = {}   # id -> t0
rtts = []
received = 0

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[client] conectado em {BROKER_HOST}:{BROKER_PORT} rc={reason_code}")
    client.subscribe(RESP_TOPIC, qos=QOS)
    print(f"[client] assinando: {RESP_TOPIC} (QoS={QOS})")

def on_message(client, userdata, msg):
    global received
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        _id = data.get("id")
        t0 = pending.pop(_id, None)
        if t0 is not None:
            rtt_ms = (time.perf_counter() - t0) * 1000.0
            rtts.append(rtt_ms)
            received += 1
            if received % 10 == 0:
                print(f"[{received}] RTT médio parcial: {statistics.mean(rtts):.2f} ms")
    except Exception:
        pass

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID, clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message

    # TLS opcional (usar porta 8883 e descomentar 3 linhas abaixo):
    # import ssl
    # client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    # client.tls_insecure_set(False)

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    client.loop_start()
    time.sleep(1.0)  # pequena janela para completar a assinatura

    for i in range(N_MESSAGES):
        _id = str(uuid.uuid4())
        blob = "x" * BYTES
        payload = {"id": _id, "seq": i, "ts": time.time(), "blob": blob}
        pending[_id] = time.perf_counter()
        client.publish(REQ_TOPIC, json.dumps(payload), qos=QOS)
        time.sleep(SLEEP_S)

    # aguarda respostas remanescentes
    deadline = time.time() + TIMEOUT_S
    while pending and time.time() < deadline:
        time.sleep(0.05)

    client.loop_stop()
    client.disconnect()

    sent = N_MESSAGES
    lost = len(pending)
    recv = sent - lost

    print("\n=== MQTT (público) ===")
    print(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"Topic base: {BASE_TOPIC}")
    print(f"Enviadas: {sent} | Recebidas: {recv} | Perdas: {lost}")
    if rtts:
        print(f"RTT média:   {statistics.mean(rtts):.2f} ms")
        print(f"RTT mediana: {statistics.median(rtts):.2f} ms")
        try:
            p95 = statistics.quantiles(rtts, n=20)[18]  # ~p95
            print(f"RTT p95:     {p95:.2f} ms")
        except Exception:
            pass
        print(f"RTT máx.:    {max(rtts):.2f} ms")
    else:
        print("Sem RTTs calculados. Verifique broker/eco/namespace de tópicos.")

if __name__ == "__main__":
    main()
