import { createRouter, createWebHistory } from 'vue-router'
import { setupGuards } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/datasets' },
    { path: '/login', name: 'login', component: () => import('../pages/LoginPage.vue'), meta: { public: true } },
    { path: '/datasets', name: 'datasets', component: () => import('../pages/DatasetsPage.vue'), meta: { title: '标本索引' } },
    {
      path: '/datasets/:id/profile',
      name: 'dataset-profile',
      component: () => import('../pages/DatasetProfilePage.vue'),
      meta: { title: '检验报告单' },
    },
    { path: '/rules', name: 'rules', component: () => import('../pages/RulesPage.vue'), meta: { title: '规则构建器' } },
    { path: '/runs', name: 'runs', component: () => import('../pages/RunsPage.vue'), meta: { title: '执行台账' } },
    { path: '/issues', name: 'issues', component: () => import('../pages/IssuesPage.vue'), meta: { title: '问题分诊板' } },
    { path: '/:pathMatch(.*)*', redirect: '/datasets' },
  ],
})

setupGuards(router)

export default router
