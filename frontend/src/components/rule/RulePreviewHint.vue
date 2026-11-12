<template>
  <ul v-if="issues.length" class="mt-2">
    <li v-for="issue in issues" :key="issue.field + issue.message" class="text-[11.5px]" :style="{ color: 'var(--alert-deep)' }">
      · {{ issue.message }}<span v-if="issue.offset">（第 {{ issue.offset }} 个字符）</span>
    </li>
  </ul>
  <div v-else class="mt-2 text-[11.5px]" :style="{ color: 'var(--assay)' }">参数校验通过，可以保存</div>
</template>

<script setup lang="ts">
import type { DraftIssue } from '../../utils/ruleSerialize'

defineProps<{ issues: DraftIssue[] }>()
</script>
