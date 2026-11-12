<template>
  <span class="inline-flex items-center gap-1.5 whitespace-nowrap" :style="{ color: tone.color }">
    <span class="inline-block" :style="markStyle"></span>
    <span class="text-[11px]">{{ tone.label }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { severityTone } from '../../utils/severityTone'

const props = defineProps<{ severity: string }>()
const tone = computed(() => severityTone(props.severity))
const markStyle = computed(() => {
  switch (tone.value.shape) {
    case 'block':
      return { width: '6px', height: '10px', background: tone.value.color }
    case 'double-bar':
      return { width: '6px', height: '10px', borderLeft: `2px solid ${tone.value.color}`, borderRight: `2px solid ${tone.value.color}` }
    case 'bar':
      return { width: '2px', height: '10px', background: tone.value.color }
    default:
      return { width: '6px', height: '1px', background: tone.value.color, marginTop: '4px' }
  }
})
</script>
