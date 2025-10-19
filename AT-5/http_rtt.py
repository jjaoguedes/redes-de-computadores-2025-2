# http_rtt.py
import time, uuid, os, statistics
import requests

# ===================== Config =====================
URL        = os.getenv("HTTP_URL", "https://httpbin.org/post")  # alternativo: https://postman-echo.com/post
N_MESSAGES = int(os.getenv("N", "50"))
BYTES      = int(os.getenv("BYTES", "32"))
SLEEP_S    = float(os.getenv("SLEEP", "0.02"))
TIMEOUT_S  = float(os.getenv("TIMEOUT", "5"))
# ====================================================

def main():
    rtts = []
    for i in range(N_MESSAGES):
        payload = {
            "id": str(uuid.uuid4()),
            "seq": i,
            "ts": time.time(),
            "blob": "x" * BYTES
        }
        t0 = time.perf_counter()
        r = requests.post(URL, json=payload, timeout=TIMEOUT_S)
        r.raise_for_status()
        _ = r.json()  # força parse (garante resposta ok)
        rtt_ms = (time.perf_counter() - t0) * 1000.0
        rtts.append(rtt_ms)
        if (i + 1) % 10 == 0:
            print(f"[{i+1}] RTT médio parcial: {statistics.mean(rtts):.2f} ms")
        time.sleep(SLEEP_S)

    print("\n=== HTTP (público) ===")
    print(f"URL: {URL}")
    print(f"Enviadas: {N_MESSAGES} | Recebidas: {N_MESSAGES} | Perdas: 0")
    print(f"RTT média:   {statistics.mean(rtts):.2f} ms")
    print(f"RTT mediana: {statistics.median(rtts):.2f} ms")
    try:
        p95 = statistics.quantiles(rtts, n=20)[18]  # ~p95
        print(f"RTT p95:     {p95:.2f} ms")
    except Exception:
        pass
    print(f"RTT máx.:    {max(rtts):.2f} ms")

if __name__ == "__main__":
    main()
