# 2D 生图聚合平台改造计划

## 实施进度

更新时间：2026-05-31

- [x] 移除 3D 后端路由和 3D 服务文件。
- [x] 删除旧的 3D 静态页面入口。
- [x] 增加 SQLite 数据库初始化。
- [x] 增加本地图片存储目录规划和代码。
- [x] 增加用户名密码注册、登录、退出和当前用户接口。
- [x] 增加生图预设系统。
- [x] 增加当前上游厂商 provider 适配层。
- [x] 增加统一生图服务和规范化返回结构。
- [x] 增加任务历史和图片访问接口。
- [x] 前端升级为 Vue 3 + Vite + TypeScript。
- [x] 前端实现生图工作台、预设选择、上传参考图、结果展示和历史记录。
- [x] 完成前端构建验证。
- [x] 完成后端基础接口验证。
- [ ] 后续接入豆包 Seedream、阿里通义万相、腾讯混元等模型供应商。
- [ ] 后续接入对象存储、正式用户体系、额度和计费。

## 1. 改造目标

将当前的 Q 版 3D 图片生成器，改造成一个纯 2D 生图聚合平台。

第一版暂时继续使用当前 `.env` 中配置的上游接口：

- `API_BASE_URL`
- `API_KEY`
- `MODEL`

豆包 Seedream、阿里通义万相、腾讯混元、智谱、MiniMax 等模型供应商的接入先放到后续待办，不在第一版实现。

## 2. 产品范围

平台不再只支持 Q 版形象生成，而是扩展成多个 2D 生图场景。

第一版内置场景：

- Q 版形象大师
- 妆造大师
- 人设写真
- 头像生成
- 自由生图

当前已有的 Q 版生图能力保留，但改成平台中的一个内置预设。

3D 生成能力全部移除。

## 3. 当前项目情况

当前项目结构比较简单：

- `main.py`：FastAPI 应用和路由
- `service.py`：当前上游生图逻辑和 Q 版提示词
- `service_3d.py`：腾讯混元 3D 生成逻辑
- `static/index.html`：单页前端
- `config.py`：环境变量配置

当前需要处理的问题：

- 3D 路由和前端 UI 混在主应用里。
- 提示词逻辑写死在 Q 版宠物/人物场景里。
- 前端通过解析文本中的图片 URL 来展示结果，结构不稳定。
- 部分中文文案存在乱码，需要修正。
- 没有登录、任务历史、图片持久化存储、用户隔离和使用次数记录。

## 4. 目标架构

```text
前端页面
  -> FastAPI 后端
    -> 登录模块
    -> 预设/提示词模块
    -> 生图服务模块
    -> 当前上游厂商适配器
    -> 本地图片存储
    -> SQLite 数据库
```

第一版保持单体应用，不引入微服务、分布式文件系统或复杂任务队列。先把产品主流程跑通。

## 5. 技术选型

### 5.1 前端技术选型

当前项目使用单个 `static/index.html` 承载前端。这个方式适合 demo，但不适合继续扩展成平台。

后续前端建议升级为：

```text
Vue 3
Vite
TypeScript
Vue Router
Pinia
Element Plus 或 Naive UI
```

选择 Vue 3 的原因：

- 生图平台会包含大量表单、上传、历史记录、结果图库和用户状态，Vue 更适合维护这些交互。
- 后续增加模型选择、套餐额度、用户中心、管理配置时，组件化结构更稳。
- 国内生态成熟，团队维护成本低。
- Vite 构建后的静态文件可以继续由 FastAPI 或 Nginx 托管。

前端设计和实现时，需要使用 `frontend-design` 技能来约束页面结构、交互体验、视觉风格和响应式细节。

### 5.2 后端技术选型

后端继续使用 FastAPI，不重新选型。

原因：

- 当前项目已经基于 FastAPI，迁移成本低。
- 生图平台核心是上传图片、调用上游 API、保存任务、返回 JSON，FastAPI 很适合。
- 异步请求上游模型接口比较方便。
- 后续增加 SQLite、登录、对象存储、任务记录、多模型 provider 都能自然扩展。

后端建议技术栈：

```text
FastAPI
SQLAlchemy 或 SQLModel
SQLite 初期
后续 MySQL 或 PostgreSQL
本地文件存储初期
后续对象存储
```

暂不建议切换到 Django、Node.js 或其他后端框架，除非后续产品重点转向复杂后台管理系统。

## 6. 后端改造计划

