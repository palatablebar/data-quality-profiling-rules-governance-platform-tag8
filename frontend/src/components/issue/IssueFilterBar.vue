<template>
  <div class="flex flex-wrap items-end gap-4 py-3 border-b border-rule">
    <div>
      <div class="label mb-1">数据集</div>
      <select v-model="filters.dataset_id" class="input !w-[190px]" @change="$emit('apply')">
        <option :value="null">全部数据集</option>
        <option v-for="dataset in datasets" :key="dataset.id" :value="dataset.id">{{ dataset.name }}</option>
      </select>
    </div>
    <div>
      <div class="label mb-1">严重度</div>
      <select v-model="filters.severity" class="input !w-[120px]" @change="$emit('apply')">
        <option :value="null">全部</option>
        <option v-for="severity in SEVERITY_LIST" :key="severity" :value="severity">{{ SEVERITY_LABELS[severity] }}</option>
      </select>
    </div>
    <div>
      <div class="label mb-1">状态</div>
      <select v-model="filters.status" class="input !w-[120px]" @change="$emit('apply')">
        <option :value="null">全部</option>
        <option v-for="status in ISSUE_STATUS_LIST" :key="status" :value="status">{{ ISSUE_STATUS_LABELS[status] }}</option>
      </select>
    </div>
    <button class="btn" @click="$emit('reset')">重置筛选</button>
    <span class="text-[11px] text-ink-soft ml-auto tabular-nums">命中 {{ total }} 条</span>
  </div>
</template>

<script setup lang="ts">
import { SEVERITY_LABELS, SEVERITY_LIST } from '../../constants/severity'
import { ISSUE_STATUS_LABELS, ISSUE_STATUS_LIST } from '../../constants/issueStatus'
import type { Dataset } from '../../types/dataset'
import type { IssueFilterState } from '../../stores/issueStore'

defineProps<{ filters: IssueFilterState; datasets: Dataset[]; total: number }>()
defineEmits<{ apply: []; reset: [] }>()
</script>
