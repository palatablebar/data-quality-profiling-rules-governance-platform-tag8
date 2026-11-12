<template>
  <dl class="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-3">
    <div v-for="item in rows" :key="item.label">
      <dt class="label">{{ item.label }}</dt>
      <dd class="text-[12.5px] mt-0.5 tabular-nums break-all">{{ item.value }}</dd>
    </div>
  </dl>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Dataset } from '../../types/dataset'
import { formatBytes, formatInt, shortChecksum } from '../../utils/formatters'

const props = defineProps<{ dataset: Dataset }>()
const rows = computed(() => [
  { label: '文件名', value: props.dataset.name },
  { label: '格式', value: props.dataset.source_format },
  { label: '行数', value: formatInt(props.dataset.row_count) },
  { label: '列数', value: String(props.dataset.column_count) },
  { label: '文件大小', value: formatBytes(props.dataset.file_size) },
  { label: '校验和', value: shortChecksum(props.dataset.checksum) },
  { label: '上传时间', value: props.dataset.uploaded_at ?? '-' },
  { label: '状态', value: props.dataset.status },
])
</script>
