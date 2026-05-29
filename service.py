import base64
import httpx
from config import API_KEY, API_BASE_URL, MODEL

QVERSION_SYSTEM_PROMPT = """你是一个专业的宠物Q版3D风格化图像生成助手。
请将用户提供的宠物照片转换为Q版3D卡通风格的图像。要求：
- 保留宠物的品种特征、毛色、花纹等关键识别特征
- 转换为Q版比例（大头、圆润身体、短小四肢）
- 3D渲染风格，柔和的光影效果
- 可爱、萌系的表情
- 干净的纯色背景（浅蓝或浅粉）
- 高质量、细节丰富的渲染效果"""

QVERSION_USER_PROMPT = "请将这张宠物照片转换为Q版3D卡通风格图像，保留宠物的所有外观特征（品种、毛色、花纹、眼睛颜色等），生成一张可爱的Q版3D渲染图。"


async def generate_qversion_from_image(image_bytes: bytes, content_type: str) -> dict:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime = content_type if content_type else "image/png"
    data_url = f"data:{mime};base64,{b64}"

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": QVERSION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": QVERSION_USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{API_BASE_URL}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        )
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"content": content, "usage": usage, "model": data.get("model", MODEL)}


async def generate_qversion_from_text(description: str) -> dict:
    prompt = (
        f"根据以下宠物描述，生成一张Q版3D卡通风格的宠物图像。\n"
        f"要求：Q版比例（大头圆身短肢）、3D渲染、可爱萌系表情、纯色背景。\n\n"
        f"宠物描述：{description}"
    )

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": QVERSION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{API_BASE_URL}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        )
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"content": content, "usage": usage, "model": data.get("model", MODEL)}
