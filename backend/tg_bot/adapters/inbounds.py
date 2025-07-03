from typing import Literal
import httpx, time, json
from settings import domain_xui, port_xui, url_xui, username_xui, password_xui
from typing import Any
import uuid


async def get_inbounds(session_cookie: str) -> Any:
    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.get(
            f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/list",
            headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}
        )
        print(res)
        return res.json()


async def get_inbound(session_cookie: str, inbound_id: int) -> Any:
    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.get(
            f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/get/{inbound_id}",
            headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}
        )
        return res.json()


async def add_client(session_cookie: str, inbound_id: int, email: str, expiry_days: int = 30) -> Any:
    client_id = str(uuid.uuid4())  # генерируем UUID для клиента
    url = f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/addClient"

    expiry_time = int((time.time() + expiry_days * 86400) * 1000)
    # settings как JSON-строка
    settings_payload = {
        "clients": [
            {
                "id": client_id,
                "email": email,
                "flow": "",
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": expiry_time,
                "enable": True
            }
        ]
    }

    payload = {
        "id": inbound_id,
        "settings": json.dumps(settings_payload)  # <-- превращаем в строку
    }

    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.post(
            url,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            },
            json=payload
        )
        res.raise_for_status()
        return res.json()


async def delete_inbound(session_cookie: str, inbound_id: int) -> Any:
    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.post(
            f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/del/{inbound_id}",
            headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}
        )
        return res.json()


async def delete_client(session_cookie: str, inbound_id: int, client_email: str) -> Any:
    # Сначала получаем inbound, чтобы найти UUID клиента по email
    inbound = await get_inbound(session_cookie, inbound_id)
    if not inbound.get("obj"):
        return {"success": False, "msg": "Inbound not found"}
    
    settings = json.loads(inbound["obj"]["settings"])
    clients = settings.get("clients", [])
    
    # Ищем клиента по email
    client_uuid = None
    for client in clients:
        if client["email"] == client_email:
            client_uuid = client["id"]
            break
    
    if not client_uuid:
        return {"success": False, "msg": "Client not found"}
    
    # Теперь делаем запрос на удаление
    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.post(
            f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
        return res.json()


async def get_client(session_cookie: str, email: str) -> Any:
    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.get(
            f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/getClientTraffics/{email}",
            headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}
        )
        return res.json()


async def get_client_uuid(session_cookie: str, inbound_id: int, email: str) -> str | None:
    async with httpx.AsyncClient(verify=False, cookies={"3x-ui": session_cookie}) as client:
        res = await client.get(
            f"https://{domain_xui}:{port_xui}/{url_xui}/panel/api/inbounds/get/{inbound_id}",
            headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}
        )
        inbound = res.json()
        sett = json.loads(inbound["obj"]["settings"])
        for client_info in sett["clients"]:
            if client_info["email"] == email:
                return client_info["id"]
        return None


async def add_inbound_with_reality(
        session_cookie: str,
        base_url: str,
        uuid: str,
        remark: str,
        port: int,
        public_key: str,
        private_key: str,
        sni: str,
        dest: str,
        short_id: str = "",
        expiry_days: int = 7,
        network_type: Literal["tcp", "grpc"] = "grpc"
):
    """
    Создаёт VLESS + Reality inbound с одним клиентом (tcp или grpc) и полной структурой realitySettings.
    grpc пока в тесте.
    """

    url = f"{base_url}/panel/api/inbounds/add"
    expiry_time_ms = int((time.time() + expiry_days * 86400) * 1000) if expiry_days > 0 else 0

    # Полная структура realitySettings
    stream_settings = {
        "network": network_type,
        "security": "reality",
        "realitySettings": {
            "show": False,
            "xver": 0,
            "dest": dest,
            "serverNames": sni.split(","),
            "privateKey": private_key,
            "shortIds": [short_id],
            "minClient": "",
            "maxClient": "",
            "maxTimediff": 0,
            "settings": {
                "publicKey": public_key,
                "fingerprint": "chrome",
                "serverName": "",
                "spiderX": "/"
            }
        }
    }

    # GRPC специфичные настройки
    if network_type == "grpc":
        stream_settings["grpcSettings"] = {
            "serviceName": "grpc",
            "multiMode": False
        }

    payload = {
        "enable": True,
        "remark": remark,
        "listen": "",
        "port": port,
        "protocol": "vless",
        "expiryTime": 0,
        "settings": json.dumps({
            "clients": [{
                "id": uuid,
                "flow": "xtls-rprx-vision",
                "email": f"{remark}@vpn"
            }],
            "decryption": "none",
            "fallbacks": []
        }),
        "streamSettings": json.dumps(stream_settings),
        "sniffing": json.dumps({
            "enabled": True,
            "destOverride": ["http", "tls"]
        }),
        "total": 0,
        "up": 0,
        "down": 0,
        "listen_ip": ""
    }

    headers = {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    cookies = {"3x-ui": session_cookie}

    async with httpx.AsyncClient(verify=False, cookies=cookies) as client:
        try:
            res = await client.post(url, headers=headers, data=payload)
            res.raise_for_status()
            data = res.json()
            if data.get("success"):
                print(f" Подключение создано (порт {port}, UUID {uuid}, тип: {network_type})")
            else:
                print(f" Ошибка: {data.get('msg')}")
            return data
        except Exception as e:
            print("Ошибка при создании:", e)
            return None

