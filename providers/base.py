from typing import Protocol


class ImageProvider(Protocol):
    name: str
    model: str

    async def generate_from_text(self, system_prompt: str, prompt: str, options: dict) -> dict:
        ...

    async def generate_from_image(
        self,
        image_bytes: bytes,
        content_type: str,
        system_prompt: str,
        prompt: str,
        options: dict,
    ) -> dict:
        ...
