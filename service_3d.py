import json
import base64
import asyncio
import io
from PIL import Image
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ai3d.v20250513.ai3d_client import Ai3dClient
from tencentcloud.ai3d.v20250513 import models
from config import TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_REGION


def _get_client():
    cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
    http_profile = HttpProfile()
    http_profile.endpoint = "ai3d.tencentcloudapi.com"
    http_profile.reqTimeout = 120
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    return Ai3dClient(cred, TENCENT_REGION, client_profile)


async def submit_3d_job(image_url: str, mode: str = "pro") -> dict:
    client = _get_client()

    if mode == "rapid":
        req = models.SubmitHunyuanTo3DRapidJobRequest()
        params = {"ImageUrl": image_url}
        req.from_json_string(json.dumps(params))
        resp = await asyncio.to_thread(client.SubmitHunyuanTo3DRapidJob, req)
    else:
        req = models.SubmitHunyuanTo3DProJobRequest()
        params = {"ImageUrl": image_url}
        req.from_json_string(json.dumps(params))
        resp = await asyncio.to_thread(client.SubmitHunyuanTo3DProJob, req)

    data = json.loads(resp.to_json_string())
    return {"job_id": data.get("JobId"), "request_id": data.get("RequestId")}


async def submit_3d_job_base64(image_bytes: bytes, mode: str = "pro") -> dict:
    client = _get_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    if mode == "rapid":
        req = models.SubmitHunyuanTo3DRapidJobRequest()
        params = {"ImageBase64": b64}
        req.from_json_string(json.dumps(params))
        resp = await asyncio.to_thread(client.SubmitHunyuanTo3DRapidJob, req)
    else:
        req = models.SubmitHunyuanTo3DProJobRequest()
        params = {"ImageBase64": b64}
        req.from_json_string(json.dumps(params))
        resp = await asyncio.to_thread(client.SubmitHunyuanTo3DProJob, req)

    data = json.loads(resp.to_json_string())
    return {"job_id": data.get("JobId"), "request_id": data.get("RequestId")}


def _compress_image(image_bytes: bytes, max_size: int = 1024, quality: int = 85) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


async def submit_3d_job_multi(images_bytes_list: list[bytes], mode: str = "pro") -> dict:
    client = _get_client()
    compressed = [_compress_image(img) for img in images_bytes_list]

    if mode == "rapid":
        b64 = base64.b64encode(compressed[0]).decode("utf-8")
        req = models.SubmitHunyuanTo3DRapidJobRequest()
        params = {"ImageBase64": b64}
        req.from_json_string(json.dumps(params))
        resp = await asyncio.to_thread(client.SubmitHunyuanTo3DRapidJob, req)
    else:
        view_types = ["back", "left", "right"]
        multi_views = []
        extra = compressed[1:4]
        for i, img in enumerate(extra):
            b64 = base64.b64encode(img).decode("utf-8")
            multi_views.append({
                "ViewType": view_types[i],
                "ViewImageBase64": b64,
            })
        req = models.SubmitHunyuanTo3DProJobRequest()
        params = {"ImageBase64": base64.b64encode(compressed[0]).decode("utf-8")}
        if multi_views:
            params["MultiViewImages"] = multi_views
        req.from_json_string(json.dumps(params))
        resp = await asyncio.to_thread(client.SubmitHunyuanTo3DProJob, req)

    data = json.loads(resp.to_json_string())
    return {"job_id": data.get("JobId"), "request_id": data.get("RequestId")}


async def query_3d_job(job_id: str, mode: str = "pro") -> dict:
    client = _get_client()

    if mode == "rapid":
        req = models.QueryHunyuanTo3DRapidJobRequest()
        req.from_json_string(json.dumps({"JobId": job_id}))
        resp = await asyncio.to_thread(client.QueryHunyuanTo3DRapidJob, req)
    else:
        req = models.QueryHunyuanTo3DProJobRequest()
        req.from_json_string(json.dumps({"JobId": job_id}))
        resp = await asyncio.to_thread(client.QueryHunyuanTo3DProJob, req)

    data = json.loads(resp.to_json_string())
    result_files = data.get("ResultFile3Ds") or []
    model_urls = {}
    preview_url = ""
    for item in result_files:
        fmt = item.get("Type", "unknown")
        model_urls[fmt] = item.get("Url", "")
        if item.get("PreviewImageUrl"):
            preview_url = item["PreviewImageUrl"]

    return {
        "status": data.get("Status"),
        "model_urls": model_urls,
        "preview_url": preview_url,
        "progress": data.get("Progress", 0),
        "request_id": data.get("RequestId"),
    }
