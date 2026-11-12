import { onBeforeUnmount, ref } from 'vue'
import { useRunStore } from '../stores/runStore'
import { RUN_TERMINAL_STATUSES } from '../constants/ruleRunStatus'

export function useRunPolling() {
  const store = useRunStore()
  const active = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let delay = 1000

  function stop() {
    active.value = false
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  function tick(runId: number, onDone?: () => void) {
    timer = setTimeout(async () => {
      const detail = await store.refreshDetail(runId)
      if (!detail) {
        delay = Math.min(delay * 2, 8000)
        tick(runId, onDone)
        return
      }
      if (RUN_TERMINAL_STATUSES.includes(detail.status as never)) {
        stop()
        onDone?.()
        return
      }
      delay = Math.min(delay + 1000, 4000)
      tick(runId, onDone)
    }, delay)
  }

  function start(runId: number, onDone?: () => void) {
    stop()
    active.value = true
    delay = 1000
    tick(runId, onDone)
  }

  onBeforeUnmount(stop)
  return { active, start, stop }
}
