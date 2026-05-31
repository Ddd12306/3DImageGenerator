<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  Copy,
  Download,
  Eye,
  History,
  ImagePlus,
  LogOut,
  RefreshCw,
  Sparkles,
  Trash2,
  UploadCloud,
  UserRound,
  WandSparkles,
  X
} from 'lucide-vue-next'
import { api, type GeneratedImage, type GenerationResult, type Preset, type TaskItem } from './api'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const presets = ref<Preset[]>([])
const selectedPresetId = ref('q_avatar')
const prompt = ref('')
const fields = reactive<Record<string, string>>({})
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const result = ref<GenerationResult | null>(null)
const selectedTask = ref<TaskItem | null>(null)
const previewImage = ref<GeneratedImage | null>(null)
const tasks = ref<TaskItem[]>([])
const loading = ref(false)
const loadingHistory = ref(false)
const deletingTaskId = ref('')
const error = ref('')
const authMode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')

const selectedPreset = computed(() => presets.value.find((preset) => preset.id === selectedPresetId.value) || presets.value[0])
const canUseImage = computed(() => selectedPreset.value?.input_modes.includes('image'))
const canGenerate = computed(() => Boolean(auth.user) && !loading.value && (prompt.value.trim().length > 0 || selectedFile.value))
const displayImages = computed(() => result.value?.images || selectedTask.value?.images || [])
const displayPrompt = computed(() => result.value?.prompt || selectedTask.value?.prompt || '')
const displayContent = computed(() => result.value?.content || '')
const displayMeta = computed(() =>
  result.value
    ? `${result.value.provider} / ${result.value.model}`
    : selectedTask.value
      ? `${presetName(selectedTask.value.preset_id)} / ${selectedTask.value.model}`
      : ''
)
const hasDisplayResult = computed(() => Boolean(result.value || selectedTask.value))
const isShadowPreset = computed(() => selectedPreset.value?.id === 'shadow_artist')
const promptPlaceholder = computed(() =>
  isShadowPreset.value
    ? '例如：给影子加一对夸张但自然的翅膀，边缘像真实阴影一样柔和，脚和路面不要变。'
    : '描述你想生成的画面、角色、人设、妆容、场景或特殊要求。'
)

const shadowIdeas = [
  '把影子画成背后长出一对天使翅膀，边缘保持柔和阴影质感。',
  '让影子像披着超级英雄披风，披风顺着阳光方向自然延展。',
  '在影子里加入街头涂鸦线条和小怪兽轮廓，像影子自己活过来。',
  '把影子改成赛博装甲外形，只改影子，不改变鞋子和地面。'
]

function resetFields(preset: Preset | undefined) {
  Object.keys(fields).forEach((key) => delete fields[key])
  preset?.fields.forEach((field) => {
    fields[field.id] = field.default || ''
  })
}

watch(selectedPreset, (preset) => {
  resetFields(preset)
  result.value = null
  error.value = ''
})

onMounted(async () => {
  await auth.load()
  const data = await api.getPresets()
  presets.value = data.presets
  const initialPreset = data.presets.find((preset) => preset.id === 'shadow_artist') || data.presets[0]
  selectedPresetId.value = initialPreset?.id || 'q_avatar'
  resetFields(initialPreset)
  if (auth.user) {
    await loadTasks()
  }
})

async function submitAuth() {
  error.value = ''
  try {
    if (authMode.value === 'login') {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, password.value)
    }
    password.value = ''
    await loadTasks()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  }
}

async function logout() {
  await auth.logout()
  tasks.value = []
  result.value = null
  selectedTask.value = null
  previewImage.value = null
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  selectedFile.value = file
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(file)
}

