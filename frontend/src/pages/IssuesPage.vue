<template>
  <div class="paper-page">
    <PageHeader
      eyebrow="triage board"
      title="问题分诊板"
      subtitle="每条违规都带 row_index 与 observed_value，能凭这两项回到原始文件定位。"
      :meta="meta"
    >
      <template #actions>
        <button class="btn" :disabled="!auth.canWrite || !selectedIds.length" @click="assignSelected">批量指派给分析师</button>
      </template>
    </PageHeader>

    <PermissionNotice v-if="!auth.canWrite" class="mb-3" />

    <IssueFilterBar :filters="filters" :datasets="datasetStore.items" :total="issueStore.total" @apply="apply" @reset="reset" />

    <div v-if="issueStore.summary" class="flex flex-wrap items-baseline gap-6 py-2 text-[11px] text-ink-soft">
      <span>严重度分布：</span>
      <span v-for="severity in SEVERITY_LIST" :key="severity" class="tabular-nums">
        {{ SEVERITY_LABELS[severity] }} {{ issueStore.summary.by_severity[severity] ?? 0 }}
      </span>
      <span class="ml-4">状态：</span>
      <span v-for="status in ISSUE_STATUS_LIST" :key="status" class="tabular-nums">
        {{ ISSUE_STATUS_LABELS[status] }} {{ issueStore.summary.by_status[status] ?? 0 }}
      </span>
    </div>

    <ErrorNotice :error="issueStore.error" />

    <table v-if="issueStore.items.length" class="table-base mt-1">
      <thead>
        <tr>
          <th class="w-[24px]"><input type="checkbox" :checked="allSelected" @change="toggleAll" /></th>
          <th class="w-[60px]">严重度</th>
          <th>规则 / 列</th>
          <th class="w-[70px] text-right">row_index</th>
          <th class="w-[200px]">observed_value</th>
          <th class="w-[92px]">状态</th>
          <th class="w-[96px]">跟进人</th>
          <th class="w-[70px]"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="issue in issueStore.items" :key="issue.id" class="cursor-pointer" @click="open(issue)">
          <td @click.stop><input v-model="selectedIds" type="checkbox" :value="issue.id" /></td>
          <td><SeverityBadge :severity="issue.severity" /></td>
          <td>
            <div class="text-[12px]">{{ issue.rule_name ?? '-' }}</div>
            <div class="text-[10.5px] text-ink-soft">{{ issue.column_name }}</div>
          </td>
          <td class="num">{{ issue.row_index }}</td>
          <td class="tabular-nums text-[11.5px] break-all">
            <span v-if="issue.observed_value === ''" class="text-ink-soft">（空）</span>
            <span v-else>{{ issue.observed_value }}</span>
          </td>
          <td class="text-[11.5px]">{{ ISSUE_STATUS_LABELS[issue.status] }}</td>
          <td class="text-[11.5px]">{{ issue.assignee_name ?? '-' }}</td>
          <td class="num"><button class="link-button text-[11px]" @click.stop="open(issue)">明细 →</button></td>
        </tr>
      </tbody>
    </table>

    <EmptyState
      v-else-if="!issueStore.loading"
      class="mt-6"
      title="分诊板是空的"
      :description="MESSAGES.issueEmptyHint"
    >
      <RouterLink to="/runs" class="btn">去看执行台账</RouterLink>
    </EmptyState>

    <div class="mt-8 border-t border-rule pt-3 text-[10.5px] text-ink-soft">
      共 {{ issueStore.total }} 条问题单 · 当前筛选：{{ filterSummary }}
    </div>

    <IssueDrawer
      :issue="issueStore.selected"
      :users="issueStore.users"
      @close="issueStore.select(null)"
      @update="onUpdate"
    />
    <ActivityTrail />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '../components/common/PageHeader.vue'
import SeverityBadge from '../components/common/SeverityBadge.vue'
import IssueFilterBar from '../components/issue/IssueFilterBar.vue'
import IssueDrawer from '../components/issue/IssueDrawer.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import ActivityTrail from '../components/common/ActivityTrail.vue'
import { useIssueStore } from '../stores/issueStore'
import { useDatasetStore } from '../stores/datasetStore'
import { useAuthStore } from '../stores/authStore'
import { useIssueFilter } from '../hooks/useIssueFilter'
import { ISSUE_STATUS_LABELS, ISSUE_STATUS_LIST } from '../constants/issueStatus'
import { SEVERITY_LABELS, SEVERITY_LIST } from '../constants/severity'
import { MESSAGES } from '../constants/messages'
import type { Issue } from '../types/issue'

const route = useRoute()
const issueStore = useIssueStore()
const datasetStore = useDatasetStore()
const auth = useAuthStore()
const selectedIds = ref<number[]>([])
const { filters, apply, reset } = useIssueFilter({
  dataset_id: route.query.dataset ? Number(route.query.dataset) : null,
  rule_id: route.query.rule ? Number(route.query.rule) : null,
})

const meta = computed(() => [
  { label: '问题总数', value: String(issueStore.summary?.total ?? issueStore.total) },
  { label: '严重', value: String(issueStore.summary?.by_severity.critical ?? 0) },
  { label: '高', value: String(issueStore.summary?.by_severity.high ?? 0) },
  { label: '待分诊', value: String(issueStore.summary?.by_status.open ?? 0) },
])

const allSelected = computed(() => issueStore.items.length > 0 && selectedIds.value.length === issueStore.items.length)

const filterSummary = computed(() => {
  const parts = []
  if (filters.dataset_id) parts.push(`数据集 #${filters.dataset_id}`)
  if (filters.severity) parts.push(`严重度 ${SEVERITY_LABELS[filters.severity] ?? filters.severity}`)
  if (filters.status) parts.push(`状态 ${ISSUE_STATUS_LABELS[filters.status] ?? filters.status}`)
  return parts.length ? parts.join(' · ') : '全部'
})

onMounted(async () => {
  if (!datasetStore.items.length) await datasetStore.load()
  await issueStore.loadUsers()
  issueStore.filters = { ...filters }
  await issueStore.load()
})

function toggleAll() {
  selectedIds.value = allSelected.value ? [] : issueStore.items.map((issue) => issue.id)
}

async function open(issue: Issue) {
  issueStore.select(issue)
}

async function onUpdate(payload: { status?: string; assignee_id?: number | null; note?: string }) {
  if (!issueStore.selected) return
  await issueStore.update(issueStore.selected.id, payload)
}

async function assignSelected() {
  const analyst = issueStore.users.find((user) => user.role === 'analyst')
  await issueStore.assignMany(selectedIds.value, analyst?.id ?? null)
  selectedIds.value = []
}
</script>
