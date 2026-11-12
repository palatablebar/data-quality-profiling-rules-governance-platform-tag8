<template>
  <tr class="align-top">
    <td class="w-[26px]">
      <button
        class="w-[13px] h-[13px] border mt-[2px]"
        :style="{ borderColor: rule.is_active ? 'var(--assay)' : 'var(--rule-line)', background: rule.is_active ? 'color-mix(in oklch, var(--assay) 18%, var(--paper))' : 'transparent' }"
        :title="rule.is_active ? '停用规则' : '启用规则'"
        @click="$emit('toggle', rule.id, !rule.is_active)"
      ></button>
    </td>
    <td>
      <div class="text-[12.5px]">{{ rule.name }}</div>
      <div class="text-[10.5px] text-ink-soft mt-0.5">{{ rule.rule_type_label }} · {{ rule.column_name }}</div>
    </td>
    <td class="text-[11.5px] text-ink-soft">{{ rule.param_summary }}</td>
    <td><SeverityBadge :severity="rule.severity" /></td>
    <td class="num text-[11.5px]">{{ rule.sample_limit }}</td>
    <td class="num whitespace-nowrap">
      <button class="link-button text-[11px] mr-3" @click="$emit('edit', rule)">编辑</button>
      <button class="link-button text-[11px]" :style="{ color: 'var(--alert-deep)' }" @click="$emit('remove', rule.id)">删除</button>
    </td>
  </tr>
</template>

<script setup lang="ts">
import SeverityBadge from '../common/SeverityBadge.vue'
import type { QualityRule } from '../../types/rule'

defineProps<{ rule: QualityRule }>()
defineEmits<{ edit: [rule: QualityRule]; toggle: [id: number, active: boolean]; remove: [id: number] }>()
</script>
