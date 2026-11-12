<template>
  <div class="border border-dashed border-rule px-8 py-10 text-center">
    <div class="mx-auto w-[150px] border border-rule bg-paper-2 px-3 py-2 text-left">
      <div class="eyebrow">specimen no.</div>
      <div class="mt-2 h-[1px] bg-rule"></div>
      <div class="mt-2 h-[1px] bg-rule"></div>
      <div class="mt-2 h-[1px] w-2/3 bg-rule"></div>
    </div>
    <h2 class="display mt-5 !text-[19px]">{{ title }}</h2>
    <p class="mt-2 text-[12.5px] text-ink-soft max-w-[460px] mx-auto">{{ description }}</p>
    <p v-if="hint" class="mt-1 text-[11.5px] text-ink-soft">{{ hint }}</p>
    <div class="mt-4"><slot /></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; description: string; hint?: string }>()
</script>
