<template>
  <div class="text-[11px] text-ink-soft leading-relaxed">
    <span class="label mr-2">模式</span>
    <span class="tabular-nums break-all">{{ summary || 'unknown' }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{ summary: string | null }>()
</script>
