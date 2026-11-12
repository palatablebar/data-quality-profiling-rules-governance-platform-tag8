<template>
  <div
    class="border border-dashed border-rule px-5 py-4 bg-paper-2/40"
    :style="dragging ? { borderColor: 'var(--assay)' } : {}"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="text-[12.5px]">上传标本文件</div>
        <div class="text-[11.5px] text-ink-soft mt-1">
          支持 .csv / .parquet / .jsonl / .xlsx，首行为表头，单列不要重名，建议不超过 20 万行
        </div>
      </div>
      <label class="btn cursor-pointer" :class="{ 'opacity-40 pointer-events-none': uploading }">
        {{ uploading ? '上传中…' : '选择文件' }}
        <input type="file" class="hidden" accept=".csv,.parquet,.jsonl,.xlsx" @change="onPick" />
      </label>
    </div>
    <ErrorNotice :error="error" @retry="error = null" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ErrorNotice from '../common/ErrorNotice.vue'
import type { ApiError } from '../../types/api'

const props = defineProps<{ uploading: boolean }>()
const emit = defineEmits<{ upload: [file: File] }>()
const dragging = ref(false)
const error = ref<ApiError | string | null>(null)

function onPick(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) submit(file)
  input.value = ''
}

function onDrop(event: DragEvent) {
  dragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) submit(file)
}

function submit(file: File) {
  error.value = null
  const name = file.name.toLowerCase()
  if (!/\.(csv|parquet|jsonl|xlsx)$/.test(name)) {
    error.value = { code: 'QUAL-2002', message: '仅支持 .csv / .parquet / .jsonl / .xlsx' }
    return
  }
  if (file.size > (props.uploading ? 0 : 64 * 1024 * 1024)) {
    error.value = { code: 'QUAL-2005', message: '文件超过 64MB 上限，请抽样后再上传' }
    return
  }
  emit('upload', file)
}
</script>
