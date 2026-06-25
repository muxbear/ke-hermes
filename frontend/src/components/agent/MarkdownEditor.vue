<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import { Edit3, Eye, Save, FileText, Lock } from 'lucide-vue-next'

const props = defineProps<{
  content: string
  filename: string | null
  loading: boolean
  readOnly?: boolean
}>()

const emit = defineEmits<{
  (e: 'save', content: string): void
  (e: 'update:content', content: string): void
}>()

const editContent = ref('')
const viewMode = ref<'edit' | 'preview'>(props.readOnly ? 'preview' : 'edit')
const dirty = ref(false)

watch(
  () => props.content,
  (val) => {
    editContent.value = val
    dirty.value = false
  },
)

watch(
  () => props.readOnly,
  (val) => {
    if (val) viewMode.value = 'preview'
  },
)

function onInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  editContent.value = target.value
  dirty.value = target.value !== props.content
}

function onSave() {
  emit('save', editContent.value)
  dirty.value = false
}

function toggleMode(mode: 'edit' | 'preview') {
  if (props.readOnly && mode === 'edit') return
  viewMode.value = mode
}

const renderedHtml = computed(() => {
  if (!editContent.value) return '<p style="color: var(--foreground-muted);">暂无内容</p>'
  return marked.parse(editContent.value, { breaks: true }) as string
})
</script>

<template>
  <div class="markdown-editor">
    <!-- No file selected -->
    <div v-if="!filename" class="editor-empty">
      <FileText :size="32" class="empty-icon" />
      <p class="empty-title">请选择一个文件进行编辑</p>
      <span class="empty-hint">点击上方文件标签开始编辑内容</span>
    </div>

    <!-- Editor with toolbar -->
    <template v-else>
      <div class="editor-toolbar">
        <div class="toolbar-left">
          <span v-if="readOnly" class="readonly-indicator">
            <Lock :size="11" />
            只读
          </span>
          <span v-else-if="dirty" class="dirty-indicator">未保存</span>
        </div>
        <div class="toolbar-right">
          <div class="mode-toggle">
            <button
              v-if="!readOnly"
              class="mode-btn"
              :class="{ active: viewMode === 'edit' }"
              @click="toggleMode('edit')"
            >
              <Edit3 :size="13" />
              编辑
            </button>
            <button
              class="mode-btn"
              :class="{ active: viewMode === 'preview' }"
              @click="toggleMode('preview')"
            >
              <Eye :size="13" />
              预览
            </button>
          </div>
          <button v-if="!readOnly" class="save-btn" :disabled="!dirty" @click="onSave">
            <Save :size="13" />
            保存
          </button>
        </div>
      </div>

      <div class="editor-body" v-loading="loading">
        <!-- Edit mode -->
        <textarea
          v-if="viewMode === 'edit' && !readOnly"
          class="editor-textarea"
          :value="editContent"
          @input="onInput"
          placeholder="在此编辑 Markdown 内容..."
          spellcheck="false"
        />

        <!-- Preview mode -->
        <div
          v-else
          class="editor-preview"
          v-html="renderedHtml"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.markdown-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-card);
  overflow: hidden;
}

/* ---- Empty state ---- */
.editor-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--foreground-muted);
  gap: 6px;
}

.empty-icon {
  opacity: 0.3;
}

.empty-title {
  font-size: var(--font-size-sm);
  margin: 0;
}

.empty-hint {
  font-size: var(--font-size-xs);
}

/* ---- Toolbar ---- */
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.toolbar-file-icon {
  color: #eab308;
  flex-shrink: 0;
}

.toolbar-filename {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dirty-indicator {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
  flex-shrink: 0;
}

.readonly-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(107, 114, 128, 0.15);
  color: #9ca3af;
  flex-shrink: 0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.mode-toggle {
  display: flex;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  background: transparent;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.mode-btn.active {
  background: rgba(255, 255, 255, 0.06);
  color: var(--foreground-primary);
}

.mode-btn:hover:not(.active) {
  color: var(--foreground-secondary);
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: var(--radius-lg);
  background: transparent;
  font-size: var(--font-size-xs);
  color: #eab308;
  cursor: pointer;
  transition: all 0.15s ease;
}

.save-btn:hover:not(:disabled) {
  background: rgba(234, 179, 8, 0.1);
}

.save-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---- Editor body ---- */
.editor-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.editor-textarea {
  width: 100%;
  height: 100%;
  padding: 16px;
  border: none;
  background: transparent;
  color: var(--foreground-primary);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: var(--font-size-sm);
  line-height: 1.6;
  resize: none;
  outline: none;
  tab-size: 2;
}

.editor-textarea::placeholder {
  color: var(--foreground-muted);
}

/* ---- Preview ---- */
.editor-preview {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.editor-preview :deep(h1) {
  font-size: 1.5em;
  margin: 0 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-subtle);
}

.editor-preview :deep(h2) {
  font-size: 1.3em;
  margin: 20px 0 8px;
}

.editor-preview :deep(h3) {
  font-size: 1.1em;
  margin: 16px 0 6px;
}

.editor-preview :deep(p) {
  margin: 8px 0;
}

.editor-preview :deep(code) {
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.editor-preview :deep(pre) {
  background: rgba(255, 255, 255, 0.04);
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  overflow-x: auto;
}

.editor-preview :deep(pre code) {
  background: none;
  padding: 0;
  border-radius: 0;
}

.editor-preview :deep(ul),
.editor-preview :deep(ol) {
  padding-left: 20px;
}

.editor-preview :deep(li) {
  margin: 4px 0;
}

.editor-preview :deep(blockquote) {
  border-left: 3px solid #eab308;
  padding-left: 12px;
  margin: 12px 0;
  color: var(--foreground-secondary);
}

.editor-preview :deep(a) {
  color: var(--color-accent);
  text-decoration: none;
}

.editor-preview :deep(a:hover) {
  text-decoration: underline;
}

.editor-preview :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.editor-preview :deep(th),
.editor-preview :deep(td) {
  border: 1px solid var(--border-subtle);
  padding: 6px 12px;
  text-align: left;
}

.editor-preview :deep(th) {
  background: rgba(255, 255, 255, 0.04);
  font-weight: var(--font-weight-semibold);
}

.editor-preview :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 16px 0;
}
</style>
