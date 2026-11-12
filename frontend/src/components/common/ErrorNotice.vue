<template>
  <div v-if="message" class="border-l-2 pl-3 py-2 my-2" :style="{ borderColor: 'var(--alert)' }">
    <div class="flex items-start justify-between gap-4">
      <div>
        <div class="text-[12.5px]" :style="{ color: 'var(--alert-deep)' }">
          <span class="stamp mr-2">{{ code }}</span>{{ message }}
        </div>
        <div v-if="hint" class="text-[11.5px] text-ink-soft mt-1">{{ hint }}</div>
        <div v-if="requestId" class="text-[10.5px] text-ink-soft mt-1">request_id {{ requestId }}</div>
      </div>
      <button v-if="retryable" class="btn !py-1" @click="$emit('retry')">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ERROR_CODES } from '../../constants/errorCodes'
import type { ApiError } from '../../types/api'

const props = defineProps<{ error: ApiError | string | null; retryable?: boolean }>()
defineEmits<{ retry: [] }>()

const code = computed(() => (typeof props.error === 'object' && props.error ? props.error.code : 'QUAL-5000'))
const message = computed(() => {
  if (!props.error) return ''
  if (typeof props.error === 'string') return props.error
  return props.error.message
})
const hint = computed(() => ERROR_CODES[code.value]?.hint ?? '')
const requestId = computed(() => (typeof props.error === 'object' && props.error ? props.error.requestId : null))
</script>
