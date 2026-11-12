<template>
  <div class="paper-page">
    <PageHeader
      eyebrow="rule builder"
      title="规则构建器"
      subtitle="规则由列决定：先选一列，再选 not_null 或 range 起步；参数面板实时校验。"
      :meta="meta"
    >
      <template #actions>
        <select v-model="datasetId" class="input !w-[220px]" @change="onDatasetChange">
          <option v-for="dataset in datasetStore.items" :key="dataset.id" :value="dataset.id">{{ dataset.name }}</option>
        </select>
        <button class="btn" :disabled="!auth.canWrite || ruleStore.running" @click="runAll">批量执行</button>
      </template>
    </PageHeader>

    <PermissionNotice v-if="!auth.canWrite" class="mb-4" />
    <ErrorNotice :error="ruleStore.error" />
    <div v-if="ruleStore.lastAuditNotice" class="mb-3 text-[11.5px]" :style="{ color: 'var(--assay)' }">
      {{ ruleStore.lastAuditNotice }}
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-8">
      <section>
        <div class="flex items-baseline justify-between mb-2">
          <div class="eyebrow">规则清单 · {{ ruleStore.items.length }} 条（启用 {{ ruleStore.activeCount }}）</div>
          <button class="link-button text-[11px]" :disabled="!auth.canWrite" @click="loadRecommendations">从剖析结果推荐 3 条</button>
        </div>

        <table class="table-base">
          <thead>
            <tr>
              <th class="w-[26px]"></th>
              <th>规则</th>
              <th class="w-[190px]">参数</th>
              <th class="w-[64px]">严重度</th>
              <th class="w-[58px] text-right">样本</th>
              <th class="w-[120px]"></th>
            </tr>
          </thead>
          <tbody>
            <RuleCard
              v-for="rule in ruleStore.items"
              :key="rule.id"
              :rule="rule"
              @edit="editRule"
              @toggle="toggle"
              @remove="askRemove"
            />
          </tbody>
        </table>

        <EmptyState
          v-if="!ruleStore.items.length && !ruleStore.loading"
          class="mt-4"
          title="还没有规则"
          :description="MESSAGES.ruleEmptyHint"
        >
          <button class="btn btn-solid" :disabled="!auth.canWrite" @click="loadRecommendations">从剖析结果推荐 3 条</button>
        </EmptyState>

        <section v-if="recommendations.length" class="mt-6">
          <div class="eyebrow mb-2">候选规则（点击带入右侧面板）</div>
          <ul>
            <li v-for="item in recommendations" :key="item.column_name + item.rule_type" class="flex items-baseline gap-4 py-1.5 border-b border-dashed border-rule">
              <span class="text-[12px] w-[110px] tabular-nums">{{ item.column_name }}</span>
              <span class="text-[11.5px] w-[75px]">{{ item.rule_type }}</span>
              <SeverityBadge :severity="item.severity" class="w-[56px]" />
              <span class="text-[11.5px] text-ink-soft flex-1">{{ item.reason }}</span>
              <button class="link-button text-[11px]" :disabled="!auth.canWrite" @click="applySuggestion(item)">带入 →</button>
            </li>
          </ul>
        </section>
      </section>

      <aside class="border-l border-rule pl-6">
        <div class="flex items-baseline justify-between mb-2">
          <div class="eyebrow">{{ draft.id ? `编辑规则 #${draft.id}` : '新建规则' }}</div>
          <button class="link-button text-[11px]" @click="resetDraft">清空</button>
        </div>

        <div class="mb-3">
          <div class="label mb-1">选择列</div>
          <ColumnPicker v-model="draft.column_name" :columns="columns" />
        </div>

        <RuleParamForm :draft="draft" />
        <RulePreviewHint :issues="issues" />

        <div class="mt-4 flex gap-2">
          <button class="btn btn-solid" :disabled="!auth.canWrite || !valid || ruleStore.saving" @click="saveDraft">
            {{ ruleStore.saving ? '保存中…' : '保存规则' }}
          </button>
          <button class="btn" @click="resetDraft">重置</button>
        </div>
      </aside>
    </div>

    <ConfirmDialog
      :open="Boolean(pendingRemove)"
      title="删除规则"
      message="删除规则会同时删除它产生的历史问题单，且不可恢复。"
      @cancel="pendingRemove = null"
      @confirm="confirmRemove"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '../components/common/PageHeader.vue'
