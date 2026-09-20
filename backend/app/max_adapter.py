import hashlib
import hmac
import json
import ssl
import time
from urllib.parse import parse_qsl
import httpx


def validate_launch(raw: str, bot_token: str, now: int | None = None) -> dict:
    if not bot_token:
        raise ValueError("MAX не настроен")
    pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)) or keys.count("hash") != 1:
        raise ValueError("Повторяющиеся параметры")
    params = dict(pairs)
    original = params.pop("hash")
    launch = "\n".join(f"{key}={params[key]}" for key in sorted(params))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, launch.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(original, expected):
        raise ValueError("Неверная подпись")
    now = now if now is not None else int(time.time())
    auth_date = int(params.get("auth_date", "0"))
    if not -30 <= now - auth_date <= 600:
        raise ValueError("Срок данных запуска истёк")
    user = json.loads(params.get("user", "{}"))
    if not isinstance(user, dict) or type(user.get("id")) is not int or user["id"] <= 0:
        raise ValueError("Неверный пользователь")
    return {"id": user["id"], "name": str(user.get("first_name", "Пользователь"))[:100], "hash": original}


class MaxClient:
    def __init__(self, config):
        if config.max_api_base.rstrip('/') != 'https://platform-api2.max.ru':
            raise ValueError('Передача токена разрешена только официальному API MAX')
        self.config = config

    async def send(self, chat_id: int, text: str):
        verify = ssl.create_default_context(cafile=self.config.max_ca_bundle or None)
        async with httpx.AsyncClient(base_url=self.config.max_api_base,
                                     headers={"Authorization": self.config.max_bot_token},
                                     timeout=15, verify=verify, follow_redirects=False, trust_env=False) as client:
            response = await client.post("/messages", params={"chat_id": chat_id}, json={"text": text})
            response.raise_for_status()


def prepare_event(payload: dict, app_url: str) -> tuple[str, dict]:
    kind = payload.get("update_type")
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    key = hashlib.sha256(canonical.encode()).hexdigest()
    chat_id = payload.get("chat_id")
    if kind == "message_created":
        message = payload.get("message", {})
        chat_id = message.get("recipient", {}).get("chat_id")
        text = message.get("body", {}).get("text", "").strip().lower()
        if text not in ("/start", "/help", "поддержка"):
            return key, {}
        mid = message.get("body", {}).get("mid")
        if mid:
            key = hashlib.sha256(f"message:{mid}".encode()).hexdigest()
    elif kind != "bot_started":
        return key, {}
    if type(chat_id) is not int or not app_url:
        return key, {}
    return key, {"chat_id": chat_id,
                 "text": "Опора АПК — подбор поддержки и план подготовки. Откройте мини-приложение: " + app_url}
