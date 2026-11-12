<template>
  <div class="min-h-screen grid" :class="collapsed ? 'grid-cols-[64px_1fr]' : 'grid-cols-[280px_1fr]'">
    <aside class="border-r border-rule bg-paper-2 flex flex-col min-h-screen">
      <div class="px-4 pt-5 pb-4">
        <div v-if="!collapsed" class="font-display text-[18px] leading-none tracking-[0.02em]">QUALISCOPE</div>
        <div v-else class="font-display text-[15px]">QS</div>
        <div v-if="!collapsed" class="eyebrow mt-2">数据可信度治理平台</div>
        <div v-if="!collapsed" class="text-[10.5px] text-ink-soft mt-1">{{ MESSAGES.customer }}</div>
      </div>
      <div class="hr mx-4"></div>

      <nav class="mt-3 flex-1 px-3">
        <template v-if="!collapsed">
          <div class="eyebrow px-3 py-2">标本</div>
          <RouterLink to="/datasets" class="rail-link" active-class="active">
            <span>数据集索引</span><span class="text-[11px]">{{ datasetStore.items.length }}</span>
          </RouterLink>
          <RouterLink to="/rules" class="rail-link" active-class="active">
            <span>规则构建器</span><span class="text-[11px]">{{ ruleStore.items.length }}</span>
          </RouterLink>
          <div class="eyebrow px-3 py-2 mt-3">批次</div>
          <RouterLink to="/runs" class="rail-link" active-class="active">
            <span>执行台账</span>
          </RouterLink>
          <div class="eyebrow px-3 py-2 mt-3">分诊</div>
          <RouterLink to="/issues" class="rail-link" active-class="active">
            <span>问题分诊板</span><span class="text-[11px]">{{ issueTotal }}</span>
          </RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/datasets" class="rail-link !justify-center !px-0" active-class="active" title="数据集">数</RouterLink>
          <RouterLink to="/rules" class="rail-link !justify-center !px-0" active-class="active" title="规则">规</RouterLink>
          <RouterLink to="/runs" class="rail-link !justify-center !px-0" active-class="active" title="批次">批</RouterLink>
          <RouterLink to="/issues" class="rail-link !justify-center !px-0" active-class="active" title="问题">诊</RouterLink>
        </template>
      </nav>

      <div class="px-4 pb-5">
        <div class="hr mb-3"></div>
        <div v-if="!collapsed" class="text-[12.5px]">{{ auth.displayName || '未登录' }}</div>
        <div v-if="!collapsed" class="text-[10.5px] text-ink-soft mt-0.5">{{ roleLabel }}</div>
        <QuotaMeter v-if="!collapsed" class="mt-3" :quota="quota" />
        <div class="flex items-center justify-between mt-3">
          <button class="btn btn-quiet !px-2 !py-1" @click="collapsed = !collapsed">
            {{ collapsed ? '»' : '« 折叠索引' }}
          </button>
          <button class="btn btn-quiet !px-2 !py-1" @click="logout">退出</button>
        </div>
      </div>
    </aside>

    <main class="min-w-0">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { MESSAGES } from '../../constants/messages'
import { ROLE_LABELS } from '../../types/user'
import { useAuthStore } from '../../stores/authStore'
import { useDatasetStore } from '../../stores/datasetStore'
import { useRuleStore } from '../../stores/ruleStore'
import { useRunStore } from '../../stores/runStore'
import { fetchIssueSummary } from '../../api/issue'
import QuotaMeter from './QuotaMeter.vue'

const collapsed = ref(false)
const auth = useAuthStore()
const datasetStore = useDatasetStore()
const ruleStore = useRuleStore()
const runStore = useRunStore()
const router = useRouter()
const issueTotal = ref(0)

const quota = computed(() => runStore.quota)
const roleLabel = computed(() => ROLE_LABELS[auth.role] ?? auth.role)

onMounted(async () => {
  if (!auth.user) await auth.restore()
  await Promise.all([datasetStore.load(), ruleStore.load(null)])
  try {
    const summary = await fetchIssueSummary(null)
    issueTotal.value = summary.total
  } catch {
    issueTotal.value = 0
  }
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
