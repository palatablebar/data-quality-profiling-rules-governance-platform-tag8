<template>
  <span class="stamp" :style="{ color: color }">{{ RUN_STATUS_LABELS[status] ?? status }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RUN_STATUS_LABELS } from '../../constants/ruleRunStatus'

const props = defineProps<{ status: string }>()
const color = computed(() => {
  if (props.status === 'succeeded') return 'var(--assay)'
  if (props.status === 'failed') return 'var(--alert-deep)'
  if (props.status === 'running') return 'var(--ink)'
  return 'var(--ink-soft)'
})
</script>
