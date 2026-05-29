from pathlib import Path
from typing import List
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from service import generate_qversion_from_image, generate_qversion_from_text
from service_3d import submit_3d_job, submit_3d_job_base64, submit_3d_job_multi, query_3d_job
from config import API_KEY

app = FastAPI(title="Pet Q-Version 3D Generator")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


@app.middleware("http")
async def no_cache_index_html(request, call_next):
    response = await call_next(request)
    if request.url.path in ("/", "/static/index.html"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


def _upstream_error_detail(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    text = response.text.strip()
    if len(text) > 500:
        text = text[:500] + "..."
    return f"上游图像服务返回 {response.status_code}: {text or response.reason_phrase}"


@app.exception_handler(httpx.HTTPStatusError)
async def http_status_error_handler(_, exc: httpx.HTTPStatusError):
    return JSONResponse(status_code=502, content={"detail": _upstream_error_detail(exc)})


@app.exception_handler(httpx.RequestError)
async def http_request_error_handler(_, exc: httpx.RequestError):
    return JSONResponse(status_code=502, content={"detail": f"无法连接上游图像服务: {exc}"})


@app.exception_handler(KeyError)
async def key_error_handler(_, exc: KeyError):
    return JSONResponse(status_code=502, content={"detail": f"上游图像服务响应格式异常，缺少字段: {exc}"})


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/static/index.html")


@app.on_event("startup")
async def startup():
    if not API_KEY:
        raise RuntimeError("API_KEY not set. Copy .env.example to .env and fill in your key.")


@app.post("/generate/image")
async def generate_from_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size must be under 20MB")

    result = await generate_qversion_from_image(image_bytes, file.content_type)
    return JSONResponse(content=result)


@app.post("/generate/text")
async def generate_from_text(description: str = Form(...)):
    if not description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    result = await generate_qversion_from_text(description.strip())
    return JSONResponse(content=result)


@app.post("/generate3d/submit")
async def submit_3d(image_url: str = Form(...), mode: str = Form("pro")):
    if mode not in ("pro", "rapid"):
        raise HTTPException(status_code=400, detail="mode must be 'pro' or 'rapid'")
    if not image_url.startswith("http"):
        raise HTTPException(status_code=400, detail="image_url must be a valid URL")

    result = await submit_3d_job(image_url, mode)
    return JSONResponse(content=result)


@app.get("/generate3d/query")
async def query_3d(job_id: str = Query(...), mode: str = Query("pro")):
    result = await query_3d_job(job_id, mode)
    return JSONResponse(content=result)


@app.post("/generate3d/upload")
async def generate_3d_from_upload(file: UploadFile = File(...), mode: str = Form("pro")):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")
    if mode not in ("pro", "rapid"):
        raise HTTPException(status_code=400, detail="mode must be 'pro' or 'rapid'")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size must be under 20MB")

    result = await submit_3d_job_base64(image_bytes, mode)
    return JSONResponse(content=result)


@app.post("/generate3d/upload-multi")
async def generate_3d_from_multi_upload(files: List[UploadFile] = File(...), mode: str = Form("pro")):
    if mode not in ("pro", "rapid"):
        raise HTTPException(status_code=400, detail="mode must be 'pro' or 'rapid'")
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 images allowed")

    images_bytes = []
    for f in files:
        if not f.content_type or not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File {f.filename} is not an image")
        data = await f.read()
        if len(data) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File {f.filename} exceeds 20MB")
        images_bytes.append(data)

    result = await submit_3d_job_multi(images_bytes, mode)
    return JSONResponse(content=result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