### 6.1 移除 3D 功能

删除或停用：

- `service_3d.py`
- `/generate3d/submit`
- `/generate3d/query`
- `/generate3d/upload`
- `/generate3d/upload-multi`
- `requirements.txt` 中的腾讯 3D SDK 依赖
- `.env.example` 中的 3D 相关环境变量
- 前端所有 3D 标签页、按钮、轮询逻辑和结果展示区域

### 6.2 增加预设系统

新增一个生图预设层，用来管理不同玩法的提示词和输入字段。

建议文件：

- `presets.py`

每个预设包含：

- `id`：预设标识
- `name`：展示名称
- `description`：说明
- `input_mode`：输入模式
- `system_prompt`：系统提示词
- `text_prompt_template`：文本生图提示词模板
- `image_prompt_template`：图生图提示词模板
- `fields`：前端需要展示的字段

第一批预设：

- `q_avatar`：Q 版形象大师
- `makeup_master`：妆造大师
- `persona_photo`：人设写真
- `profile_avatar`：头像生成
- `free_generation`：自由生图

### 6.3 增加模型供应商适配层

第一版只实现当前上游厂商。

建议结构：

```text
providers/
  __init__.py
  base.py
  current_provider.py
```

供应商接口建议：

```python
class ImageProvider:
    async def generate_from_text(self, prompt: str, options: dict) -> dict:
        ...

    async def generate_from_image(self, image_bytes: bytes, content_type: str, prompt: str, options: dict) -> dict:
        ...
```

这样后续接入豆包、阿里、腾讯时，只需要新增 provider，不需要重写业务逻辑和前端。

### 6.4 增加统一生图服务

建议文件：

- `services/image_service.py`

职责：

- 校验用户输入
- 读取所选预设
- 组装最终提示词
- 调用当前上游厂商适配器
- 统一上游返回结构
- 保存任务和图片信息
- 给前端返回稳定的数据结构

### 6.5 统一接口返回格式

前端不再直接解析上游原始文本，而是消费后端统一结构。

建议返回：

```json
{
  "task_id": "string",
  "provider": "current",
  "model": "string",
  "preset": "makeup_master",
  "status": "succeeded",
  "content": "上游原始文本或摘要",
  "images": [
    {
      "url": "string",
      "local_path": "string",
      "width": null,
      "height": null
    }
  ],
  "usage": {}
}
```

如果当前上游仍然返回一段文本或图片 URL，先由后端做解析和规范化，前端只处理统一后的 `images` 数组。

### 6.6 新接口设计

建议新增接口：

- `GET /api/health`：健康检查
- `GET /api/presets`：获取生图预设
- `POST /api/auth/register`：注册
- `POST /api/auth/login`：登录
- `POST /api/auth/logout`：退出登录
- `GET /api/me`：获取当前用户
- `POST /api/generate/text`：文本生图
- `POST /api/generate/image`：参考图生图
- `POST /api/generate/persona`：人设生图
- `GET /api/tasks`：当前用户任务历史
- `GET /api/tasks/{task_id}`：任务详情
- `GET /api/images/{image_id}`：获取图片

旧接口可以直接删除，也可以短期保留为兼容别名：

- `/generate/text`
- `/generate/image`

## 7. 登录计划

建议第一版就做登录。

原因：

- 用户会上传自拍、人脸、宠物、个人形象等隐私图片。
- 需要区分不同用户的生成历史。
- 后续要做额度、套餐、付费、风控时必须有用户体系。

第一版登录方式：

- 用户名 + 密码
- 密码哈希存储
- Cookie Session 或 JWT
- 提供当前用户接口

后续可扩展：

- 手机号登录
- 微信登录
- 第三方 OAuth
- 管理后台用户管理

## 8. 数据库计划

第一版使用 SQLite。

建议数据库文件：

- `data/app.db`

建议数据表：

### users

- `id`
- `username`
- `password_hash`
- `created_at`

### generation_tasks

- `id`
- `user_id`
- `preset_id`
- `input_type`
- `prompt`
- `provider`
- `model`
- `status`
- `raw_response`
- `error_message`
- `created_at`
- `updated_at`

### generated_images

- `id`
- `task_id`
- `user_id`
- `source_url`
- `local_path`
- `mime_type`
- `created_at`

### uploaded_images

- `id`
- `user_id`
- `original_filename`
- `local_path`
- `mime_type`
- `size_bytes`
- `created_at`

