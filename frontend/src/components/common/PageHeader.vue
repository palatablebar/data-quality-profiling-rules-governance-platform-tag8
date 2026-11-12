<template>
  <header class="pb-4">
    <div class="flex items-start justify-between gap-6">
      <div class="min-w-0">
        <div class="eyebrow">{{ eyebrow }}</div>
        <h1 class="display mt-1">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1 text-[12.5px] text-ink-soft">{{ subtitle }}</p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <slot name="actions" />
      </div>
    </div>
    <dl v-if="meta && meta.length" class="mt-4 flex flex-wrap gap-x-9 gap-y-2">
      <div v-for="item in meta" :key="item.label" class="flex items-baseline gap-2">
        <dt class="label">{{ item.label }}</dt>
        <dd class="text-[12.5px] tabular-nums">{{ item.value }}</dd>
      </div>
    </dl>
    <div class="hr mt-4"></div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
  subtitle?: string
  meta?: Array<{ label: string; value: string }>
}>()
</script>
