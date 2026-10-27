<template>
  <div class="rich-text-editor">
    <div class="rich-text-toolbar">
      <select aria-label="段落样式" @change="formatText('formatBlock', $event.target.value)">
        <option value="P">正文</option>
        <option value="H2">标题</option>
        <option value="H3">副标题</option>
      </select>
      <select aria-label="字号" @change="formatText('fontSize', $event.target.value)">
        <option value="3">默认</option>
        <option value="2">较小</option>
        <option value="4">较大</option>
      </select>
      <span class="toolbar-divider" />
      <el-button size="small" title="加粗" @click="formatText('bold')"><b>B</b></el-button>
      <el-button size="small" title="斜体" @click="formatText('italic')"><i>I</i></el-button>
      <el-button size="small" title="下划线" @click="formatText('underline')"><u>U</u></el-button>
      <el-button size="small" title="项目符号" @click="formatText('insertUnorderedList')">•</el-button>
      <el-button size="small" title="编号列表" @click="formatText('insertOrderedList')">1.</el-button>
      <el-button size="small" title="插入图片" @mousedown.prevent="saveSelection" @click="imageInput?.click()">图片</el-button>
      <input ref="imageInput" class="image-input" type="file" accept="image/png,image/jpeg,image/gif,image/webp" @change="insertSelectedImage" />
    </div>
    <div
      ref="editor"
      class="rich-text-content"
      contenteditable="true"
      @input="syncValue"
      @paste="handlePaste"
      @mousedown.capture="previewImage"
      @click="previewImage"
      @dblclick="previewImage"
    ></div>

    <el-dialog v-model="previewVisible" title="图片预览" width="80%" append-to-body>
      <img v-if="previewUrl" class="image-preview" :src="previewUrl" alt="备注图片预览" />
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const props = defineProps({
  modelValue: { type: String, default: '' },
  uploadUrl: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])
const editor = ref()
const imageInput = ref()
const savedSelection = ref()
const previewVisible = ref(false)
const previewUrl = ref('')

const isSafeImageSource = (value) => (
  /^data:image\/(png|jpeg|gif|webp);base64,/i.test(value) || /^\/media\//.test(value)
)

// 只允许备注编辑器支持的标签和图片来源，避免保存或展示任意 HTML。
const sanitizeHtml = (html) => {
  const parsed = new DOMParser().parseFromString(html || '', 'text/html')
  const allowedTags = new Set(['B', 'STRONG', 'I', 'EM', 'U', 'UL', 'OL', 'LI', 'P', 'H2', 'H3', 'BR', 'FONT', 'IMG'])
  const cleanNode = (node) => {
    for (const child of [...node.childNodes]) {
      if (child.nodeType !== Node.ELEMENT_NODE) {
        if (child.nodeType !== Node.TEXT_NODE) child.remove()
        continue
      }
      if (['SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'SVG', 'MATH'].includes(child.tagName)) {
        child.remove()
        continue
      }
      if (!allowedTags.has(child.tagName)) {
        cleanNode(child)
        child.replaceWith(...child.childNodes)
        continue
      }
      [...child.attributes].forEach(attribute => {
        const isImageSource = child.tagName === 'IMG' && attribute.name === 'src' && isSafeImageSource(attribute.value)
        const isFontSize = child.tagName === 'FONT' && attribute.name === 'size' && /^[1-7]$/.test(attribute.value)
        if (!isImageSource && !isFontSize) child.removeAttribute(attribute.name)
      })
      if (child.tagName === 'IMG' && !child.hasAttribute('src')) child.remove()
      else cleanNode(child)
    }
  }
  cleanNode(parsed.body)
  return parsed.body.innerHTML
}

const syncValue = () => emit('update:modelValue', sanitizeHtml(editor.value?.innerHTML || ''))

const saveSelection = () => {
  const selection = window.getSelection()
  if (selection?.rangeCount && editor.value?.contains(selection.anchorNode)) {
    savedSelection.value = selection.getRangeAt(0).cloneRange()
  }
}

const restoreSelection = () => {
  if (!editor.value) return
  const selection = window.getSelection()
  selection.removeAllRanges()
  if (savedSelection.value) {
    selection.addRange(savedSelection.value)
    return
  }
  const range = document.createRange()
  range.selectNodeContents(editor.value)
  range.collapse(false)
  selection.addRange(range)
}

const insertImageData = (url) => {
  editor.value?.focus()
  restoreSelection()
  const selection = window.getSelection()
  const range = selection.getRangeAt(0)
  const image = document.createElement('img')
  image.src = url
  image.alt = '备注图片'
  range.deleteContents()
  range.insertNode(image)
  range.setStartAfter(image)
  range.collapse(true)
  selection.removeAllRanges()
  selection.addRange(range)
  syncValue()
}

const uploadImage = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post(props.uploadUrl, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data.url
}

const fileToDataUrl = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(reader.result)
  reader.onerror = reject
  reader.readAsDataURL(file)
})

