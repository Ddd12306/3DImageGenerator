import { computed, onMounted, reactive, ref, watch } from 'vue';
import { Copy, Download, Eye, History, ImagePlus, LogOut, RefreshCw, Sparkles, Trash2, UploadCloud, UserRound, WandSparkles, X } from 'lucide-vue-next';
import { api } from './api';
import { useAuthStore } from './stores/auth';
const auth = useAuthStore();
const presets = ref([]);
const selectedPresetId = ref('q_avatar');
const prompt = ref('');
const fields = reactive({});
const selectedFile = ref(null);
const previewUrl = ref('');
const result = ref(null);
const selectedTask = ref(null);
const previewImage = ref(null);
const tasks = ref([]);
const loading = ref(false);
const loadingHistory = ref(false);
const deletingTaskId = ref('');
const error = ref('');
const authMode = ref('login');
const username = ref('');
const password = ref('');
const selectedPreset = computed(() => presets.value.find((preset) => preset.id === selectedPresetId.value) || presets.value[0]);
const canUseImage = computed(() => selectedPreset.value?.input_modes.includes('image'));
const canGenerate = computed(() => Boolean(auth.user) && !loading.value && (prompt.value.trim().length > 0 || selectedFile.value));
const displayImages = computed(() => result.value?.images || selectedTask.value?.images || []);
const displayPrompt = computed(() => result.value?.prompt || selectedTask.value?.prompt || '');
const displayContent = computed(() => result.value?.content || '');
const displayMeta = computed(() => result.value
    ? `${result.value.provider} / ${result.value.model}`
    : selectedTask.value
        ? `${presetName(selectedTask.value.preset_id)} / ${selectedTask.value.model}`
        : '');
const hasDisplayResult = computed(() => Boolean(result.value || selectedTask.value));
const isShadowPreset = computed(() => selectedPreset.value?.id === 'shadow_artist');
const promptPlaceholder = computed(() => isShadowPreset.value
    ? '例如：给影子加一对夸张但自然的翅膀，边缘像真实阴影一样柔和，脚和路面不要变。'
    : '描述你想生成的画面、角色、人设、妆容、场景或特殊要求。');
