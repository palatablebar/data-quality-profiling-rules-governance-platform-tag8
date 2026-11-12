import { defineStore } from 'pinia'
import { bulkAssign, fetchIssueSummary, fetchIssues, updateIssue } from '../api/issue'
import type { Issue, IssueSummary } from '../types/issue'
import type { User } from '../types/user'
import { fetchUsers } from '../api/auth'

export interface IssueFilterState {
  dataset_id: number | null
  severity: string | null
  status: string | null
  rule_id: number | null
}

interface IssueStoreState {
  items: Issue[]
  total: number
  summary: IssueSummary | null
  users: User[]
  filters: IssueFilterState
  loading: boolean
  error: string
  selected: Issue | null
}

export const useIssueStore = defineStore('issue', {
  state: (): IssueStoreState => ({
    items: [],
    total: 0,
    summary: null,
    users: [],
    filters: { dataset_id: null, severity: null, status: null, rule_id: null },
    loading: false,
    error: '',
    selected: null,
  }),
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const page = await fetchIssues({ ...this.filters, page_size: 200 })
        this.items = page.items
        this.total = page.total
        this.summary = await fetchIssueSummary(this.filters.dataset_id)
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '问题单加载失败'
      } finally {
        this.loading = false
      }
    },
    async loadUsers() {
      const result = await fetchUsers()
      this.users = result.items
    },
    async update(issueId: number, payload: { status?: string; assignee_id?: number | null; note?: string }) {
      const issue = await updateIssue(issueId, payload)
      const index = this.items.findIndex((item) => item.id === issueId)
      if (index >= 0) this.items[index] = issue
      if (this.selected?.id === issueId) this.selected = issue
      this.summary = await fetchIssueSummary(this.filters.dataset_id)
      return issue
    },
    async assignMany(issueIds: number[], assigneeId: number | null) {
      await bulkAssign({ issue_ids: issueIds, assignee_id: assigneeId, status: 'triaged' })
      await this.load()
    },
    select(issue: Issue | null) {
      this.selected = issue
    },
  },
})
