from typing import Any


PRESETS: list[dict[str, Any]] = [
    {
        "id": "shadow_artist",
        "name": "影子造梦师",
        "description": "把照片里的普通影子改造成有故事感的创意影子，尽量保留原始街拍现场。",
        "input_modes": ["text", "image"],
        "fields": [
            {
                "id": "shadow_concept",
                "label": "影子设定",
                "type": "select",
                "default": "street_creature",
                "options": [
                    {"label": "街头小怪影", "value": "street_creature"},
                    {"label": "天使翅膀", "value": "angel_wings"},
                    {"label": "超级英雄披风", "value": "hero_cape"},
                    {"label": "赛博装甲轮廓", "value": "cyber_armor"},
                    {"label": "涂鸦纹身图腾", "value": "graffiti_totem"},
                ],
            },
            {
                "id": "intensity",
                "label": "改造强度",
                "type": "select",
                "default": "balanced",
                "options": [
                    {"label": "轻微点睛", "value": "subtle"},
                    {"label": "自然明显", "value": "balanced"},
                    {"label": "强烈戏剧感", "value": "bold"},
                ],
            },
            {
                "id": "realism",
                "label": "融合方式",
                "type": "select",
                "default": "photoreal",
                "options": [
                    {"label": "真实街拍", "value": "photoreal"},
                    {"label": "手绘叠画", "value": "drawn_overlay"},
                    {"label": "电影海报感", "value": "cinematic"},
                ],
            },
        ],
        "system_prompt": "你是一个影子创意改造师，擅长在不破坏原照片真实感的前提下，把画面中的影子变成有趣、有故事、有视觉记忆点的角色或图案。你必须优先保留原图的街道路面、鞋子、人物可见部分、镜头角度、阳光方向和照片质感，只改造影子区域及其自然边缘。不要重绘整张照片，不要改变主体身份，不要加入与光照方向冲突的元素。",
        "text_prompt_template": "请生成一张真实街拍感图片：一个人站在阳光下，地面上有影子。把影子设计成{shadow_concept}，改造强度为{intensity}，融合方式为{realism}。影子要像自然投射在地面上，同时带有创意细节和故事感。用户补充要求：{prompt}",
        "image_prompt_template": "请基于参考图进行局部创意改造。识别画面中的人物影子，把影子改造成{shadow_concept}，改造强度为{intensity}，融合方式为{realism}。必须保留原照片的构图、路面纹理、黄色道路标线、鞋子、可见衣物、阳光方向和街拍质感；主要只在影子范围内添加创意形状、线条或轮廓，让它看起来像真实地投射在地面上。不要改变脚、鞋、路面结构和整体拍摄角度。用户补充要求：{prompt}",
    },
    {
        "id": "q_avatar",
        "name": "Q 版形象大师",
        "description": "根据人物、宠物或角色描述生成可爱、辨识度高的 Q 版 2D 形象。",
        "input_modes": ["text", "image"],
        "fields": [
            {
                "id": "subject_type",
                "label": "对象类型",
                "type": "select",
                "default": "person",
                "options": [
                    {"label": "人物", "value": "person"},
                    {"label": "宠物", "value": "pet"},
                    {"label": "虚拟角色", "value": "character"},
                ],
            },
            {
                "id": "style",
                "label": "风格",
                "type": "select",
                "default": "soft_2d",
                "options": [
                    {"label": "柔和 2D 卡通", "value": "soft_2d"},
                    {"label": "表情包头像", "value": "sticker"},
                    {"label": "潮玩感头像", "value": "toy_avatar"},
                ],
            },
        ],
        "system_prompt": "你是专业的 2D 头像和角色形象生成助手，擅长保留主体特征并转化为可爱、自然、有辨识度的 Q 版形象。",
        "text_prompt_template": "请根据用户描述生成一张 Q 版 2D 形象图。需要保留对象的核心特征、表情气质、服装或配饰，避免变成通用模板。风格为：{style}。用户描述：{prompt}",
        "image_prompt_template": "请根据参考图生成一张 Q 版 2D 形象图。需要保留参考图中的核心识别特征、表情气质、服装或配饰，避免过度美化或变成通用模板。风格为：{style}。用户补充要求：{prompt}",
    },
    {
        "id": "makeup_master",
        "name": "妆造大师",
        "description": "根据自拍或描述设计适合个人气质的妆容、发型、服装和整体造型。",
        "input_modes": ["text", "image"],
        "fields": [
            {
                "id": "makeup_style",
                "label": "妆容风格",
                "type": "select",
                "default": "daily_clean",
                "options": [
                    {"label": "日常清透", "value": "daily_clean"},
                    {"label": "通勤高级", "value": "office"},
                    {"label": "约会甜美", "value": "date_soft"},
                    {"label": "晚宴精致", "value": "evening"},
                ],
            },
            {
                "id": "intensity",
                "label": "妆造强度",
                "type": "select",
                "default": "medium",
                "options": [
                    {"label": "轻度", "value": "light"},
                    {"label": "中等", "value": "medium"},
                    {"label": "明显改造", "value": "strong"},
                ],
            },
            {"id": "scene", "label": "使用场景", "type": "text", "default": "日常出门、拍照都适合"},
        ],
        "system_prompt": "你是专业的妆造设计和人像生图助手。目标是基于用户特征设计适合的妆容、发型、服装和整体造型，不改变身份特征，不制造夸张失真效果。",
        "text_prompt_template": "请根据描述生成一张妆造效果图。妆容风格：{makeup_style}。妆造强度：{intensity}。使用场景：{scene}。要求自然、精致、适合本人气质，包含妆容、发型、服装和光线氛围。用户描述：{prompt}",
        "image_prompt_template": "请根据参考图为图中人物设计适合的妆造效果图。妆容风格：{makeup_style}。妆造强度：{intensity}。使用场景：{scene}。要求保留本人五官和脸型识别度，优化妆容、发型、服装和整体气质，不改变身份，不夸张磨皮。用户补充要求：{prompt}",
    },
    {
        "id": "persona_photo",
        "name": "人设写真",
        "description": "根据人设、气质、服装和场景生成写真感人物图。",
        "input_modes": ["text", "image"],
        "fields": [
            {"id": "persona_name", "label": "人设名称", "type": "text", "default": "都市灵感策展人"},
            {"id": "temperament", "label": "气质", "type": "text", "default": "冷静、聪明、亲和"},
            {"id": "outfit", "label": "服装", "type": "text", "default": "简洁有设计感的通勤穿搭"},
            {"id": "scene", "label": "场景", "type": "text", "default": "自然光室内写真"},
        ],
        "system_prompt": "你是专业的人设写真生图助手，擅长将人物设定转化为可信、精致、有故事感的 2D 图像。",
        "text_prompt_template": "请生成一张人设写真图。人设名称：{persona_name}。气质：{temperament}。服装：{outfit}。场景：{scene}。用户描述：{prompt}",
        "image_prompt_template": "请基于参考图生成一张人设写真图，保留人物核心识别度。人设名称：{persona_name}。气质：{temperament}。服装：{outfit}。场景：{scene}。用户补充要求：{prompt}",
    },
    {
        "id": "profile_avatar",
        "name": "头像生成",
        "description": "生成适合社交媒体、职场资料或个人品牌的头像。",
        "input_modes": ["text", "image"],
        "fields": [
            {
                "id": "avatar_type",
                "label": "头像类型",
                "type": "select",
                "default": "social",
                "options": [
                    {"label": "社交头像", "value": "social"},
                    {"label": "职场头像", "value": "business"},
                    {"label": "创作者头像", "value": "creator"},
                    {"label": "二次元头像", "value": "anime"},
                ],
            }
        ],
        "system_prompt": "你是专业头像生成助手，擅长根据用途生成清晰、好看、有记忆点的头像图。",
        "text_prompt_template": "请生成一张头像图。头像类型：{avatar_type}。要求主体清晰、构图干净、适合作为头像。用户描述：{prompt}",
        "image_prompt_template": "请根据参考图生成一张头像图。头像类型：{avatar_type}。要求保留人物识别度，主体清晰，构图干净。用户补充要求：{prompt}",
    },
    {
        "id": "free_generation",
        "name": "自由生图",
        "description": "自由输入提示词，生成任意 2D 图片。",
        "input_modes": ["text", "image"],
        "fields": [
            {"id": "style", "label": "画面风格", "type": "text", "default": "高质量、细节丰富、构图完整"},
        ],
        "system_prompt": "你是专业的 2D 图片生成助手，擅长将用户提示词转化为清晰、完整、高质量的图像。",
        "text_prompt_template": "请生成一张 2D 图片。画面风格：{style}。用户提示词：{prompt}",
        "image_prompt_template": "请根据参考图生成一张 2D 图片。画面风格：{style}。用户补充要求：{prompt}",
    },
]


def list_presets() -> list[dict[str, Any]]:
    return PRESETS


def get_preset(preset_id: str) -> dict[str, Any]:
    for preset in PRESETS:
        if preset["id"] == preset_id:
            return preset
    raise KeyError(preset_id)


def default_fields(preset: dict[str, Any]) -> dict[str, str]:
    return {field["id"]: field.get("default", "") for field in preset.get("fields", [])}


def build_prompt(preset_id: str, prompt: str, fields: dict[str, Any] | None, mode: str) -> tuple[str, str]:
    preset = get_preset(preset_id)
    values = default_fields(preset)
    values.update(fields or {})
    values["prompt"] = prompt.strip() or "请根据当前预设生成一张完整、自然、高质量的图片。"
    template_key = "image_prompt_template" if mode == "image" else "text_prompt_template"
    return preset["system_prompt"], preset[template_key].format(**values)
