<template>
  <section class="mt-8">
    <button class="flex w-full items-baseline justify-between border-t border-rule pt-3" @click="expanded = !expanded">
      <span class="eyebrow">审计日志 · 最近 10 条</span>
      <span class="text-[11px] text-ink-soft">{{ expanded ? '收起' : '展开' }}</span>
    </button>
    <ul v-if="expanded" class="mt-2">
      <li v-for="entry in items" :key="entry.id" class="flex items-baseline gap-3 py-1 text-[12px] border-b border-dashed border-rule">
        <span class="text-ink-soft tabular-nums w-[136px] shrink-0">{{ entry.created_at }}</span>
        <span class="w-[92px] shrink-0">{{ entry.actor_name ?? '-' }}</span>
        <span class="w-[120px] shrink-0">{{ entry.action }}</span>
        <span class="text-ink-soft">{{ entry.entity_type }} #{{ entry.entity_id ?? '-' }}</span>
      </li>
      <li v-if="!items.length" class="py-2 text-[12px] text-ink-soft">暂无审计记录</li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchRecentAudit } from '../../api/audit'
import type { AuditEntry } from '../../types/audit'

const items = ref<AuditEntry[]>([])
const expanded = ref(true)

onMounted(async () => {
  try {
    const result = await fetchRecentAudit(10)
    items.value = result.items
  } catch {
    items.value = []
  }
})
</script>