function clearFile() {
  selectedFile.value = null
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

async function generate() {
  if (!auth.user) {
    error.value = '请先登录'
    return
  }
  if (!selectedPreset.value) return

  loading.value = true
  error.value = ''
  result.value = null
  selectedTask.value = null
  try {
    if (selectedFile.value && canUseImage.value) {
      result.value = await api.generateImage(selectedPreset.value.id, prompt.value, { ...fields }, selectedFile.value)
    } else {
      result.value = await api.generateText(selectedPreset.value.id, prompt.value, { ...fields })
    }
    await loadTasks()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '生成失败'
  } finally {
    loading.value = false
  }
}

async function loadTasks() {
  if (!auth.user) return
  loadingHistory.value = true
  try {
    const data = await api.getTasks()
    tasks.value = data.tasks
  } finally {
    loadingHistory.value = false
  }
}

async function copyPrompt(text: string) {
  await navigator.clipboard.writeText(text)
}

function useShadowIdea(idea: string) {
  prompt.value = idea
}

function selectTask(task: TaskItem) {
  selectedTask.value = task
  result.value = null
  previewImage.value = task.images[0] || null
}

async function deleteHistoryTask(task: TaskItem) {
  if (task.status !== 'failed') return
  if (!window.confirm('确认删除这条失败记录？')) return

  deletingTaskId.value = task.id
  error.value = ''
  try {
    await api.deleteTask(task.id)
    tasks.value = tasks.value.filter((item) => item.id !== task.id)
    if (selectedTask.value?.id === task.id) {
      selectedTask.value = null
      previewImage.value = null
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '删除失败'
  } finally {
    deletingTaskId.value = ''
  }
}

function presetName(presetId: string) {
  return presets.value.find((preset) => preset.id === presetId)?.name || presetId
}

function imageFileName(image: GeneratedImage) {
  const extension = image.mime_type?.split('/')[1]?.replace('jpeg', 'jpg') || 'png'
  return `generated-${image.id || Date.now()}.${extension}`
}
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark"><Sparkles :size="20" /></div>
        <div>
          <h1>2D 生图工作台</h1>
          <p>人设、妆造、头像和 Q 版形象</p>
        </div>
      </div>

      <div v-if="auth.user" class="userbar">
        <span><UserRound :size="16" /> {{ auth.user.username }}</span>
        <button type="button" class="icon-btn" title="退出登录" @click="logout">
          <LogOut :size="18" />
        </button>
      </div>
    </header>

    <section v-if="!auth.user" class="auth-panel">
      <div class="auth-card">
        <h2>{{ authMode === 'login' ? '登录' : '注册' }}</h2>
        <div class="auth-tabs">
          <button :class="{ active: authMode === 'login' }" type="button" @click="authMode = 'login'">登录</button>
          <button :class="{ active: authMode === 'register' }" type="button" @click="authMode = 'register'">注册</button>
        </div>
        <label>
          用户名
          <input v-model="username" autocomplete="username" placeholder="至少 3 个字符" />
        </label>
        <label>
          密码
          <input v-model="password" type="password" autocomplete="current-password" placeholder="至少 6 个字符" @keyup.enter="submitAuth" />
        </label>
        <button class="primary-btn" type="button" @click="submitAuth">继续</button>
      </div>
    </section>

    <section v-else class="workspace">
      <aside class="preset-rail">
        <button
          v-for="preset in presets"
          :key="preset.id"
          type="button"
          class="preset-item"
          :class="{ active: preset.id === selectedPresetId }"
          @click="selectedPresetId = preset.id"
        >
          <WandSparkles :size="18" />
          <span>{{ preset.name }}</span>
        </button>
      </aside>

      <section class="tool-panel">
        <div class="panel-head">
          <div>
            <h2>{{ selectedPreset?.name }}</h2>
            <p>{{ selectedPreset?.description }}</p>
          </div>
          <button type="button" class="ghost-btn" :disabled="loadingHistory" @click="loadTasks">
            <RefreshCw :size="16" />刷新历史
          </button>
        </div>

        <div class="field-grid">
          <label v-for="field in selectedPreset?.fields" :key="field.id" class="field">
            {{ field.label }}
            <select v-if="field.type === 'select'" v-model="fields[field.id]">
              <option v-for="option in field.options" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
            <input v-else v-model="fields[field.id]" />
          </label>
        </div>

        <label class="field prompt-field">
          提示词
          <textarea v-model="prompt" rows="7" :placeholder="promptPlaceholder" />
        </label>

        <div v-if="isShadowPreset" class="idea-strip" aria-label="影子创意示例">
          <button v-for="idea in shadowIdeas" :key="idea" type="button" @click="useShadowIdea(idea)">
            {{ idea }}
          </button>
        </div>

        <div class="upload-zone" :class="{ disabled: !canUseImage }">
          <div>
            <UploadCloud :size="22" />
            <strong>参考图</strong>
            <span>{{ canUseImage ? '可选，上传后走图生图流程' : '当前预设不支持参考图' }}</span>
          </div>
          <input :disabled="!canUseImage" type="file" accept="image/*" @change="onFileChange" />
        </div>

        <div v-if="previewUrl" class="preview-row">
          <img :src="previewUrl" alt="参考图预览" />
          <button class="ghost-btn" type="button" @click="clearFile">移除参考图</button>
        </div>

        <button class="primary-btn generate-btn" type="button" :disabled="!canGenerate" @click="generate">
          <ImagePlus :size="18" />
          {{ loading ? '生成中...' : '生成图片' }}
        </button>

        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <section class="result-panel">
        <div class="panel-head compact">
          <h2>{{ selectedTask ? '历史预览' : '生成结果' }}</h2>
          <button v-if="displayPrompt" class="icon-btn" title="复制提示词" type="button" @click="copyPrompt(displayPrompt)">
            <Copy :size="17" />
          </button>
        </div>

        <div v-if="loading" class="empty-state">正在调用上游生图服务...</div>
        <div v-else-if="hasDisplayResult" class="result-content">
          <div v-if="displayImages.length" class="image-grid">
            <figure v-for="image in displayImages" :key="image.id || image.url">
              <button class="image-preview-button" type="button" @click="previewImage = image">
                <img :src="image.url" alt="生成结果" />
                <span><Eye :size="15" />预览</span>
              </button>
              <div class="figure-actions">
                <a :href="image.url" :download="imageFileName(image)">
                  <Download :size="15" />下载
                </a>
                <a :href="image.url" target="_blank" rel="noreferrer">
                  打开
                </a>
              </div>
            </figure>
          </div>
          <pre v-else>{{ displayContent || '这条历史记录没有可预览的图片。' }}</pre>
          <div class="meta-line">{{ displayMeta }}</div>
        </div>
        <div v-else class="empty-state">结果会显示在这里。</div>
      </section>

      <aside class="history-panel">
        <div class="panel-head compact">
          <h2><History :size="18" />历史</h2>
        </div>
        <div v-if="!tasks.length" class="empty-state small">还没有生成记录。</div>
        <article
          v-for="task in tasks"
          :key="task.id"
          class="task-item"
          :class="{ active: selectedTask?.id === task.id }"
        >
          <button type="button" class="task-select" @click="selectTask(task)">
            <div class="task-thumb">
              <img v-if="task.images[0]" :src="task.images[0].url" alt="历史结果" />
              <ImagePlus v-else :size="18" />
            </div>
            <div>
              <strong>{{ presetName(task.preset_id) }}</strong>
              <span>{{ task.status }} · {{ task.input_type }}</span>
              <em v-if="task.images.length">{{ task.images.length }} 张，可预览下载</em>
            </div>
          </button>
          <button
            v-if="task.status === 'failed'"
            type="button"
            class="icon-btn danger-btn"
            title="删除失败记录"
            :disabled="deletingTaskId === task.id"
            @click="deleteHistoryTask(task)"
          >
            <Trash2 :size="16" />
          </button>
        </article>
      </aside>
    </section>

    <div v-if="previewImage" class="preview-modal" role="dialog" aria-modal="true" @click.self="previewImage = null">
      <div class="preview-modal-inner">
        <div class="preview-modal-actions">
          <a :href="previewImage.url" :download="imageFileName(previewImage)">
            <Download :size="16" />下载
          </a>
          <button class="icon-btn" type="button" title="关闭预览" @click="previewImage = null">
            <X :size="18" />
          </button>
        </div>
        <img :src="previewImage.url" alt="大图预览" />
      </div>
    </div>
  </main>
</template>
