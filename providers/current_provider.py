import base64
import re
from typing import Any

import httpx

from config import API_BASE_URL, API_KEY, MODEL

IMAGE_URL_RE = re.compile(r"https?://[^\s\"'<>]+?\.(?:png|jpg|jpeg|gif|webp)(?:\?[^\s\"'<>]*)?", re.IGNORECASE)


class CurrentProvider:
    name = "current"
    model = MODEL

    async def generate_from_text(self, system_prompt: str, prompt: str, options: dict) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        return await self._post(payload)

    async def generate_from_image(
        self,
        image_bytes: bytes,
        content_type: str,
        system_prompt: str,
        prompt: str,
        options: dict,
    ) -> dict[str, Any]:
        mime = content_type or "image/png"
        data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        }
        return await self._post(payload)

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not API_KEY:
            raise RuntimeError("API_KEY 未配置")

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            )
            response.raise_for_status()

        data = response.json()
        content = self._extract_content(data)
        image_urls = IMAGE_URL_RE.findall(content)
        image_b64s = self._extract_base64_images(data)
        return {
            "provider": self.name,
            "model": data.get("model", self.model),
            "content": content,
            "image_urls": image_urls,
            "image_b64s": image_b64s,
            "usage": data.get("usage", {}),
            "raw": self._redact_base64(data),
        }

    def _extract_content(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            return str(content)
        image_count = len(self._extract_base64_images(data))
        if image_count:
            return f"上游返回了 {image_count} 张 base64 图片，已保存为本地图片。"
        return str(data)

    def _extract_base64_images(self, data: dict[str, Any]) -> list[dict[str, str]]:
        images: list[dict[str, str]] = []
        for item in data.get("data") or []:
            if not isinstance(item, dict):
                continue
            b64_json = item.get("b64_json")
            if isinstance(b64_json, str) and b64_json:
                images.append({"b64_json": b64_json, "mime_type": item.get("mime_type") or "image/png"})
        return images

    def _redact_base64(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[base64 image omitted]" if key == "b64_json" and isinstance(item, str) else self._redact_base64(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._redact_base64(item) for item in value]
        return value