这些表已经足够支持登录、历史记录、图片归属、使用统计和后续计费。

## 9. 文件存储计划

第一版使用本地文件存储，不单独搭文件服务器。

建议目录：

```text
data/
  uploads/
  outputs/
  app.db
```

规则：

- 用户上传图片保存到 `data/uploads/`
- 生成图片保存到 `data/outputs/`
- 数据库只保存相对路径
- 图片访问需要校验用户归属，避免用户访问别人的图片

正式上线后再迁移到对象存储：

- 火山引擎 TOS
- 阿里云 OSS
- 腾讯云 COS

生产环境建议：

- 使用对象存储保存图片
- 数据库保存对象 key
- 私有图片使用签名 URL
- 配置生命周期规则自动清理长期不用的临时图

## 10. 前端改造计划

将当前 `static/index.html` 升级为 Vue 3 前端应用，并改造成 2D 生图工作台。

前端设计阶段需要使用 `frontend-design` 技能，重点检查：

- 页面是不是直接进入可用的生图工作台，而不是营销落地页。
- 工具区、上传区、结果区和历史区是否清晰。
- 登录状态、加载状态、失败状态、空状态是否完整。
- 移动端和桌面端布局是否稳定。
- 文案、按钮、卡片、表单控件是否符合工具型产品体验。

主要区域：

- 顶部导航和登录状态
- 生图预设选择
- 输入面板
- 参考图上传
- 人设字段
- 提示词输入框
- 生成按钮
- 结果图库
- 历史记录

### 10.1 Q 版形象大师

功能：

- 选择对象类型：宠物/人物
- 上传参考图或输入描述
- 生成 Q 版 2D 图片

### 10.2 妆造大师

功能：

- 上传自拍或参考图
- 选择风格方向
- 可填写：
  - 妆容风格
  - 发型
  - 服装
  - 场景
  - 妆造强度
- 生成适合用户形象的妆造图

### 10.3 人设写真

功能：

- 人设名称
- 外貌特征
- 气质
- 服装
- 场景
- 风格
- 负面词

### 10.4 自由生图

功能：

- 输入自由提示词
- 可选参考图
- 生成图片

## 11. 安全和隐私要求

第一版最低要求：

- 限制上传图片大小
- 只接受图片 MIME 类型
- 用户只能访问自己的图片
- 密码必须哈希存储
- 不记录明文密码
- 默认不公开用户生成的人脸图片
- 后续需要提供图片删除能力

后续增强：

- 内容审核
- 管理后台审核
- 频率限制
- 用户数据删除
- 操作审计日志

## 12. 模型供应商切换待办

第一版不做模型切换。

后续候选供应商：

- 火山方舟豆包 Seedream
- 阿里百炼通义万相
- 腾讯混元生图
- 智谱 CogView
- MiniMax 生图

后续能力：

- 多供应商路由
- 失败自动切换
- 成本预估
- 按模型配置质量档位
- 管理后台配置模型
- 用户侧选择模型

## 13. 实施顺序

1. 修正页面和提示词中的中文乱码。
2. 移除所有 3D 后端路由和前端入口。
3. 增加 SQLite 数据库和本地文件存储目录。
4. 增加简单注册和登录流程。
5. 增加生图预设配置系统。
6. 增加当前上游厂商适配器。
7. 将现有 Q 版生图改造成 `q_avatar` 预设。
8. 增加 `makeup_master` 妆造大师预设。
9. 增加 `persona_photo` 人设写真预设。
10. 使用 `frontend-design` 技能设计前端信息架构、交互和响应式布局。
11. 将前端重构为 Vue 3 版 2D 生图工作台。
12. 增加任务历史和结果图库。
13. 本地验证文本生图、上传图片生图、登录、历史记录和图片访问。

## 14. 第一版验收标准

第一版完成时应满足：

- 应用中不再出现任何 3D 功能。
- 用户可以注册和登录。
- 登录用户可以用文本生成图片。
- 登录用户可以上传参考图生成图片。
- Q 版形象生图作为内置预设可用。
- 妆造大师作为内置预设可用。
- 生图任务保存到 SQLite。
- 上传图片和生成图片保存到本地目录。
- 用户可以查看自己的生成历史。
- 前端已经从单 HTML 页面升级为 Vue 3 应用。
- 前端设计和实现过程已按 `frontend-design` 技能要求检查。
- 后续更换模型供应商时，只需要新增 provider，不需要重写业务和前端。
