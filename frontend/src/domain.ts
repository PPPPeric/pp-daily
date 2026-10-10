export interface Project { id: string; name: string; icon?: string; color: string; position: number; created: string; archived: string | null }
export interface Completion { project_id: string; day: string; completed_at: string }
export interface Snapshot { version: number; generation: string; projects: Project[]; completions: Completion[] }
export const dayAt = (now = new Date()) => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year:'numeric', month:'2-digit', day:'2-digit' }).format(now)
export function addDays(day: string, count: number) { const date = new Date(day + 'T12:00:00Z'); date.setUTCDate(date.getUTCDate() + count); return date.toISOString().slice(0, 10) }
export const keyOf = (c: Completion) => c.project_id + ':' + c.day
export function metrics(project: Project, records: Completion[], today: string) {
  const days = [...new Set(records.filter(c => c.project_id === project.id && c.day <= today).map(c => c.day))].sort()
  const set = new Set(days)
  const end = project.archived && project.archived < today ? project.archived : today
  let current = 0, cursor = set.has(end) ? end : addDays(end, -1)
  while (set.has(cursor)) { current++; cursor = addDays(cursor, -1) }
  let longest = 0, run = 0, previous = ''
  for (const day of days) { run = previous && addDays(previous, 1) === day ? run + 1 : 1; longest = Math.max(longest, run); previous = day }
  return [days.length, days.filter(d => d.slice(0,7) === today.slice(0,7)).length, current, longest]
}

export const projectIcon = (project: Pick<Project, 'name' | 'icon'>) => Array.from(project.icon?.trim() || project.name.trim())[0] || 'p'
