export interface PresetFieldOption {
  label: string
  value: string
}

export interface PresetField {
  id: string
  label: string
  type: 'text' | 'select'
  default?: string
  options?: PresetFieldOption[]
}

export interface Preset {
  id: string
  name: string
  description: string
  input_modes: string[]
  fields: PresetField[]
}

export interface User {
  id: number
  username: string
}

export interface GeneratedImage {
  id: number
  url: string
  source_url?: string
  local_path?: string
  mime_type?: string
  created_at?: string
}

export interface GenerationResult {
  task_id: string
  provider: string
  model: string
  preset: string
  status: string
  prompt: string
  content: string
  images: GeneratedImage[]
  usage: Record<string, unknown>
}

export interface TaskItem {
  id: string
  preset_id: string
  input_type: string
  prompt: string
  provider: string
  model: string
  status: string
  error_message?: string
  created_at: string
  updated_at: string
  images: GeneratedImage[]
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {})
    },
    ...options
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || `请求失败 (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  getPresets: () => request<{ presets: Preset[] }>('/api/presets'),
  me: () => request<{ user: User }>('/api/me'),
  register: (username: string, password: string) =>
    request<{ user: User }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
  login: (username: string, password: string) =>
    request<{ user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
  generateText: (presetId: string, prompt: string, fields: Record<string, string>) =>
    request<GenerationResult>('/api/generate/text', {
      method: 'POST',
      body: JSON.stringify({ preset_id: presetId, prompt, fields })
    }),
  generateImage: (presetId: string, prompt: string, fields: Record<string, string>, file: File) => {
    const form = new FormData()
    form.append('file', file)
    form.append('preset_id', presetId)
    form.append('prompt', prompt)
    form.append('fields_json', JSON.stringify(fields))
    return request<GenerationResult>('/api/generate/image', {
      method: 'POST',
      body: form
    })
  },
  getTasks: () => request<{ tasks: TaskItem[] }>('/api/tasks'),
  deleteTask: (taskId: string) => request<{ ok: boolean }>(`/api/tasks/${taskId}`, { method: 'DELETE' })
}
