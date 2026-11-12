<template>
  <div class="border border-rule bg-paper-2 px-3 py-2 text-[11.5px] text-ink-soft">
    <span class="stamp mr-2" :style="{ color: 'var(--low)' }">read only</span>{{ message }}
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ message?: string }>(), {
  message: '当前角色为审计（viewer），仅有查看权限：上传、建规则、执行与指派均不可用。',
})
</script>
