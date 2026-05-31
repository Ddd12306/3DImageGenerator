import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from auth import (
    authenticate_user,
    clear_session_cookie,
    create_session,
    create_user,
    delete_session,
    get_current_user,
    set_session_cookie,
)
from config import SESSION_COOKIE_NAME
from database import get_db, init_db, json_loads
from presets import get_preset, list_presets
from services.image_service import ImageGenerationService
from services.storage import resolve_data_path

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
MAX_IMAGE_BYTES = 20 * 1024 * 1024

app = FastAPI(title="2D Image Generation Platform")
image_service = ImageGenerationService()

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


class AuthRequest(BaseModel):
    username: str
    password: str


class GenerateTextRequest(BaseModel):
    preset_id: str = "free_generation"
    prompt: str = ""
    fields: dict[str, Any] = Field(default_factory=dict)


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.exception_handler(httpx.HTTPStatusError)
async def http_status_error_handler(_, exc: httpx.HTTPStatusError):
    response = exc.response
    text = response.text.strip()
    if len(text) > 500:
        text = text[:500] + "..."
    return JSONResponse(status_code=502, content={"detail": f"上游图像服务返回 {response.status_code}: {text or response.reason_phrase}"})


@app.exception_handler(httpx.RequestError)
async def http_request_error_handler(_, exc: httpx.RequestError):
    return JSONResponse(status_code=502, content={"detail": f"无法连接上游图像服务: {exc}"})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/presets")
async def presets():
    return {"presets": list_presets()}


@app.post("/api/auth/register")
async def register(payload: AuthRequest):
    user = create_user(payload.username, payload.password)
    token = create_session(user["id"])
    response = JSONResponse({"user": user})
    set_session_cookie(response, token)
    return response


@app.post("/api/auth/login")
async def login(payload: AuthRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_session(user["id"])
    response = JSONResponse({"user": user})
    set_session_cookie(response, token)
    return response


@app.post("/api/auth/logout")
async def logout(session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME)):
    response = JSONResponse({"ok": True})
    delete_session(session_token)
    clear_session_cookie(response)
    return response


@app.get("/api/me")
async def me(user: dict[str, Any] = Depends(get_current_user)):
    return {"user": {"id": user["id"], "username": user["username"]}}


@app.post("/api/generate/text")
async def generate_text(payload: GenerateTextRequest, user: dict[str, Any] = Depends(get_current_user)):
    _validate_preset(payload.preset_id, "text")
    result = await image_service.generate_text(user, payload.preset_id, payload.prompt, payload.fields)
    return JSONResponse(result)


@app.post("/api/generate/persona")
async def generate_persona(payload: GenerateTextRequest, user: dict[str, Any] = Depends(get_current_user)):
    preset_id = payload.preset_id or "persona_photo"
    _validate_preset(preset_id, "text")
    result = await image_service.generate_text(user, preset_id, payload.prompt, payload.fields)
    return JSONResponse(result)


@app.post("/api/generate/image")
async def generate_image(
    file: UploadFile = File(...),
    preset_id: str = Form("free_generation"),
    prompt: str = Form(""),
    fields_json: str = Form("{}"),
    user: dict[str, Any] = Depends(get_current_user),
):
    _validate_preset(preset_id, "image")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持上传图片文件")

    try:
        fields = json.loads(fields_json or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="fields_json 不是合法 JSON") from exc

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="图片大小不能超过 20MB")

    result = await image_service.generate_image(
        user=user,
        preset_id=preset_id,
        prompt=prompt,
        fields=fields,
        image_bytes=image_bytes,
        content_type=file.content_type,
        filename=file.filename,
    )
    return JSONResponse(result)


