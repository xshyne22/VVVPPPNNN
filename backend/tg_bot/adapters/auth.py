from settings import domain_xui, port_xui, url_xui, username_xui, password_xui
import httpx

async def login_to_xui() -> str:
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(
                url=f"https://{domain_xui}:{port_xui}/{url_xui}/login",
                json={"username": username_xui, "password": password_xui},
            )
            response.raise_for_status()
            session_cookie = response.cookies.get("3x-ui")
            if session_cookie:
                return session_cookie
            else:
                return None

        except httpx.HTTPStatusError as e:
            print(f"Error HTTP: {e.response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        return None
