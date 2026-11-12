import http from './http'
import type { User } from '../types/user'

export interface LoginResult {
  token: string
  token_type: string
  user: User
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const { data } = await http.post<LoginResult>('/auth/login', { email, password })
  return data
}

export async function fetchMe(): Promise<{ user: User }> {
  const { data } = await http.get<{ user: User }>('/auth/me')
  return data
}

export async function fetchUsers(): Promise<{ items: User[]; total: number }> {
  const { data } = await http.get<{ items: User[]; total: number }>('/auth/users')
  return data
}
