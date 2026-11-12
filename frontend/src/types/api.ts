export interface ApiError {
  code: string
  message: string
  detail?: unknown
  requestId?: string | null
  status?: number
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ListResponse<T> {
  items: T[]
  total: number
}
