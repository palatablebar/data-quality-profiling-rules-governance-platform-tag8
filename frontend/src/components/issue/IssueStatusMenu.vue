<template>
  <div class="flex flex-wrap gap-1.5">
    <button
      v-for="status in ISSUE_STATUS_LIST"
      :key="status"
      class="btn !py-1 !text-[11px]"
      :class="{ 'btn-solid': current === status }"
      :disabled="current === status"
      @click="$emit('change', status)"
    >
      {{ ISSUE_STATUS_LABELS[status] }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ISSUE_STATUS_LABELS, ISSUE_STATUS_LIST } from '../../constants/issueStatus'

defineProps<{ current: string }>()
defineEmits<{ change: [status: string] }>()
</script>
