<template>
  <select class="input" :value="modelValue" @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)">
    <option v-for="severity in SEVERITY_LIST" :key="severity" :value="severity">
      {{ SEVERITY_LABELS[severity] }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { SEVERITY_LABELS, SEVERITY_LIST } from '../../constants/severity'

defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>
