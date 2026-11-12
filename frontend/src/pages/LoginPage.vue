<template>
  <div class="min-h-screen grid lg:grid-cols-[1.1fr_1fr]">
    <section class="bg-paper-2 border-r border-rule px-10 lg:px-16 py-12 flex flex-col justify-between">
      <div>
        <div class="eyebrow">Mingchuan Bank · Data Governance</div>
        <h1 class="display mt-3 !text-[34px] leading-[1.1]">QualiScope</h1>
        <div class="mt-2 text-[13px] text-ink-soft">数据可信度治理平台 · 把一份数据集从「不知道能不能用」验到「每一行违规都有据可查」</div>

        <div class="mt-10 w-[300px] border border-rule bg-paper px-5 py-4 -rotate-1">
          <div class="eyebrow">specimen label</div>
          <div class="mt-3 space-y-2">
            <div class="flex justify-between"><span class="label">机构</span><span class="text-[12px]">明川银行</span></div>
            <div class="flex justify-between"><span class="label">数据集</span><span class="text-[12px] tabular-nums">cust_account_202611.csv</span></div>
            <div class="flex justify-between"><span class="label">批次</span><span class="text-[12px] tabular-nums">QC-202611-001</span></div>
            <div class="hr"></div>
            <div class="flex justify-between"><span class="label">状态</span><span class="text-[12px]">已归档</span></div>
          </div>
        </div>
      </div>
      <div class="text-[11px] text-ink-soft leading-relaxed">
        监管报送一年 4 次 · 数仓 600+ 张表<br />
        列级剖析 → 规则构建 → 批量执行 → 违规隔离 → 问题分诊 → 报告单归档
      </div>
    </section>

    <section class="px-10 lg:px-20 py-12 flex flex-col justify-center">
      <div class="w-full max-w-[380px]">
        <div class="eyebrow">sign in</div>
        <h2 class="display mt-2 !text-[24px]">进入检验台</h2>
        <p class="text-[12px] text-ink-soft mt-2">使用数据治理组账号登录，按角色进入对应页面。</p>

        <form class="mt-8 space-y-5" @submit.prevent="submit">
          <div>
            <label class="label block mb-1">邮箱</label>
            <input v-model="email" type="email" class="input" autocomplete="username" placeholder="steward@mingchuan-bank.cn" />
          </div>
          <div>
            <label class="label block mb-1">密码</label>
            <input v-model="password" type="password" class="input" autocomplete="current-password" placeholder="QualiScope@2026" />
          </div>
          <button type="submit" class="btn btn-solid w-full justify-center !py-2" :disabled="auth.loading">
            {{ auth.loading ? '验证中…' : '登录' }}
          </button>
        </form>

        <ErrorNotice :error="error" />

        <div class="mt-8">
          <div class="label mb-2">演示账号（密码统一 QualiScope@2026）</div>
          <ul class="space-y-1.5">
            <li v-for="account in demoAccounts" :key="account.email">
              <button class="link-button text-[11.5px]" @click="fill(account.email)">
                {{ account.label }} · {{ account.email }}
              </button>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import { useAuthStore } from '../stores/authStore'
import type { ApiError } from '../types/api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const email = ref('steward@mingchuan-bank.cn')
const password = ref('QualiScope@2026')
const error = ref<ApiError | null>(null)

const demoAccounts = [
  { label: '数据管家', email: 'steward@mingchuan-bank.cn' },
  { label: '分析师', email: 'analyst@mingchuan-bank.cn' },
  { label: '审计（只读）', email: 'audit@mingchuan-bank.cn' },
]

function fill(value: string) {
  email.value = value
  password.value = 'QualiScope@2026'
}

async function submit() {
  error.value = null
  try {
    await auth.login(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/datasets'
    router.push(redirect)
  } catch (err) {
    error.value = err as ApiError
  }
}
</script>
