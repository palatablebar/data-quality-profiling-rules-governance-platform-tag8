<template>
  <div class="min-w-[190px]">
    <div class="flex items-center gap-2">
      <div class="flex-1 h-[5px] bg-rule relative overflow-hidden">
        <div class="absolute inset-y-0 left-0" :style="{ width: nullWidth, background: 'var(--alert)' }"></div>
      </div>
      <span class="text-[10.5px] tabular-nums text-ink-soft w-[42px] text-right">{{ nullDisplay }}</span>
    </div>
    <div class="mt-1 text-[10.5px] text-ink-soft tabular-nums">
      基数 {{ distinctDisplay }} · 异常 {{ outliers }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ nullRate: number; nullDisplay: string; distinctDisplay: string; outliers: number }>()
const nullWidth = computed(() => `${Math.min(100, Math.max(2, props.nullRate * 100))}%`)
</script>
