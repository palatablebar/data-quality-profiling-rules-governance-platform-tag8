<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-40 flex items-center justify-center bg-paper/70">
      <div class="w-[420px] border border-rule bg-paper px-6 py-5">
        <div class="eyebrow">confirm</div>
        <h3 class="display !text-[18px] mt-1">{{ title }}</h3>
        <p class="mt-2 text-[12.5px] text-ink-soft">{{ message }}</p>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn" @click="$emit('cancel')">取消</button>
          <button class="btn btn-solid" @click="$emit('confirm')">确认</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ open: boolean; title: string; message: string }>()
defineEmits<{ confirm: []; cancel: [] }>()
</script>
