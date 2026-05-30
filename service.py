import base64
import httpx
from config import API_KEY, API_BASE_URL, MODEL

SUBJECT_PROMPTS = {
    "pet": {
        "label": "宠物",
        "description_label": "宠物描述",
        "system": """你是一个专业的宠物Q版3D风格化图像生成助手。
请将用户提供的宠物照片转换为Q版3D卡通风格的图像。要求：
- 保留宠物的品种特征、毛色、花纹等关键识别特征
- 转换为Q版比例（大头、圆润身体、短小四肢）
- 3D渲染风格，柔和的光影效果
- 可爱、萌系的表情
- 干净的纯色背景（浅蓝或浅粉）
- 高质量、细节丰富的渲染效果""",
        "image": "请将这张宠物照片转换为Q版3D卡通风格图像，保留宠物的所有外观特征（品种、毛色、花纹、眼睛颜色等），生成一张可爱的Q版3D渲染图。",
        "text": "根据以下宠物描述，生成一张Q版3D卡通风格的宠物图像。",
        "requirements": "要求：Q版比例（大头圆身短肢）、3D渲染、可爱萌系表情、纯色背景。",
    },
    "person": {
        "label": "人物",
        "description_label": "人物描述",
        "system": """你是一个专业的专属人物Q版3D形象生成助手。
请根据用户提供的人物照片，提取这个人的专属识别特征并转换为Q版3D卡通形象。要求：
- 重点保留照片中的个人专属特征：发型、发色、脸型轮廓、眉眼形状、鼻嘴比例、脸部气质、肤色、痣/酒窝/胡须/眼镜等可见特征
- 保留照片中的表情和神态，例如微笑、严肃、眨眼、歪头、活泼、温柔等，不要改成无关表情
- 保留服装、配饰、姿态和照片里能识别身份的细节，让结果看起来像“这个人的Q版形象”，而不是通用娃娃模板
- 转换为Q版比例（大头、圆脸、短小身体、柔和四肢），但不能丢失人物辨识度
- 3D渲染风格，像高质量潮玩手办或动画角色
- 表情可爱自然，避免夸张变形、恐怖效果或过度美化导致不像本人
- 干净的纯色或简洁渐变背景
- 高质量、细节丰富、适合作为专属头像、IP形象或3D建模参考""",
        "image": "请根据这张人物照片生成专属Q版3D卡通形象。必须保留照片中这个人的发型、脸型、眉眼鼻嘴特征、肤色、表情神态、服装和配饰等专属识别点，让结果明显像本人，而不是通用Q版人物。生成一张可爱自然、高质量的Q版3D渲染图。",
        "text": "根据以下人物描述，生成一张专属Q版3D卡通风格的人物形象。",
        "requirements": "要求：Q版比例（大头圆脸短身）、3D渲染、可爱自然表情、保留个人专属特征、表情神态、服装配饰和姿态，避免通用模板脸，纯色或简洁背景。",
    },
}


def _get_subject_prompt(subject_type: str) -> dict:
    return SUBJECT_PROMPTS.get(subject_type, SUBJECT_PROMPTS["pet"])


async def generate_qversion_from_image(image_bytes: bytes, content_type: str, subject_type: str = "pet") -> dict:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime = content_type if content_type else "image/png"
    data_url = f"data:{mime};base64,{b64}"
    subject_prompt = _get_subject_prompt(subject_type)

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": subject_prompt["system"]},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": subject_prompt["image"]},
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


async def generate_qversion_from_text(description: str, subject_type: str = "pet") -> dict:
    subject_prompt = _get_subject_prompt(subject_type)
    prompt = (
        f"{subject_prompt['text']}\n"
        f"{subject_prompt['requirements']}\n\n"
        f"{subject_prompt['description_label']}：{description}"
    )

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": subject_prompt["system"]},
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