import RuleCard from '../components/rule/RuleCard.vue'
import RuleParamForm from '../components/rule/RuleParamForm.vue'
import RulePreviewHint from '../components/rule/RulePreviewHint.vue'
import ColumnPicker from '../components/rule/ColumnPicker.vue'
import SeverityBadge from '../components/common/SeverityBadge.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import { useRuleDraft } from '../hooks/useRuleDraft'
import { useDatasetStore } from '../stores/datasetStore'
import { useRuleStore } from '../stores/ruleStore'
import { useAuthStore } from '../stores/authStore'
import { fetchColumns, fetchRecommendations } from '../api/profile'
import { MESSAGES } from '../constants/messages'
import type { QualityRule } from '../types/rule'
import type { RuleSuggestion } from '../types/profile'

const route = useRoute()
const router = useRouter()
const datasetStore = useDatasetStore()
const ruleStore = useRuleStore()
const auth = useAuthStore()

const datasetId = ref<number>(Number(route.query.dataset ?? 0))
const columns = ref<Array<{ column_name: string; type_label: string; null_rate: number }>>([])
const recommendations = ref<RuleSuggestion[]>([])
const pendingRemove = ref<number | null>(null)

const { draft, issues, valid, reset, applySuggestion: applySuggestionToDraft, edit, save, pickColumn } = useRuleDraft(null)

const meta = computed(() => [
  { label: '数据集', value: datasetStore.items.find((item) => item.id === datasetId.value)?.name ?? '-' },
  { label: '规则', value: String(ruleStore.items.length) },
  { label: '启用', value: String(ruleStore.activeCount) },
  { label: '样本上限', value: '200 / 规则' },
])

onMounted(async () => {
  if (!datasetStore.items.length) await datasetStore.load()
  if (!datasetId.value) {
    const withRules = datasetStore.items.find((item) => item.rule_count > 0)
    datasetId.value = withRules?.id ?? datasetStore.items[0]?.id ?? 0
  }
  await Promise.all([reloadRules(), loadColumns()])
  const column = route.query.column
  if (typeof column === 'string') pickColumn(column)
})

async function reloadRules() {
  await ruleStore.load(datasetId.value || null)
}

async function loadColumns() {
  if (!datasetId.value) return
  try {
    const result = await fetchColumns(datasetId.value)
    columns.value = result.columns
  } catch {
    columns.value = []
  }
}

async function loadRecommendations() {
  if (!datasetId.value) return
  try {
    const result = await fetchRecommendations(datasetId.value, 3)
    recommendations.value = result.items
  } catch {
    recommendations.value = []
  }
}

function onDatasetChange() {
  reset(datasetId.value)
  reloadRules()
  loadColumns()
}

function resetDraft() {
  reset(datasetId.value)
}

function editRule(rule: QualityRule) {
  edit({ ...rule, params: rule.params })
}

async function toggle(ruleId: number, active: boolean) {
  await ruleStore.toggle(ruleId, active)
}

function askRemove(ruleId: number) {
  pendingRemove.value = ruleId
}

async function confirmRemove() {
  if (pendingRemove.value === null) return
  await ruleStore.remove(pendingRemove.value, datasetId.value)
  pendingRemove.value = null
}

async function saveDraft() {
  await save()
  reset(datasetId.value)
}

async function runAll() {
  if (!datasetId.value) return
  const result = await ruleStore.runAll(datasetId.value)
  router.push({ path: '/runs', query: { run: String(result.run_id) } })
}

function applySuggestion(item: RuleSuggestion) {
  applySuggestionToDraft(item, datasetId.value)
}
</script>
