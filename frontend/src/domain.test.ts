import { describe, expect, it } from 'vitest'
import { addDays, dayAt, metrics, type Project } from './domain'
const p: Project = {id:'one',name:'阅读',color:'#285C47',position:0,created:'2024-01-01',archived:null}
const records = (...days: string[]) => days.map(day => ({project_id:'one',day,completed_at:day+'T12:00:00+08:00'}))
describe('daily rules', () => {
  it('uses Shanghai date across UTC midnight', () => expect(dayAt(new Date('2026-10-09T16:01:00Z'))).toBe('2026-10-10'))
  it('handles leap days and year rollover', () => { expect(addDays('2024-02-28',1)).toBe('2024-02-29'); expect(addDays('2025-12-31',1)).toBe('2026-01-01') })
  it('keeps yesterday streak until today completed', () => expect(metrics(p,records('2026-09-30','2026-10-01','2026-10-02'),'2026-10-03')).toEqual([3,2,3,3]))
  it('breaks after a missed yesterday', () => expect(metrics(p,records('2026-10-01'),'2026-10-03')).toEqual([1,1,0,1]))
  it('counts today once and isolates other projects', () => expect(metrics(p,[...records('2026-10-02','2026-10-03','2026-10-03'),{project_id:'two',day:'2026-10-01',completed_at:''}],'2026-10-03')).toEqual([2,2,2,2]))
  it('retains archived streak', () => expect(metrics({...p,archived:'2026-10-02'},records('2026-10-01','2026-10-02'),'2026-10-10')).toEqual([2,2,2,2]))
  it('empty project has zero metrics', () => expect(metrics(p,[],'2026-10-10')).toEqual([0,0,0,0]))
})
