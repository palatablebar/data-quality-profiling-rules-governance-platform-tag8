<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="issue" class="fixed inset-0 z-30">
        <div class="absolute inset-0 bg-ink/20" @click="$emit('close')"></div>
        <aside class="absolute right-0 top-0 h-full w-[520px] max-w-full bg-paper border-l border-rule flex flex-col">
          <div class="px-6 pt-5 pb-3 border-b border-rule flex items-start justify-between gap-4">
            <div>
              <div class="eyebrow">issue no. {{ issue.id }}</div>
              <h2 class="display !text-[20px] mt-1">{{ issue.rule_name ?? '问题单' }}</h2>
              <div class="mt-1 flex items-center gap-3">
                <SeverityBadge :severity="issue.severity" />
                <span class="text-[11px] text-ink-soft">{{ issue.dataset_name }} · {{ issue.report_no ?? '-' }}</span>
              </div>
            </div>
            <button class="btn !px-2 !py-1" @click="$emit('close')">关闭</button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-4">
            <dl class="grid grid-cols-2 gap-x-6 gap-y-3">
              <div><dt class="label">列名</dt><dd class="text-[12.5px] tabular-nums mt-0.5">{{ issue.column_name }}</dd></div>
              <div><dt class="label">row_index</dt><dd class="text-[12.5px] tabular-nums mt-0.5">{{ issue.row_index }}</dd></div>
              <div class="col-span-2">
                <dt class="label">observed_value</dt>
                <dd class="text-[13px] tabular-nums mt-0.5 break-all">
                  <span v-if="issue.observed_value === ''" class="text-ink-soft">（空字符串）</span>
                  <span v-else>{{ issue.observed_value }}</span>
                </dd>
              </div>
              <div class="col-span-2">
                <dt class="label">expected_expr</dt>
                <dd class="text-[12.5px] tabular-nums mt-0.5 break-all">{{ issue.expected_expr }}</dd>
              </div>
              <div><dt class="label">状态</dt><dd class="text-[12.5px] mt-0.5">{{ ISSUE_STATUS_LABELS[issue.status] }}</dd></div>
              <div><dt class="label">跟进人</dt><dd class="text-[12.5px] mt-0.5">{{ issue.assignee_name ?? '未指派' }}</dd></div>
            </dl>

            <div class="mt-5">
              <div class="label mb-1">复现片段</div>
              <pre class="border border-rule bg-paper-2 px-3 py-2 text-[11.5px] tabular-nums whitespace-pre-wrap">{{ issue.repro_snippet }}</pre>
              <button class="btn mt-2 !py-1" @click="copySnippet">{{ copied ? '已复制' : '复制复现片段' }}</button>
            </div>

            <div class="mt-6">
              <div class="label mb-2">状态流转</div>
              <IssueStatusMenu :current="issue.status" @change="(status) => $emit('update', { status })" />
            </div>

            <div class="mt-5">
              <div class="label mb-1">指派给</div>
              <select class="input" :value="issue.assignee_id ?? ''" @change="onAssign">
                <option value="">未指派</option>
                <option v-for="user in users" :key="user.id" :value="user.id">{{ user.display_name }}（{{ user.role }}）</option>
              </select>
            </div>

            <div class="mt-5">
              <div class="label mb-1">备注</div>
              <textarea
                class="input min-h-[70px]"
                :value="issue.note ?? ''"
                placeholder="例如：已让业务方核对第 101 行状态值"
                @change="$emit('update', { note: ($event.target as HTMLTextAreaElement).value })"
              ></textarea>
            </div>
          </div>

          <div class="px-6 py-3 border-t border-rule text-[10.5px] text-ink-soft">
            创建时间 {{ issue.created_at }} · 批次 #{{ issue.rule_run_id }}
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SeverityBadge from '../common/SeverityBadge.vue'
import IssueStatusMenu from './IssueStatusMenu.vue'
import { ISSUE_STATUS_LABELS } from '../../constants/issueStatus'
import type { Issue } from '../../types/issue'
import type { User } from '../../types/user'

const props = defineProps<{ issue: Issue | null; users: User[] }>()
const emit = defineEmits<{
  close: []
  update: [payload: { status?: string; assignee_id?: number | null; note?: string }]
}>()
const copied = ref(false)

function onAssign(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update', { assignee_id: value === '' ? null : Number(value) })
}

async function copySnippet() {
  const text = props.issue?.repro_snippet ?? ''
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => (copied.value = false), 1600)
  } catch {
    copied.value = false
  }
}
</script>
