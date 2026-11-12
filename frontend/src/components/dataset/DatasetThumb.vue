<template>
  <div class="w-[96px] border border-rule bg-paper px-2 py-1.5 -rotate-1 shrink-0">
    <div class="eyebrow !text-[9px]">{{ dataset.source_format.toUpperCase() }}</div>
    <div class="font-display text-[14px] leading-tight truncate" :title="dataset.name">{{ shortName }}</div>
    <div class="text-[10px] text-ink-soft mt-0.5 tabular-nums">
      {{ dataset.row_count_display }} × {{ dataset.column_count }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Dataset } from '../../types/dataset'

const props = defineProps<{ dataset: Dataset }>()
const shortName = computed(() => props.dataset.name.replace(/\.(csv|parquet|jsonl|xlsx)$/i, ''))
</script>
