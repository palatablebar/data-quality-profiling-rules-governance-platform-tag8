<template>
  <div>
    <div class="flex items-baseline justify-between">
      <span class="label">扫描配额</span>
      <span class="text-[11px] tabular-nums">{{ used }} / {{ total }}</span>
    </div>
    <div class="mt-1 h-[3px] bg-rule relative overflow-hidden">
      <div class="absolute left-0 top-0 h-[3px]" :style="{ width: width, background: 'var(--assay)' }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { QuotaSnapshot } from '../../types/user'

const props = defineProps<{ quota: QuotaSnapshot | null }>()
const used = computed(() => props.quota?.quota_used ?? 0)
const total = computed(() => props.quota?.daily_scan_quota ?? 0)
const width = computed(() => {
  if (!total.value) return '0%'
  return `${Math.min(100, (used.value / total.value) * 100)}%`
})
</script>
