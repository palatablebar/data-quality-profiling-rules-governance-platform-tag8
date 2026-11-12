<template>
  <div class="min-w-[190px]">
    <div class="relative h-[14px]">
      <div class="absolute left-0 right-0 top-[9px] h-[1px] bg-rule"></div>
      <div v-for="mark in marks" :key="mark.label" class="absolute top-0" :style="{ left: mark.left }">
        <div class="h-[7px] w-[1px]" :style="{ background: mark.color }"></div>
        <div class="text-[9.5px] tabular-nums -translate-x-1/2 mt-[1px]" :style="{ color: mark.color }">
          {{ mark.label }}
        </div>
      </div>
    </div>
    <div class="flex justify-between text-[9.5px] text-ink-soft tabular-nums mt-1">
      <span>{{ minDisplay }}</span><span>{{ maxDisplay }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  min: string | null
  max: string | null
  p50: string
  p95: string
  positions: { p50: number | null; p95: number | null }
}>()

const minDisplay = computed(() => props.min ?? '-')
const maxDisplay = computed(() => props.max ?? '-')
const marks = computed(() => {
  if (props.positions.p50 === null || props.positions.p95 === null) return []
  return [
    { label: `p50 ${props.p50}`, left: `${props.positions.p50 * 100}%`, color: 'var(--ink-soft)' },
    { label: `p95 ${props.p95}`, left: `${props.positions.p95 * 100}%`, color: 'var(--assay)' },
  ]
})
</script>
