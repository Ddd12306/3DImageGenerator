import uuid
from typing import Any

from database import get_db, json_dumps, utc_now
from presets import build_prompt, get_preset
from providers.current_provider import CurrentProvider
from services.storage import save_base64_output, save_remote_output, save_upload


class ImageGenerationService:
    def __init__(self) -> None:
        self.provider = CurrentProvider()

    async def generate_text(self, user: dict[str, Any], preset_id: str, prompt: str, fields: dict[str, Any]) -> dict:
        get_preset(preset_id)
        system_prompt, final_prompt = build_prompt(preset_id, prompt, fields, "text")
        task_id = self._create_task(user["id"], preset_id, "text", final_prompt, fields)
        try:
            result = await self.provider.generate_from_text(system_prompt, final_prompt, {})
            return await self._complete_task(user["id"], task_id, preset_id, final_prompt, result)
        except Exception as exc:
            self._fail_task(task_id, exc)
            raise

    async def generate_image(
        self,
        user: dict[str, Any],
        preset_id: str,
        prompt: str,
        fields: dict[str, Any],
        image_bytes: bytes,
        content_type: str,
        filename: str | None,
    ) -> dict:
        get_preset(preset_id)
        system_prompt, final_prompt = build_prompt(preset_id, prompt, fields, "image")
        upload_path = save_upload(user["id"], image_bytes, filename, content_type)
        self._record_upload(user["id"], filename, upload_path, content_type, len(image_bytes))
        task_id = self._create_task(user["id"], preset_id, "image", final_prompt, fields)
        try:
            result = await self.provider.generate_from_image(image_bytes, content_type, system_prompt, final_prompt, {})
            return await self._complete_task(user["id"], task_id, preset_id, final_prompt, result)
        except Exception as exc:
            self._fail_task(task_id, exc)
            raise

    def _create_task(self, user_id: int, preset_id: str, input_type: str, prompt: str, fields: dict[str, Any]) -> str:
        task_id = uuid.uuid4().hex
        now = utc_now()
        with get_db() as db:
            db.execute(
                """
                INSERT INTO generation_tasks
                    (id, user_id, preset_id, input_type, prompt, fields_json, provider, model, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    user_id,
                    preset_id,
                    input_type,
                    prompt,
                    json_dumps(fields),
                    self.provider.name,
                    self.provider.model,
                    "running",
                    now,
                    now,
                ),
            )
        return task_id

    def _record_upload(self, user_id: int, filename: str | None, local_path: str, mime_type: str, size_bytes: int) -> None:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO uploaded_images (user_id, original_filename, local_path, mime_type, size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, filename, local_path, mime_type, size_bytes, utc_now()),
            )

    async def _complete_task(
        self,
        user_id: int,
        task_id: str,
        preset_id: str,
        prompt: str,
        provider_result: dict[str, Any],
    ) -> dict:
        images: list[dict[str, Any]] = []
        with get_db() as db:
            db.execute(
                """
                UPDATE generation_tasks
                SET status = ?, raw_response = ?, model = ?, updated_at = ?
                WHERE id = ?
                """,
                ("succeeded", json_dumps(provider_result.get("raw", {})), provider_result.get("model", self.provider.model), utc_now(), task_id),
            )

        for source_url in provider_result.get("image_urls", []):
            local_path = None
            mime_type = None
            try:
                local_path, mime_type = await save_remote_output(user_id, source_url)
            except Exception:
                # Keep the source URL if the upstream image cannot be copied locally.
                pass
            image_id = self._record_generated_image(user_id, task_id, source_url, local_path, mime_type)
            images.append(
                {
                    "id": image_id,
                    "url": f"/api/images/{image_id}" if local_path else source_url,
                    "source_url": source_url,
                    "local_path": local_path,
                    "mime_type": mime_type,
                }
            )

        for inline_image in provider_result.get("image_b64s", []):
            local_path = None
            mime_type = None
            try:
                local_path, mime_type = save_base64_output(
                    user_id,
                    inline_image["b64_json"],
                    inline_image.get("mime_type") or "image/png",
                )
            except Exception:
                pass
            if not local_path:
                continue
            image_id = self._record_generated_image(user_id, task_id, None, local_path, mime_type)
            images.append(
                {
                    "id": image_id,
                    "url": f"/api/images/{image_id}",
                    "source_url": None,
                    "local_path": local_path,
                    "mime_type": mime_type,
                }
            )

        return {
            "task_id": task_id,
            "provider": provider_result.get("provider", self.provider.name),
            "model": provider_result.get("model", self.provider.model),
            "preset": preset_id,
            "status": "succeeded",
            "prompt": prompt,
            "content": provider_result.get("content", ""),
            "images": images,
            "usage": provider_result.get("usage", {}),
        }

    def _record_generated_image(
        self,
        user_id: int,
        task_id: str,
        source_url: str | None,
        local_path: str | None,
        mime_type: str | None,
    ) -> int:
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO generated_images (task_id, user_id, source_url, local_path, mime_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task_id, user_id, source_url, local_path, mime_type, utc_now()),
            )
            return int(cursor.lastrowid)

    def _fail_task(self, task_id: str, exc: Exception) -> None:
        with get_db() as db:
            db.execute(
                "UPDATE generation_tasks SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                ("failed", str(exc), utc_now(), task_id),
            )
