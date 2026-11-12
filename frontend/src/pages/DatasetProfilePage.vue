<template>
  <div class="paper-page">
    <PageHeader
      eyebrow="assay report"
      :title="payload?.dataset.name ?? '检验报告单'"
      :subtitle="subtitle"
      :meta="meta"
    >
      <template #actions>
        <QuotaMeter class="w-[130px] mr-3" :quota="runStore.quota" />
        <button class="btn" :disabled="!auth.canWrite || recomputing" @click="recompute">重算剖析</button>
        <RouterLink to="/rules" class="btn">去建规则 →</RouterLink>
      </template>
    </PageHeader>

    <ErrorNotice :error="error" retryable @retry="load(Number(route.params.id))" />

    <div v-if="loading" class="py-10 text-[12.5px] text-ink-soft">正在读取剖析结果…</div>

    <template v-else-if="payload">
      <div class="flex items-center justify-between mb-3">
        <div class="eyebrow">列级检验记录 · 共 {{ payload.columns.length }} 列</div>
        <div class="text-[11px] text-ink-soft tabular-nums">
          批次 #{{ payload.run?.run_id ?? '-' }} · 扫描 {{ formatInt(payload.run?.rows_scanned ?? 0) }} 行 · 耗时 {{ formatDuration(payload.run?.duration_ms) }}
        </div>
      </div>

      <ColumnTable :columns="payload.columns" @pick="pickColumn" />

      <section v-if="payload.recommendations.length" class="mt-8">
        <div class="flex items-baseline justify-between border-t border-rule pt-3">
          <div class="eyebrow">从剖析结果推荐</div>
          <RouterLink to="/rules" class="link-button text-[11px]">全部带入规则构建器 →</RouterLink>
        </div>
        <ul class="mt-2">
          <li v-for="item in payload.recommendations" :key="item.column_name + item.rule_type" class="flex items-baseline gap-4 py-1.5 border-b border-dashed border-rule">
            <span class="text-[12px] w-[120px] tabular-nums">{{ item.column_name }}</span>
            <span class="text-[11.5px] w-[80px]">{{ item.rule_type }}</span>
            <SeverityBadge :severity="item.severity" class="w-[60px]" />
            <span class="text-[11.5px] text-ink-soft">{{ item.reason }}</span>
          </li>
        </ul>
      </section>

      <div class="mt-8 flex items-center justify-between border-t border-rule pt-3 text-[10.5px] text-ink-soft">
        <span>数据集 #{{ payload.dataset.id }} · 校验和 {{ payload.dataset.checksum.slice(0, 16) }}</span>
        <span>生成时间 {{ new Date().toLocaleString('zh-CN') }} · 报告单编号 QC-{{ payload.dataset.id }}-PROFILE</span>
      </div>
      <ActivityTrail />
    </template>

    <EmptyState
      v-else
      class="mt-6"
      title="这份标本还没验过"
      description="先执行一次剖析：系统会逐列计算空值率、基数、分位、模式与异常值。"
    >
      <button class="btn btn-solid" :disabled="!auth.canWrite || recomputing" @click="recompute">开始剖析</button>
    </EmptyState>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '../components/common/PageHeader.vue'
import ColumnTable from '../components/profile/ColumnTable.vue'
import QuotaMeter from '../components/common/QuotaMeter.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ActivityTrail from '../components/common/ActivityTrail.vue'
import SeverityBadge from '../components/common/SeverityBadge.vue'
import { useProfileQuery } from '../hooks/useProfileQuery'
import { useRunStore } from '../stores/runStore'
import { useAuthStore } from '../stores/authStore'
import { formatDuration, formatInt } from '../utils/formatters'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()
const auth = useAuthStore()
const { payload, loading, recomputing, error, load, recompute: recomputeProfile } = useProfileQuery()

const datasetId = computed(() => Number(route.params.id))
const subtitle = computed(() => (payload.value ? `${payload.value.dataset.source_format.toUpperCase()} · ${payload.value.dataset.column_count} 列 · 校验和 ${payload.value.dataset.checksum.slice(0, 10)}` : ''))
const meta = computed(() => {
  if (!payload.value) return []
  return [
    { label: '行数', value: formatInt(payload.value.dataset.row_count) },
    { label: '列数', value: String(payload.value.dataset.column_count) },
    { label: '剖析批次', value: `#${payload.value.run?.run_id ?? '-'}` },
    { label: '耗时', value: formatDuration(payload.value.run?.duration_ms) },
    { label: '上传时间', value: payload.value.dataset.uploaded_at ?? '-' },
  ]
})

onMounted(async () => {
  await load(datasetId.value)
})

watch(datasetId, (id) => load(id))

function pickColumn(columnName: string) {
  router.push({ path: '/rules', query: { dataset: String(datasetId.value), column: columnName } })
}

async function recompute() {
  try {
    await recomputeProfile(datasetId.value)
    await load(datasetId.value, true)
  } catch {
    /* error ref already carries the envelope */
  }
}
</script>