const readImage = async (file) => {
  if (!file || !file.type.startsWith('image/')) return
  try {
    const url = props.uploadUrl ? await uploadImage(file) : await fileToDataUrl(file)
    insertImageData(url)
  } catch (error) {
    ElMessage.error('图片上传失败，请稍后重试')
    console.error('Upload rich text image failed:', error)
  }
}

const insertSelectedImage = (event) => {
  readImage(event.target.files?.[0])
  event.target.value = ''
}

const handlePaste = (event) => {
  const image = [...(event.clipboardData?.items || [])].find(item => item.type.startsWith('image/'))
  if (!image) return
  event.preventDefault()
  readImage(image.getAsFile())
}

const previewImage = (event) => {
  const image = event.target?.closest?.('img')
  if (!image) return
  event.preventDefault()
  previewUrl.value = image.src
  previewVisible.value = true
}

const formatText = (command, value) => {
  editor.value?.focus()
  document.execCommand(command, false, value)
  syncValue()
}

const uploadEmbeddedImages = async (html) => {
  if (!props.uploadUrl) return sanitizeHtml(html)
  const parsed = new DOMParser().parseFromString(html || '', 'text/html')
  const images = [...parsed.body.querySelectorAll('img')]
    .filter(image => /^data:image\/(png|jpeg|gif|webp);base64,/i.test(image.getAttribute('src') || ''))
  for (const [index, image] of images.entries()) {
    const response = await fetch(image.getAttribute('src'))
    const blob = await response.blob()
    const extension = blob.type.split('/')[1] || 'png'
    const file = new File([blob], `notes-image-${Date.now()}-${index}.${extension}`, { type: blob.type })
    image.setAttribute('src', await uploadImage(file))
  }
  return sanitizeHtml(parsed.body.innerHTML)
}

defineExpose({ uploadEmbeddedImages })

watch(() => props.modelValue, (value) => {
  if (editor.value && editor.value.innerHTML !== value) editor.value.innerHTML = sanitizeHtml(value)
})

onMounted(() => {
  editor.value.innerHTML = sanitizeHtml(props.modelValue)
})
</script>

<style scoped>
.rich-text-editor { width: 100%; border: 1px solid #dcdfe6; border-radius: 4px; }
.rich-text-toolbar { display: flex; align-items: center; gap: 5px; padding: 6px; border-bottom: 1px solid #dcdfe6; }
.rich-text-toolbar select { height: 26px; border: 0; background: transparent; color: #606266; }
.toolbar-divider { height: 20px; border-left: 1px solid #dcdfe6; margin: 0 4px; }
.image-input { display: none; }
.rich-text-content { min-height: 180px; padding: 10px; outline: none; }
.rich-text-content:focus { border-color: #409eff; }
.rich-text-content :deep(img) { max-width: min(480px, 100%); max-height: 320px; height: auto; object-fit: contain; cursor: zoom-in; }
.image-preview { display: block; max-width: 100%; max-height: 75vh; margin: 0 auto; object-fit: contain; }
</style>
