<template>
  <div class="paper-page">
    <PageHeader
      eyebrow="specimen index"
      title="标本索引"
      subtitle="上传一批上游数据，先看它长什么样，再决定用什么规则约束它。"
      :meta="meta"
    >
      <template #actions>
        <span class="eyebrow">{{ MESSAGES.customer }}</span>
      </template>
    </PageHeader>

    <PermissionNotice v-if="!auth.canWrite" class="mb-4" />
    <DatasetUploader v-else :uploading="datasetStore.uploading" @upload="onUpload" />

    <ErrorNotice :error="datasetStore.error" retryable @retry="datasetStore.load()" />

    <div v-if="datasetStore.items.length" class="mt-6">
      <table class="table-base">
        <thead>
          <tr>
            <th class="w-[120px]">标本</th>
            <th>数据集</th>
            <th class="w-[74px]">格式</th>
            <th class="w-[90px] text-right">行数</th>
            <th class="w-[60px] text-right">列数</th>
            <th class="w-[70px] text-right">规则</th>
            <th class="w-[84px] text-right">待处理</th>
            <th class="w-[150px]">上传时间</th>
            <th class="w-[170px]"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dataset in datasetStore.items" :key="dataset.id">
            <td><DatasetThumb :dataset="dataset" /></td>
            <td>
              <RouterLink :to="`/datasets/${dataset.id}/profile`" class="text-[12.5px]">{{ dataset.name }}</RouterLink>
              <div class="text-[10.5px] text-ink-soft mt-0.5">#{{ dataset.id }} · {{ dataset.status }}</div>
            </td>
            <td class="eyebrow !tracking-normal">{{ dataset.source_format }}</td>
            <td class="num">{{ dataset.row_count_display }}</td>
            <td class="num">{{ dataset.column_count }}</td>
            <td class="num">{{ dataset.rule_count }}</td>
            <td class="num">{{ dataset.open_issues }}</td>
            <td class="text-[11.5px] tabular-nums text-ink-soft">{{ dataset.uploaded_at }}</td>
            <td class="text-right whitespace-nowrap">
              <RouterLink :to="`/datasets/${dataset.id}/profile`" class="link-button text-[11px] mr-3">剖析报告单</RouterLink>
              <RouterLink :to="`/rules?dataset=${dataset.id}`" class="link-button text-[11px] mr-3">规则</RouterLink>
              <button v-if="auth.isSteward" class="link-button text-[11px]" :style="{ color: 'var(--alert-deep)' }" @click="askDelete(dataset)">
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <EmptyState
      v-else-if="!datasetStore.loading"
      class="mt-6"
      title="还没有标本"
      :description="MESSAGES.uploadHint"
      hint="也可以先执行 seed 演示数据：docker compose exec backend python -m scripts.seed_demo"
    >
      <RouterLink to="/rules" class="btn">看规则构建器</RouterLink>
    </EmptyState>

    <ActivityTrail />

    <ConfirmDialog
      :open="Boolean(pendingDelete)"
      title="删除数据集"
      :message="`将删除 ${pendingDelete?.name ?? ''} 及其规则、剖析记录与隔离样本。历史批次保留，但无法再复跑。`"
      @cancel="pendingDelete = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../components/common/PageHeader.vue'
import DatasetThumb from '../components/dataset/DatasetThumb.vue'
import DatasetUploader from '../components/dataset/DatasetUploader.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import ActivityTrail from '../components/common/ActivityTrail.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import { useDatasetStore } from '../stores/datasetStore'
import { useAuthStore } from '../stores/authStore'
import { MESSAGES } from '../constants/messages'
import { formatInt } from '../utils/formatters'
import type { Dataset } from '../types/dataset'

const datasetStore = useDatasetStore()
const auth = useAuthStore()
const pendingDelete = ref<Dataset | null>(null)

const meta = computed(() => [
  { label: '数据集', value: String(datasetStore.items.length) },
  { label: '总行数', value: formatInt(datasetStore.items.reduce((sum, item) => sum + item.row_count, 0)) },
  { label: '规则', value: String(datasetStore.items.reduce((sum, item) => sum + item.rule_count, 0)) },
  { label: '待处理问题', value: String(datasetStore.items.reduce((sum, item) => sum + item.open_issues, 0)) },
])

onMounted(() => datasetStore.load())

async function onUpload(file: File) {
  try {
    await datasetStore.upload(file)
  } catch (error) {
    datasetStore.error = (error as { message?: string }).message ?? '上传失败'
  }
}

function askDelete(dataset: Dataset) {
  pendingDelete.value = dataset
}

async function confirmDelete() {
  if (!pendingDelete.value) return
  await datasetStore.remove(pendingDelete.value.id)
  pendingDelete.value = null
}
</script>
