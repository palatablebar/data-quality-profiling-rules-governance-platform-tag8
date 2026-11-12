<template>
  <div class="scroll-x">
    <table class="table-base">
      <thead>
        <tr>
          <th class="w-[26px]"></th>
          <th>列名</th>
          <th class="w-[78px]">类型</th>
          <th class="w-[220px]">空值率 / 基数</th>
          <th class="w-[220px]">分位刻度</th>
          <th class="w-[90px]">Top 值</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="column in columns" :key="column.id">
          <tr class="cursor-pointer" @click="toggle(column.column_name)">
            <td class="text-ink-soft">{{ expanded === column.column_name ? '−' : '+' }}</td>
            <td class="tabular-nums">{{ column.column_name }}</td>
            <td>
              <span class="eyebrow !tracking-normal">{{ column.type_label }}</span>
            </td>
            <td><ProfileBar :null-rate="column.null_rate" :null-display="column.null_rate_display" :distinct-display="column.distinct_display" :outliers="column.outlier_count" /></td>
            <td><PercentileScale :min="column.min_value" :max="column.max_value" :p50="column.p50_display" :p95="column.p95_display" :positions="column.percentile_positions" /></td>
            <td class="num">{{ column.top_values.length }}</td>
            <td class="num">
              <button class="link-button text-[11px]" @click.stop="$emit('pick', column.column_name)">加入规则 →</button>
            </td>
          </tr>
          <tr v-if="expanded === column.column_name">
            <td></td>
            <td colspan="6" class="!py-3">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <PatternSummary :summary="column.pattern_summary" />
                <div v-if="column.top_values.length">
                  <div class="label mb-1">Top 值（最多 10 个）</div>
                  <table class="w-auto">
                    <tr v-for="top in column.top_values" :key="top.value">
                      <td class="pr-6 text-[11.5px] tabular-nums">{{ top.value }}</td>
                      <td class="text-[11.5px] tabular-nums text-ink-soft text-right">{{ top.count }}</td>
                    </tr>
                  </table>
                </div>
                <div v-else class="label">无数值型 Top 值</div>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ProfileBar from './ProfileBar.vue'
import PercentileScale from './PercentileScale.vue'
import PatternSummary from './PatternSummary.vue'
import type { ColumnProfile } from '../../types/profile'

defineProps<{ columns: ColumnProfile[] }>()
defineEmits<{ pick: [columnName: string] }>()
const expanded = ref<string | null>(null)

function toggle(columnName: string) {
  expanded.value = expanded.value === columnName ? null : columnName
}
</script>
