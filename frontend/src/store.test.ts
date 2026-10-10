import 'fake-indexeddb/auto'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { IDBFactory } from 'fake-indexeddb'
import { dayAt } from './domain'

const snapshot = () => ({version:1,generation:'old',projects:[{id:'p',name:'阅读',color:'#285C47',position:0,created:dayAt(),archived:null}],completions:[]})
beforeEach(() => {
  vi.resetModules()
  vi.stubGlobal('indexedDB',new IDBFactory())
  vi.stubGlobal('navigator',{onLine:true,storage:{persist:async () => true},locks:{request:async (_name: string, task: () => Promise<unknown>) => task()}})
  vi.stubGlobal('fetch',vi.fn(async () => new Response(JSON.stringify(snapshot()),{status:200})))
})
describe('offline persistence and sync', () => {
  it('persists completion and pending queue across module reload',async () => {
    const store = await import('./store')
    await store.init()
    vi.mocked(fetch).mockRejectedValue(new TypeError('network unavailable'))
    await store.complete('p')
    expect(store.local.value.pending).toHaveLength(1)
    expect(store.local.value.snapshot.completions).toHaveLength(1)
    vi.resetModules()
    const reopened = await import('./store')
    await reopened.init()
    expect(reopened.local.value.pending).toHaveLength(1)
    expect(reopened.local.value.snapshot.completions[0]?.day).toBe(dayAt())
    await reopened.complete('p')
    expect(reopened.local.value.pending).toHaveLength(1)
  })
  it('clears queue only after successful upload',async () => {
    const store = await import('./store')
    await store.init()
    vi.mocked(fetch).mockRejectedValue(new TypeError('network unavailable'))
    await store.complete('p')
    const records = [...store.local.value.pending]
    vi.mocked(fetch).mockImplementation(async () => new Response(JSON.stringify({...snapshot(),completions:records}),{status:200}))
    await store.sync()
    expect(store.local.value.pending).toEqual([])
    expect(store.local.value.snapshot.completions).toHaveLength(1)
    expect(store.status.value).toBe('已同步')
  })
  it('retains local records on restore conflict and blocks stale upload',async () => {
    const store = await import('./store')
    await store.init()
    vi.mocked(fetch).mockImplementation(async () => new Response(JSON.stringify({detail:'数据已恢复'}),{status:409}))
    await store.complete('p')
    expect(store.conflict.value).toBe(true)
    expect(store.local.value.pending).toHaveLength(1)
    const calls = vi.mocked(fetch).mock.calls.length
    await store.sync()
    expect(vi.mocked(fetch).mock.calls.length).toBe(calls)
    vi.mocked(fetch).mockImplementation(async () => new Response(JSON.stringify({...snapshot(),generation:'new'}),{status:200}))
    await store.reloadServer()
    expect(store.conflict.value).toBe(false)
    expect(store.local.value.snapshot.generation).toBe('new')
    expect(store.local.value.pending).toEqual([])
  })
  it('does not allow management with pending records',async () => {
    const store = await import('./store')
    await store.init()
    vi.mocked(fetch).mockRejectedValue(new TypeError('network unavailable'))
    await store.complete('p')
    await expect(store.manage('/projects',{name:'学习',color:'#285C47'})).rejects.toThrow('请先同步')
  })
})
