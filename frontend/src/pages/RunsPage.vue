<template>
  <div class="paper-page">
    <PageHeader
      eyebrow="run ledger"
      title="执行台账"
      subtitle="每次批量执行都是一个可归档的批次：逐条规则打勾、失败规则下钻到违规样本。"
      :meta="meta"
    >
      <template #actions>
        <select v-model="datasetFilter" class="input !w-[220px]" @change="reloadRuns">
          <option :value="null">全部数据集</option>
          <option v-for="dataset in datasetStore.items" :key="dataset.id" :value="dataset.id">{{ dataset.name }}</option>
        </select>
        <button class="btn" :disabled="!auth.canWrite" @click="runAgain">复跑该数据集规则</button>
      </template>
    </PageHeader>

    <ErrorNotice :error="runStore.error" />

    <div class="grid grid-cols-1 xl:grid-cols-[300px_1fr] gap-8">
      <section>
        <div class="eyebrow mb-2">批次列表</div>
        <ul>
          <li v-for="run in runStore.runs" :key="run.id">
            <button
              class="w-full text-left py-2 border-b border-dashed border-rule"
              :class="{ 'bg-paper-2': runStore.detail?.id === run.id }"
              @click="selectRun(run.id)"
            >
              <div class="flex items-baseline justify-between">
                <span class="text-[12px] tabular-nums">#{{ run.id }} · {{ run.dataset_name }}</span>
                <RunStatusTag :status="run.status" />
              </div>
              <div class="text-[10.5px] text-ink-soft mt-1 tabular-nums">
                {{ run.rules_total }} 规则 · 通过 {{ run.rules_passed }} / 失败 {{ run.rules_failed }} · {{ run.duration_display }}
              </div>
              <div class="text-[10.5px] text-ink-soft tabular-nums">{{ run.finished_at ?? run.started_at ?? '-' }}</div>
            </button>
          </li>
          <li v-if="!runStore.runs.length" class="py-3 text-[12px] text-ink-soft">还没有批次，去规则构建器执行一次。</li>
        </ul>
      </section>

      <section v-if="runStore.detail">
        <div class="flex items-baseline justify-between mb-1">
          <div class="eyebrow">批次 #{{ runStore.detail.id }} · {{ runStore.detail.status === 'succeeded' ? '逐条规则结果' : runStore.detail.status }}</div>
          <div class="flex items-center gap-2">
            <span class="text-[10.5px] text-ink-soft tabular-nums">报告单 {{ runStore.detail.report_no ?? '-' }}</span>
            <button class="btn !py-1" @click="downloadReport">导出报告单</button>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-2 py-3 border-y border-rule">
          <div><div class="label">规则</div><div class="text-[13px] tabular-nums">{{ runStore.detail.rules_total }}</div></div>
          <div><div class="label">通过 / 失败</div><div class="text-[13px] tabular-nums">{{ runStore.detail.rules_passed }} / {{ runStore.detail.rules_failed }}</div></div>
          <div><div class="label">扫描行数</div><div class="text-[13px] tabular-nums">{{ runStore.detail.rows_scanned_display }}</div></div>
          <div><div class="label">违规样本</div><div class="text-[13px] tabular-nums">{{ runStore.detail.issue_count }}</div></div>
        </div>

        <RunProgressList class="mt-3" :items="runStore.detail.items" :run-status="runStore.detail.status" @drill="drill" />

        <p v-if="runStore.detail.status === 'queued' || runStore.detail.status === 'running'" class="mt-3 text-[11.5px] text-ink-soft">
          批次正在执行，逐条规则结果会自动刷新…
        </p>

        <div class="mt-6 border-t border-rule pt-3 flex items-center justify-between text-[10.5px] text-ink-soft">
          <span>数据集 #{{ runStore.detail.dataset_id }} · {{ runStore.detail.dataset_format }}</span>
          <span>耗时 {{ runStore.detail.duration_display }} · 结束于 {{ runStore.detail.finished_at ?? '-' }}</span>
        </div>
        <ActivityTrail />
      </section>
      <section v-else class="py-8 text-[12.5px] text-ink-soft">左侧选择一批执行结果查看逐条规则打勾。</section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '../components/common/PageHeader.vue'
import RunStatusTag from '../components/run/RunStatusTag.vue'
import RunProgressList from '../components/run/RunProgressList.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import ActivityTrail from '../components/common/ActivityTrail.vue'
import { useRunStore } from '../stores/runStore'
import { useDatasetStore } from '../stores/datasetStore'
import { useRuleStore } from '../stores/ruleStore'
import { useAuthStore } from '../stores/authStore'
import { useRunPolling } from '../hooks/useRunPolling'
import { fetchReport } from '../api/run'
import type { RunItem } from '../types/run'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()
const datasetStore = useDatasetStore()
const ruleStore = useRuleStore()
const auth = useAuthStore()
const datasetFilter = ref<number | null>(null)
const polling = useRunPolling()

const meta = computed(() => [
  { label: '批次数', value: String(runStore.runs.length) },
  { label: '最近批次', value: runStore.runs[0] ? `#${runStore.runs[0].id}` : '-' },
  { label: '配额剩余', value: `${runStore.quota?.quota_remaining ?? '-'} / ${runStore.quota?.daily_scan_quota ?? '-'}` },
])

onMounted(async () => {
  if (!datasetStore.items.length) await datasetStore.load()
  await reloadRuns()
  const runId = Number(route.query.run ?? 0)
  if (runId) await selectRun(runId)
  else if (runStore.runs.length) await selectRun(runStore.runs[0].id)
})

async function reloadRuns() {
  await runStore.loadRuns(datasetFilter.value)
}

async function selectRun(runId: number) {
  await runStore.loadDetail(runId)
  if (runStore.detail && ['queued', 'running'].includes(runStore.detail.status)) {
    polling.start(runId, () => reloadRuns())
  }
}

function drill(item: RunItem) {
  const run = runStore.detail
  if (!run) return
  router.push({ path: '/issues', query: { dataset: String(run.dataset_id), rule: String(item.rule_id ?? '') } })
}

async function downloadReport() {
  const run = runStore.detail
  if (!run) return
  const report = await fetchReport(run.id)
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${report.report_no}.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

async function runAgain() {
  const target = datasetFilter.value ?? datasetStore.items[0]?.id
  if (!target) return
  await ruleStore.load(target)
  const result = await ruleStore.runAll(target)
  await reloadRuns()
  await selectRun(result.run_id)
}
</script>
