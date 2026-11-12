<template>
  <div class="border border-rule">
    <div class="px-2 py-1.5 border-b border-rule">
      <input v-model="keyword" class="w-full bg-transparent outline-none text-[12px]" placeholder="搜索列名…" />
    </div>
    <ul class="max-h-[220px] overflow-y-auto">
      <li v-for="column in filtered" :key="column.column_name">
        <button
          class="w-full text-left px-2 py-1.5 flex items-center gap-2 hover:bg-paper-2"
          :class="{ 'bg-paper-2': modelValue === column.column_name }"
          @click="$emit('update:modelValue', column.column_name)"
        >
          <span class="text-[10px] text-ink-soft w-[30px] shrink-0">{{ column.type_label }}</span>
          <span class="text-[12px] flex-1 truncate tabular-nums">{{ column.column_name }}</span>
          <span class="text-[10px] text-ink-soft tabular-nums">{{ (column.null_rate * 100).toFixed(1) }}%</span>
        </button>
      </li>
      <li v-if="!filtered.length" class="px-2 py-3 text-[11.5px] text-ink-soft">没有匹配的列</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface PickerColumn {
  column_name: string
  type_label: string
  null_rate: number
}

const props = defineProps<{ columns: PickerColumn[]; modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
const keyword = ref('')

const filtered = computed(() =>
  props.columns.filter((column) => column.column_name.toLowerCase().includes(keyword.value.toLowerCase())),
)
</script>