const shadowIdeas = [
    '把影子画成背后长出一对天使翅膀，边缘保持柔和阴影质感。',
    '让影子像披着超级英雄披风，披风顺着阳光方向自然延展。',
    '在影子里加入街头涂鸦线条和小怪兽轮廓，像影子自己活过来。',
    '把影子改成赛博装甲外形，只改影子，不改变鞋子和地面。'
];
function resetFields(preset) {
    Object.keys(fields).forEach((key) => delete fields[key]);
    preset?.fields.forEach((field) => {
        fields[field.id] = field.default || '';
    });
}
watch(selectedPreset, (preset) => {
    resetFields(preset);
    result.value = null;
    error.value = '';
});
onMounted(async () => {
    await auth.load();
    const data = await api.getPresets();
    presets.value = data.presets;
    const initialPreset = data.presets.find((preset) => preset.id === 'shadow_artist') || data.presets[0];
    selectedPresetId.value = initialPreset?.id || 'q_avatar';
    resetFields(initialPreset);
    if (auth.user) {
        await loadTasks();
    }
});
async function submitAuth() {
    error.value = '';
    try {
        if (authMode.value === 'login') {
            await auth.login(username.value, password.value);
        }
        else {
            await auth.register(username.value, password.value);
        }
        password.value = '';
        await loadTasks();
    }
    catch (err) {
        error.value = err instanceof Error ? err.message : '登录失败';
    }
}
async function logout() {
    await auth.logout();
    tasks.value = [];
    result.value = null;
    selectedTask.value = null;
    previewImage.value = null;
}
function onFileChange(event) {
    const input = event.target;
    const file = input.files?.[0];
    if (!file)
        return;
    selectedFile.value = file;
    if (previewUrl.value)
        URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = URL.createObjectURL(file);
}
function clearFile() {
    selectedFile.value = null;
    if (previewUrl.value)
        URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = '';
}
async function generate() {
    if (!auth.user) {
        error.value = '请先登录';
        return;
    }
    if (!selectedPreset.value)
        return;
    loading.value = true;
    error.value = '';
    result.value = null;
    selectedTask.value = null;
    try {
        if (selectedFile.value && canUseImage.value) {
            result.value = await api.generateImage(selectedPreset.value.id, prompt.value, { ...fields }, selectedFile.value);
        }
        else {
            result.value = await api.generateText(selectedPreset.value.id, prompt.value, { ...fields });
        }
        await loadTasks();
    }
    catch (err) {
        error.value = err instanceof Error ? err.message : '生成失败';
    }
    finally {
        loading.value = false;
    }
}
async function loadTasks() {
    if (!auth.user)
        return;
    loadingHistory.value = true;
    try {
        const data = await api.getTasks();
        tasks.value = data.tasks;
    }
    finally {
        loadingHistory.value = false;
    }
}
async function copyPrompt(text) {
    await navigator.clipboard.writeText(text);
}
function useShadowIdea(idea) {
    prompt.value = idea;
}
function selectTask(task) {
    selectedTask.value = task;
    result.value = null;
    previewImage.value = task.images[0] || null;
}
async function deleteHistoryTask(task) {
    if (task.status !== 'failed')
        return;
    if (!window.confirm('确认删除这条失败记录？'))
        return;
    deletingTaskId.value = task.id;
    error.value = '';
    try {
        await api.deleteTask(task.id);
        tasks.value = tasks.value.filter((item) => item.id !== task.id);
        if (selectedTask.value?.id === task.id) {
            selectedTask.value = null;
            previewImage.value = null;
        }
    }
    catch (err) {
        error.value = err instanceof Error ? err.message : '删除失败';
    }
    finally {
        deletingTaskId.value = '';
    }
}
function presetName(presetId) {
    return presets.value.find((preset) => preset.id === presetId)?.name || presetId;
}
function imageFileName(image) {
    const extension = image.mime_type?.split('/')[1]?.replace('jpeg', 'jpg') || 'png';
    return `generated-${image.id || Date.now()}.${extension}`;
}
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.main, __VLS_intrinsics.main)({
    ...{ class: "app-shell" },
});
/** @type {__VLS_StyleScopedClasses['app-shell']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.header, __VLS_intrinsics.header)({
    ...{ class: "topbar" },
});
/** @type {__VLS_StyleScopedClasses['topbar']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "brand" },
});
/** @type {__VLS_StyleScopedClasses['brand']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "brand-mark" },
});
/** @type {__VLS_StyleScopedClasses['brand-mark']} */ ;
let __VLS_0;
/** @ts-ignore @type { | typeof __VLS_components.Sparkles} */
Sparkles;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    size: (20),
}));
const __VLS_2 = __VLS_1({
    size: (20),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.h1, __VLS_intrinsics.h1)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
if (__VLS_ctx.auth.user) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "userbar" },
    });
    /** @type {__VLS_StyleScopedClasses['userbar']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    let __VLS_5;
    /** @ts-ignore @type { | typeof __VLS_components.UserRound} */
    UserRound;
    // @ts-ignore
    const __VLS_6 = __VLS_asFunctionalComponent1(__VLS_5, new __VLS_5({
        size: (16),
    }));
    const __VLS_7 = __VLS_6({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_6));
    (__VLS_ctx.auth.user.username);
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (__VLS_ctx.logout) },
        type: "button",
        ...{ class: "icon-btn" },
        title: "退出登录",
    });
    /** @type {__VLS_StyleScopedClasses['icon-btn']} */ ;
    let __VLS_10;
    /** @ts-ignore @type { | typeof __VLS_components.LogOut} */
    LogOut;
    // @ts-ignore
    const __VLS_11 = __VLS_asFunctionalComponent1(__VLS_10, new __VLS_10({
        size: (18),
    }));
    const __VLS_12 = __VLS_11({
        size: (18),
    }, ...__VLS_functionalComponentArgsRest(__VLS_11));
}
if (!__VLS_ctx.auth.user) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "auth-panel" },
    });
    /** @type {__VLS_StyleScopedClasses['auth-panel']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "auth-card" },
    });
    /** @type {__VLS_StyleScopedClasses['auth-card']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
    (__VLS_ctx.authMode === 'login' ? '登录' : '注册');
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "auth-tabs" },
    });
    /** @type {__VLS_StyleScopedClasses['auth-tabs']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (...[$event]) => {
                if (!(!__VLS_ctx.auth.user))
                    return;
                __VLS_ctx.authMode = 'login';
                // @ts-ignore
                [auth, auth, auth, logout, authMode, authMode,];
            } },
        ...{ class: ({ active: __VLS_ctx.authMode === 'login' }) },
        type: "button",
    });
    /** @type {__VLS_StyleScopedClasses['active']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (...[$event]) => {
                if (!(!__VLS_ctx.auth.user))
                    return;
                __VLS_ctx.authMode = 'register';
                // @ts-ignore
                [authMode, authMode,];
            } },
        ...{ class: ({ active: __VLS_ctx.authMode === 'register' }) },
        type: "button",
    });
    /** @type {__VLS_StyleScopedClasses['active']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.label, __VLS_intrinsics.label)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.input)({
        autocomplete: "username",
        placeholder: "至少 3 个字符",
    });
    (__VLS_ctx.username);
    __VLS_asFunctionalElement1(__VLS_intrinsics.label, __VLS_intrinsics.label)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.input)({
        ...{ onKeyup: (__VLS_ctx.submitAuth) },
        type: "password",
        autocomplete: "current-password",
        placeholder: "至少 6 个字符",
    });
    (__VLS_ctx.password);
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (__VLS_ctx.submitAuth) },
        ...{ class: "primary-btn" },
        type: "button",
    });
    /** @type {__VLS_StyleScopedClasses['primary-btn']} */ ;
}
else {
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "workspace" },
    });
    /** @type {__VLS_StyleScopedClasses['workspace']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.aside, __VLS_intrinsics.aside)({
        ...{ class: "preset-rail" },
    });
    /** @type {__VLS_StyleScopedClasses['preset-rail']} */ ;
    for (const [preset] of __VLS_vFor((__VLS_ctx.presets))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(!__VLS_ctx.auth.user))
                        return;
                    __VLS_ctx.selectedPresetId = preset.id;
                    // @ts-ignore
                    [authMode, username, submitAuth, submitAuth, password, presets, selectedPresetId,];
                } },
            key: (preset.id),
            type: "button",
            ...{ class: "preset-item" },
            ...{ class: ({ active: preset.id === __VLS_ctx.selectedPresetId }) },
        });
        /** @type {__VLS_StyleScopedClasses['preset-item']} */ ;
        /** @type {__VLS_StyleScopedClasses['active']} */ ;
        let __VLS_15;
        /** @ts-ignore @type { | typeof __VLS_components.WandSparkles} */
        WandSparkles;
        // @ts-ignore
        const __VLS_16 = __VLS_asFunctionalComponent1(__VLS_15, new __VLS_15({
            size: (18),
        }));
        const __VLS_17 = __VLS_16({
            size: (18),
        }, ...__VLS_functionalComponentArgsRest(__VLS_16));
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (preset.name);
        // @ts-ignore
        [selectedPresetId,];
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "tool-panel" },
    });
    /** @type {__VLS_StyleScopedClasses['tool-panel']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-head" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-head']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
    (__VLS_ctx.selectedPreset?.name);
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
    (__VLS_ctx.selectedPreset?.description);
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (__VLS_ctx.loadTasks) },
        type: "button",
        ...{ class: "ghost-btn" },
        disabled: (__VLS_ctx.loadingHistory),
    });
    /** @type {__VLS_StyleScopedClasses['ghost-btn']} */ ;
    let __VLS_20;
    /** @ts-ignore @type { | typeof __VLS_components.RefreshCw} */
    RefreshCw;
    // @ts-ignore
    const __VLS_21 = __VLS_asFunctionalComponent1(__VLS_20, new __VLS_20({
        size: (16),
    }));
    const __VLS_22 = __VLS_21({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_21));
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "field-grid" },
    });
    /** @type {__VLS_StyleScopedClasses['field-grid']} */ ;
    for (const [field] of __VLS_vFor((__VLS_ctx.selectedPreset?.fields))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.label, __VLS_intrinsics.label)({
            key: (field.id),
            ...{ class: "field" },
        });
        /** @type {__VLS_StyleScopedClasses['field']} */ ;
        (field.label);
        if (field.type === 'select') {
            __VLS_asFunctionalElement1(__VLS_intrinsics.select, __VLS_intrinsics.select)({
                value: (__VLS_ctx.fields[field.id]),
            });
            for (const [option] of __VLS_vFor((field.options))) {
                __VLS_asFunctionalElement1(__VLS_intrinsics.option, __VLS_intrinsics.option)({
                    key: (option.value),
                    value: (option.value),
                });
                (option.label);
                // @ts-ignore
                [selectedPreset, selectedPreset, selectedPreset, loadTasks, loadingHistory, fields,];
            }
        }
        else {
            __VLS_asFunctionalElement1(__VLS_intrinsics.input)({});
            (__VLS_ctx.fields[field.id]);
        }
        // @ts-ignore
        [fields,];
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.label, __VLS_intrinsics.label)({
        ...{ class: "field prompt-field" },
    });
    /** @type {__VLS_StyleScopedClasses['field']} */ ;
    /** @type {__VLS_StyleScopedClasses['prompt-field']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.textarea)({
        value: (__VLS_ctx.prompt),
        rows: "7",
        placeholder: (__VLS_ctx.promptPlaceholder),
    });
    if (__VLS_ctx.isShadowPreset) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "idea-strip" },
            'aria-label': "影子创意示例",
        });
        /** @type {__VLS_StyleScopedClasses['idea-strip']} */ ;
        for (const [idea] of __VLS_vFor((__VLS_ctx.shadowIdeas))) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.auth.user))
                            return;
                        if (!(__VLS_ctx.isShadowPreset))
                            return;
                        __VLS_ctx.useShadowIdea(idea);
                        // @ts-ignore
                        [prompt, promptPlaceholder, isShadowPreset, shadowIdeas, useShadowIdea,];
                    } },
                key: (idea),
                type: "button",
            });
            (idea);
            // @ts-ignore
            [];
        }
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "upload-zone" },
        ...{ class: ({ disabled: !__VLS_ctx.canUseImage }) },
    });
    /** @type {__VLS_StyleScopedClasses['upload-zone']} */ ;
    /** @type {__VLS_StyleScopedClasses['disabled']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    let __VLS_25;
    /** @ts-ignore @type { | typeof __VLS_components.UploadCloud} */
    UploadCloud;
    // @ts-ignore
    const __VLS_26 = __VLS_asFunctionalComponent1(__VLS_25, new __VLS_25({
        size: (22),
    }));
    const __VLS_27 = __VLS_26({
        size: (22),
    }, ...__VLS_functionalComponentArgsRest(__VLS_26));
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.canUseImage ? '可选，上传后走图生图流程' : '当前预设不支持参考图');
    __VLS_asFunctionalElement1(__VLS_intrinsics.input)({
        ...{ onChange: (__VLS_ctx.onFileChange) },
        disabled: (!__VLS_ctx.canUseImage),
        type: "file",
        accept: "image/*",
    });
    if (__VLS_ctx.previewUrl) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "preview-row" },
        });
        /** @type {__VLS_StyleScopedClasses['preview-row']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.img)({
            src: (__VLS_ctx.previewUrl),
            alt: "参考图预览",
        });
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (__VLS_ctx.clearFile) },
            ...{ class: "ghost-btn" },
            type: "button",
        });
        /** @type {__VLS_StyleScopedClasses['ghost-btn']} */ ;
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (__VLS_ctx.generate) },
        ...{ class: "primary-btn generate-btn" },
        type: "button",
        disabled: (!__VLS_ctx.canGenerate),
    });
    /** @type {__VLS_StyleScopedClasses['primary-btn']} */ ;
    /** @type {__VLS_StyleScopedClasses['generate-btn']} */ ;
    let __VLS_30;
    /** @ts-ignore @type { | typeof __VLS_components.ImagePlus} */
    ImagePlus;
    // @ts-ignore
    const __VLS_31 = __VLS_asFunctionalComponent1(__VLS_30, new __VLS_30({
        size: (18),
    }));
    const __VLS_32 = __VLS_31({
        size: (18),
    }, ...__VLS_functionalComponentArgsRest(__VLS_31));
    (__VLS_ctx.loading ? '生成中...' : '生成图片');
    if (__VLS_ctx.error) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
            ...{ class: "error" },
        });
        /** @type {__VLS_StyleScopedClasses['error']} */ ;
        (__VLS_ctx.error);
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        ...{ class: "result-panel" },
    });
    /** @type {__VLS_StyleScopedClasses['result-panel']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-head compact" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-head']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
    (__VLS_ctx.selectedTask ? '历史预览' : '生成结果');
    if (__VLS_ctx.displayPrompt) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(!__VLS_ctx.auth.user))
                        return;
                    if (!(__VLS_ctx.displayPrompt))
                        return;
                    __VLS_ctx.copyPrompt(__VLS_ctx.displayPrompt);
                    // @ts-ignore
                    [canUseImage, canUseImage, canUseImage, onFileChange, previewUrl, previewUrl, clearFile, generate, canGenerate, loading, error, error, selectedTask, displayPrompt, displayPrompt, copyPrompt,];
                } },
            ...{ class: "icon-btn" },
            title: "复制提示词",
            type: "button",
        });
        /** @type {__VLS_StyleScopedClasses['icon-btn']} */ ;
        let __VLS_35;
        /** @ts-ignore @type { | typeof __VLS_components.Copy} */
        Copy;
        // @ts-ignore
        const __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
            size: (17),
        }));
        const __VLS_37 = __VLS_36({
            size: (17),
        }, ...__VLS_functionalComponentArgsRest(__VLS_36));
    }
    if (__VLS_ctx.loading) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "empty-state" },
        });
        /** @type {__VLS_StyleScopedClasses['empty-state']} */ ;
    }
    else if (__VLS_ctx.hasDisplayResult) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "result-content" },
        });
        /** @type {__VLS_StyleScopedClasses['result-content']} */ ;
        if (__VLS_ctx.displayImages.length) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                ...{ class: "image-grid" },
            });
            /** @type {__VLS_StyleScopedClasses['image-grid']} */ ;
            for (const [image] of __VLS_vFor((__VLS_ctx.displayImages))) {
                __VLS_asFunctionalElement1(__VLS_intrinsics.figure, __VLS_intrinsics.figure)({
                    key: (image.id || image.url),
                });
                __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
                    ...{ onClick: (...[$event]) => {
                            if (!!(!__VLS_ctx.auth.user))
                                return;
                            if (!!(__VLS_ctx.loading))
                                return;
                            if (!(__VLS_ctx.hasDisplayResult))
                                return;
                            if (!(__VLS_ctx.displayImages.length))
                                return;
                            __VLS_ctx.previewImage = image;
                            // @ts-ignore
                            [loading, hasDisplayResult, displayImages, displayImages, previewImage,];
                        } },
                    ...{ class: "image-preview-button" },
                    type: "button",
                });
                /** @type {__VLS_StyleScopedClasses['image-preview-button']} */ ;
                __VLS_asFunctionalElement1(__VLS_intrinsics.img)({
                    src: (image.url),
                    alt: "生成结果",
                });
                __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
                let __VLS_40;
                /** @ts-ignore @type { | typeof __VLS_components.Eye} */
                Eye;
                // @ts-ignore
                const __VLS_41 = __VLS_asFunctionalComponent1(__VLS_40, new __VLS_40({
                    size: (15),
                }));
                const __VLS_42 = __VLS_41({
                    size: (15),
                }, ...__VLS_functionalComponentArgsRest(__VLS_41));
                __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
                    ...{ class: "figure-actions" },
                });
                /** @type {__VLS_StyleScopedClasses['figure-actions']} */ ;
                __VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
                    href: (image.url),
                    download: (__VLS_ctx.imageFileName(image)),
                });
                let __VLS_45;
                /** @ts-ignore @type { | typeof __VLS_components.Download} */
                Download;
                // @ts-ignore
                const __VLS_46 = __VLS_asFunctionalComponent1(__VLS_45, new __VLS_45({
                    size: (15),
                }));
                const __VLS_47 = __VLS_46({
                    size: (15),
                }, ...__VLS_functionalComponentArgsRest(__VLS_46));
                __VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
                    href: (image.url),
                    target: "_blank",
                    rel: "noreferrer",
                });
                // @ts-ignore
                [imageFileName,];
            }
        }
        else {
            __VLS_asFunctionalElement1(__VLS_intrinsics.pre, __VLS_intrinsics.pre)({});
            (__VLS_ctx.displayContent || '这条历史记录没有可预览的图片。');
        }
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "meta-line" },
        });
        /** @type {__VLS_StyleScopedClasses['meta-line']} */ ;
        (__VLS_ctx.displayMeta);
    }
    else {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "empty-state" },
        });
        /** @type {__VLS_StyleScopedClasses['empty-state']} */ ;
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.aside, __VLS_intrinsics.aside)({
        ...{ class: "history-panel" },
    });
    /** @type {__VLS_StyleScopedClasses['history-panel']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-head compact" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-head']} */ ;
    /** @type {__VLS_StyleScopedClasses['compact']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
    let __VLS_50;
    /** @ts-ignore @type { | typeof __VLS_components.History} */
    History;
    // @ts-ignore
    const __VLS_51 = __VLS_asFunctionalComponent1(__VLS_50, new __VLS_50({
        size: (18),
    }));
    const __VLS_52 = __VLS_51({
        size: (18),
    }, ...__VLS_functionalComponentArgsRest(__VLS_51));
    if (!__VLS_ctx.tasks.length) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "empty-state small" },
        });
        /** @type {__VLS_StyleScopedClasses['empty-state']} */ ;
        /** @type {__VLS_StyleScopedClasses['small']} */ ;
    }
    for (const [task] of __VLS_vFor((__VLS_ctx.tasks))) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
            key: (task.id),
            ...{ class: "task-item" },
            ...{ class: ({ active: __VLS_ctx.selectedTask?.id === task.id }) },
        });
        /** @type {__VLS_StyleScopedClasses['task-item']} */ ;
        /** @type {__VLS_StyleScopedClasses['active']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(!__VLS_ctx.auth.user))
                        return;
                    __VLS_ctx.selectTask(task);
                    // @ts-ignore
                    [selectedTask, displayContent, displayMeta, tasks, tasks, selectTask,];
                } },
            type: "button",
            ...{ class: "task-select" },
        });
        /** @type {__VLS_StyleScopedClasses['task-select']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "task-thumb" },
        });
        /** @type {__VLS_StyleScopedClasses['task-thumb']} */ ;
        if (task.images[0]) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.img)({
                src: (task.images[0].url),
                alt: "历史结果",
            });
        }
        else {
            let __VLS_55;
            /** @ts-ignore @type { | typeof __VLS_components.ImagePlus} */
            ImagePlus;
            // @ts-ignore
            const __VLS_56 = __VLS_asFunctionalComponent1(__VLS_55, new __VLS_55({
                size: (18),
            }));
            const __VLS_57 = __VLS_56({
                size: (18),
            }, ...__VLS_functionalComponentArgsRest(__VLS_56));
        }
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
        __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
        (__VLS_ctx.presetName(task.preset_id));
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (task.status);
        (task.input_type);
        if (task.images.length) {
            __VLS_asFunctionalElement1(__VLS_intrinsics.em, __VLS_intrinsics.em)({});
            (task.images.length);
        }
        if (task.status === 'failed') {
            __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.auth.user))
                            return;
                        if (!(task.status === 'failed'))
                            return;
                        __VLS_ctx.deleteHistoryTask(task);
                        // @ts-ignore
                        [presetName, deleteHistoryTask,];
                    } },
                type: "button",
                ...{ class: "icon-btn danger-btn" },
                title: "删除失败记录",
                disabled: (__VLS_ctx.deletingTaskId === task.id),
            });
            /** @type {__VLS_StyleScopedClasses['icon-btn']} */ ;
            /** @type {__VLS_StyleScopedClasses['danger-btn']} */ ;
            let __VLS_60;
            /** @ts-ignore @type { | typeof __VLS_components.Trash2} */
            Trash2;
            // @ts-ignore
            const __VLS_61 = __VLS_asFunctionalComponent1(__VLS_60, new __VLS_60({
                size: (16),
            }));
            const __VLS_62 = __VLS_61({
                size: (16),
            }, ...__VLS_functionalComponentArgsRest(__VLS_61));
        }
        // @ts-ignore
        [deletingTaskId,];
    }
}
if (__VLS_ctx.previewImage) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.previewImage))
                    return;
                __VLS_ctx.previewImage = null;
                // @ts-ignore
                [previewImage, previewImage,];
            } },
        ...{ class: "preview-modal" },
        role: "dialog",
        'aria-modal': "true",
    });
    /** @type {__VLS_StyleScopedClasses['preview-modal']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "preview-modal-inner" },
    });
    /** @type {__VLS_StyleScopedClasses['preview-modal-inner']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "preview-modal-actions" },
    });
    /** @type {__VLS_StyleScopedClasses['preview-modal-actions']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
        href: (__VLS_ctx.previewImage.url),
        download: (__VLS_ctx.imageFileName(__VLS_ctx.previewImage)),
    });
    let __VLS_65;
    /** @ts-ignore @type { | typeof __VLS_components.Download} */
    Download;
    // @ts-ignore
    const __VLS_66 = __VLS_asFunctionalComponent1(__VLS_65, new __VLS_65({
        size: (16),
    }));
    const __VLS_67 = __VLS_66({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_66));
    __VLS_asFunctionalElement1(__VLS_intrinsics.button, __VLS_intrinsics.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.previewImage))
                    return;
                __VLS_ctx.previewImage = null;
                // @ts-ignore
                [previewImage, previewImage, previewImage, imageFileName,];
            } },
        ...{ class: "icon-btn" },
        type: "button",
        title: "关闭预览",
    });
    /** @type {__VLS_StyleScopedClasses['icon-btn']} */ ;
    let __VLS_70;
    /** @ts-ignore @type { | typeof __VLS_components.X} */
    X;
    // @ts-ignore
    const __VLS_71 = __VLS_asFunctionalComponent1(__VLS_70, new __VLS_70({
        size: (18),
    }));
    const __VLS_72 = __VLS_71({
        size: (18),
    }, ...__VLS_functionalComponentArgsRest(__VLS_71));
    __VLS_asFunctionalElement1(__VLS_intrinsics.img)({
        src: (__VLS_ctx.previewImage.url),
        alt: "大图预览",
    });
}
// @ts-ignore
[previewImage,];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
//# sourceMappingURL=App.vue.js.map