@app.get("/api/tasks")
async def tasks(user: dict[str, Any] = Depends(get_current_user)):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT *
            FROM generation_tasks
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 100
            """,
            (user["id"],),
        ).fetchall()
        images = db.execute(
            """
            SELECT *
            FROM generated_images
            WHERE user_id = ?
            ORDER BY created_at ASC
            """,
            (user["id"],),
        ).fetchall()

    images_by_task: dict[str, list[dict[str, Any]]] = {}
    for image in images:
        item = _image_response(image)
        images_by_task.setdefault(image["task_id"], []).append(item)

    return {
        "tasks": [
            {
                "id": row["id"],
                "preset_id": row["preset_id"],
                "input_type": row["input_type"],
                "prompt": row["prompt"],
                "fields": json_loads(row["fields_json"], {}),
                "provider": row["provider"],
                "model": row["model"],
                "status": row["status"],
                "error_message": row["error_message"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "images": images_by_task.get(row["id"], []),
            }
            for row in rows
        ]
    }


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, user: dict[str, Any] = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute(
            "SELECT id, status FROM generation_tasks WHERE id = ? AND user_id = ?",
            (task_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        if row["status"] != "failed":
            raise HTTPException(status_code=400, detail="只能删除失败记录")

        images = db.execute(
            "SELECT local_path FROM generated_images WHERE task_id = ? AND user_id = ?",
            (task_id, user["id"]),
        ).fetchall()

        db.execute("DELETE FROM generation_tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))

    for image in images:
        if not image["local_path"]:
            continue
        try:
            path = resolve_data_path(image["local_path"])
            if path.exists():
                path.unlink()
        except OSError:
            pass

    return {"ok": True}


@app.get("/api/tasks/{task_id}")
async def task_detail(task_id: str, user: dict[str, Any] = Depends(get_current_user)):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM generation_tasks WHERE id = ? AND user_id = ?",
            (task_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        images = db.execute(
            "SELECT * FROM generated_images WHERE task_id = ? AND user_id = ? ORDER BY created_at ASC",
            (task_id, user["id"]),
        ).fetchall()

    return {
        "task": {
            "id": row["id"],
            "preset_id": row["preset_id"],
            "input_type": row["input_type"],
            "prompt": row["prompt"],
            "fields": json_loads(row["fields_json"], {}),
            "provider": row["provider"],
            "model": row["model"],
            "status": row["status"],
            "raw_response": json_loads(row["raw_response"], {}),
            "error_message": row["error_message"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "images": [_image_response(image) for image in images],
        }
    }


@app.get("/api/images/{image_id}")
async def image_file(image_id: int, user: dict[str, Any] = Depends(get_current_user)):
    with get_db() as db:
        image = db.execute(
            "SELECT * FROM generated_images WHERE id = ? AND user_id = ?",
            (image_id, user["id"]),
        ).fetchone()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    if image["local_path"]:
        path = resolve_data_path(image["local_path"])
        if not path.exists():
            raise HTTPException(status_code=404, detail="图片文件不存在")
        return FileResponse(path, media_type=image["mime_type"] or "image/png")

    if image["source_url"]:
        return RedirectResponse(image["source_url"])

    raise HTTPException(status_code=404, detail="图片不可用")


@app.post("/generate/text")
async def legacy_generate_text(description: str = Form(...), subject_type: str = Form("person"), user: dict[str, Any] = Depends(get_current_user)):
    fields = {"subject_type": subject_type}
    result = await image_service.generate_text(user, "q_avatar", description, fields)
    return JSONResponse(result)


@app.post("/generate/image")
async def legacy_generate_image(
    file: UploadFile = File(...),
    subject_type: str = Form("person"),
    user: dict[str, Any] = Depends(get_current_user),
):
    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="图片大小不能超过 20MB")
    result = await image_service.generate_image(
        user=user,
        preset_id="q_avatar",
        prompt="",
        fields={"subject_type": subject_type},
        image_bytes=image_bytes,
        content_type=file.content_type or "image/png",
        filename=file.filename,
    )
    return JSONResponse(result)


def _validate_preset(preset_id: str, mode: str) -> None:
    try:
        preset = get_preset(preset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="预设不存在") from exc
    if mode not in preset.get("input_modes", []):
        raise HTTPException(status_code=400, detail=f"预设不支持 {mode} 输入")


def _image_response(image: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": image["id"],
        "url": f"/api/images/{image['id']}" if image["local_path"] else image["source_url"],
        "source_url": image["source_url"],
        "local_path": image["local_path"],
        "mime_type": image["mime_type"],
        "created_at": image["created_at"],
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str = ""):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="接口不存在")

    if FRONTEND_DIST.exists():
        requested = (FRONTEND_DIST / full_path).resolve()
        if full_path and requested.exists() and str(requested).startswith(str(FRONTEND_DIST.resolve())):
            return FileResponse(requested)
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(index)

    return JSONResponse(
        {
            "message": "前端尚未构建。请进入 frontend 目录运行 npm install 和 npm run build，或使用 npm run dev 启动前端开发服务器。",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
