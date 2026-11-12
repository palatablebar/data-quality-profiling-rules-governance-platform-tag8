<template>
  <ul>
    <li
      v-for="(item, index) in items"
      :key="item.id"
      class="flex items-center gap-3 py-[7px] border-b border-dashed border-rule"
    >
      <span
        class="w-[12px] h-[12px] border shrink-0"
        :class="{ 'tick-enter': item.passed || item.error_code }"
        :style="boxStyle(item, index)"
      ></span>
      <span class="text-[12.5px] w-[190px] truncate" :class="item.passed ? '' : 'text-ink'" :style="item.passed ? { opacity: 0.72 } : {}">
        {{ item.rule_name }}
      </span>
      <span class="text-[10.5px] text-ink-soft w-[86px] shrink-0">{{ item.column_name }}</span>
      <SeverityBadge :severity="item.severity" class="w-[52px] shrink-0" />
      <span class="text-[11px] tabular-nums w-[86px] text-right shrink-0">
        <template v-if="item.error_code">
          <span :style="{ color: 'var(--alert-deep)' }">{{ item.error_code }}</span>
        </template>
        <template v-else>{{ item.violation_count }} 违规</template>
      </span>
      <span class="text-[10.5px] text-ink-soft tabular-nums w-[62px] text-right shrink-0">{{ item.duration_display }}</span>
      <button v-if="!item.passed && !item.error_code" class="link-button text-[11px] ml-auto shrink-0" @click="$emit('drill', item)">
        查看违规 →
      </button>
      <span v-else class="ml-auto"></span>
    </li>
    <li v-if="!items.length" class="py-3 text-[12px] text-ink-soft">本批次没有逐条规则结果</li>
  </ul>
</template>

<script setup lang="ts">
import SeverityBadge from '../common/SeverityBadge.vue'
import type { RunItem } from '../../types/run'

defineProps<{ items: RunItem[]; runStatus?: string }>()
defineEmits<{ drill: [item: RunItem] }>()

function boxStyle(item: RunItem, index: number) {
  const finished = item.passed
  return {
    borderColor: item.error_code ? 'var(--alert-deep)' : finished ? 'var(--assay)' : 'var(--rule-line)',
    background: finished ? 'color-mix(in oklch, var(--assay) 20%, var(--paper))' : 'transparent',
    animationDelay: `${Math.min(index * 90, 900)}ms`,
  }
}
</script>
