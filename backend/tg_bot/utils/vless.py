from urllib.parse import quote
import json

def generate_vless_url(obj: dict, domain: str) -> str:
    settings = json.loads(obj["settings"])
    stream = json.loads(obj["streamSettings"])
    reality = stream["realitySettings"]
    reality_settings = reality["settings"]

    uuid = settings["clients"][0]["id"]
    port = obj["port"]
    pbk = reality_settings["publicKey"]
    fp = reality_settings.get("fingerprint", "chrome")
    sni = reality["dest"].split(":")[0]
    sid = reality["shortIds"][0]
    spx = reality_settings.get("spiderX", "2F")
    label = obj["remark"]

    query = (
        f"type=tcp"
        f"&security=reality"
        f"&pbk={pbk}"
        f"&fp={fp}"
        f"&sni={sni}"
        f"&sid={sid}"
        f"&spx=%2F"
        f"&flow=xtls-rprx-vision"
    )

    # Делай красивый label с почтой, как в UI, если хочешь
    label_encoded = quote(f"{label}-{label}@vpn")

    return f"vless://{uuid}@{domain}:{port}?{query}#{label_encoded}"