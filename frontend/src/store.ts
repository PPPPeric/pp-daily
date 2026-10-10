import { openDB } from 'idb'
import { ref } from 'vue'
import { dayAt, keyOf, type Completion, type Snapshot } from './domain'

interface Local { snapshot: Snapshot; pending: Completion[] }
const empty = (): Local => ({snapshot:{version:1,generation:'',projects:[],completions:[]},pending:[]})
const db = openDB('pp-daily', 1, {upgrade(database) { database.createObjectStore('state') }})
export const local = ref<Local>(empty())
export const status = ref('正在加载')
export const busy = ref(false)
export const conflict = ref(false)
export const storageReady = ref(false)
const lock = async <T>(action: () => Promise<T>): Promise<T> => navigator.locks ? navigator.locks.request('pp-daily-write', action) : action()
async function read(): Promise<Local> { return (await (await db).get('state','local')) || empty() }
async function save(value: Local) { await (await db).put('state',value,'local'); local.value = value }
export async function api(path: string, body?: unknown, method = 'POST'): Promise<Snapshot> {
  const response = await fetch('/api' + path, {method:body === undefined ? 'GET' : method, headers:{'Content-Type':'application/json'}, body:body === undefined ? undefined : JSON.stringify(body), signal:AbortSignal.timeout(12000), cache:'no-store'})
  if (!response.ok) {
    if (response.status === 409) conflict.value = true
    const error = await response.json().catch(() => ({}))
    throw new Error(typeof error.detail === 'string' ? error.detail : '数据校验失败，请检查输入或备份文件')
  }
  return response.json()
}
export async function init() {
  try { local.value = await read(); storageReady.value = true; await navigator.storage?.persist?.(); await sync() }
  catch { status.value = '本地存储不可用，请检查浏览器设置' }
}
export async function complete(id: string) {
  await lock(async () => {
    const value = await read(), day = dayAt(), p = value.snapshot.projects.find(p => p.id === id)
    if (!p || p.archived || !value.snapshot.generation || conflict.value) return
    const record = {project_id:id, day, completed_at:new Date().toISOString()}
    if (value.snapshot.completions.some(c => keyOf(c) === keyOf(record))) { local.value = value; return }
    value.snapshot.completions.push(record); value.pending.push(record)
    await save(value)
  })
  await sync()
}
export async function sync() {
  if (busy.value || conflict.value || !storageReady.value) return
  busy.value = true
  try {
    await lock(async () => {
      const value = await read()
      const snapshot = value.snapshot.generation ? await api('/sync', {generation:value.snapshot.generation, completions:value.pending}) : await api('/state')
      await save({snapshot,pending:[]})
      status.value = '已同步'
    })
  } catch (error) { status.value = conflict.value ? '数据已恢复，需要重新载入' : `${local.value.pending.length ? local.value.pending.length + ' 条待同步 · ' : ''}${error instanceof TypeError || !navigator.onLine ? '离线可用' : (error as Error).message}` }
  finally { busy.value = false }
}
export async function manage(path: string, body: object, method = 'POST') {
  if (conflict.value) throw new Error('请先处理数据恢复冲突')
  await sync()
  if (local.value.pending.length) throw new Error('请先同步待上传记录，再管理项目')
  await lock(async () => {
    const value = await read()
    if (value.pending.length) throw new Error('仍有待同步记录')
    await save({snapshot:await api(path,{...body,generation:value.snapshot.generation},method),pending:[]})
  })
  status.value = '已同步'
}
export async function reloadServer() { await lock(async () => save({snapshot:await api('/state'),pending:[]})); conflict.value = false; status.value = '已同步' }
export function exportLocal() {
  const blob = new Blob([JSON.stringify(local.value.snapshot,null,2)],{type:'application/json'})
  const url = URL.createObjectURL(blob), link = document.createElement('a')
  link.href = url; link.download = `pp Daily-${dayAt()}.json`; link.click(); setTimeout(() => URL.revokeObjectURL(url),60000)
}
