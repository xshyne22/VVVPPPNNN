import subprocess
import uuid
import random


async def create_vpn_identity_xray_cli():
    user_uuid = str(uuid.uuid4())
    short_id = ''.join(random.choices('0123456789abcdef', k=8))

    try:
        result = subprocess.run(["xray", "x25519"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()

        private_key = None
        public_key = None

        for line in lines:
            if "Private key" in line:
                private_key = line.split(":")[1].strip()
            elif "Public key" in line:
                public_key = line.split(":")[1].strip()

        if not private_key or not public_key:
            raise ValueError("Не удалось найти ключи в выводе Xray")

        return {
            "uuid": user_uuid,
            "short_id": short_id,
            "private_key_base64": private_key,
            "public_key_base64": public_key
        }

    except subprocess.CalledProcessError as e:
        print("Ошибка запуска xray:", e)
        return None
