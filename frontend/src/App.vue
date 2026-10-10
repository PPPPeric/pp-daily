<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import SwipeComplete from './SwipeComplete.vue'
import ProjectPicker from './ProjectPicker.vue'
import { addDays, dayAt, metrics, projectIcon, type Project } from './domain'
import { local, status, busy, conflict, storageReady, init, sync, complete, manage, exportLocal, reloadServer } from './store'

const page = ref('今日'), today = ref(dayAt()), selected = ref(''), month = ref(today.value.slice(0,7))
const viewedDay = ref(today.value), completedOpen = ref(true)
const recentDays = computed(() => Array.from({length:7},(_,i) => addDays(today.value,i-6)))
const visibleProjects = computed(() => projects.value.filter(p => p.created <= viewedDay.value && (!p.archived || p.archived >= viewedDay.value)))
const pendingProjects = computed(() => visibleProjects.value.filter(p => !done(p.id,viewedDay.value)))
const completedProjects = computed(() => visibleProjects.value.filter(p => done(p.id,viewedDay.value)))
const streak = (p: Project) => metrics(p,local.value.snapshot.completions,today.value)[2]
const shortWeekday = (day: string) => ['日','一','二','三','四','五','六'][new Date(day+'T12:00:00Z').getUTCDay()]
const message = ref(''), name = ref(''), icon = ref(''), color = ref('#285C47'), editing = ref(''), working = ref(false)
const projects = computed(() => local.value.snapshot.projects)
const project = computed(() => projects.value.find(p => p.id === selected.value) || projects.value[0])
const done = (id: string, day = today.value) => local.value.snapshot.completions.some(c => c.project_id === id && c.day === day)
const stats = computed(() => project.value ? metrics(project.value, local.value.snapshot.completions, today.value) : [0,0,0,0])
const statLabels = ['累计完成天数','本月完成天数','当前连续天数','最长连续天数']
const cells = computed(() => {
  const start = month.value + '-01', offset = (new Date(start + 'T12:00:00Z').getUTCDay() + 6) % 7
  const days = new Date(Number(month.value.slice(0,4)), Number(month.value.slice(5,7)),0).getDate()
  return [...Array(offset).fill(''), ...Array.from({length:days},(_,i) => addDays(start,i))]
})
const applicable = (day: string) => !!project.value && day <= today.value && day >= project.value.created && (!project.value.archived || day <= project.value.archived)
function shiftMonth(by: number) { const d = new Date(month.value + '-01T12:00:00Z'); d.setUTCMonth(d.getUTCMonth()+by); month.value = d.toISOString().slice(0,7) }
async function action(task: () => Promise<unknown>) {
  if (working.value) return
  working.value = true; message.value = ''
  try { await task() } catch (error) { message.value = (error as Error).message } finally { working.value = false }
}
async function saveProject() {
  await action(async () => {
    await manage(editing.value ? '/projects/' + editing.value : '/projects', {name:name.value,color:color.value,icon:icon.value.trim()},editing.value ? 'PUT' : 'POST')
    name.value = ''; icon.value = ''; editing.value = ''
  })
}
function edit(p: Project) { editing.value = p.id; name.value = p.name; icon.value = p.icon || ''; color.value = p.color }
async function archive(p: Project) {
  if (!window.confirm(`归档「${p.name}」？历史会保留，此后不再展示，也不能恢复。`)) return
  await action(() => manage('/projects/' + p.id + '/archive',{}))
}
async function move(p: Project, offset: number) {
  const ids = projects.value.map(p => p.id), index = ids.indexOf(p.id), target = index + offset
  if (target < 0 || target >= ids.length) return
  ;[ids[index],ids[target]] = [ids[target]!,ids[index]!]
  await action(() => manage('/projects/order',{ids},'PUT'))
}
async function restore(event: Event) {
  const input = event.target as HTMLInputElement, file = input.files?.[0]
  if (!file) return
  await action(async () => {
    if (file.size > 20000000) throw new Error('备份文件过大')
    const backup = JSON.parse(await file.text())
    if (backup.version !== 1 || !Array.isArray(backup.projects) || !Array.isArray(backup.completions)) throw new Error('备份格式不正确')
    if (!window.confirm(`将用备份中的 ${backup.projects.length} 个项目和 ${backup.completions.length} 条记录替换服务器数据。恢复前服务器会自动备份。是否继续？`)) return
    await manage('/restore',{backup})
  })
  input.value = ''
}
async function reset() {
  if (window.confirm('请先导出本地备份。重新载入会放弃此设备待同步记录，用服务器数据替换本地副本。')) await action(reloadServer)
}
function wake() { const previous = today.value; today.value = dayAt(); if (viewedDay.value === previous) viewedDay.value = today.value; if (document.visibilityState === 'visible') void sync() }
let timer: ReturnType<typeof setInterval>
onMounted(() => { void init(); timer = setInterval(wake,30000); window.addEventListener('online',wake); document.addEventListener('visibilitychange',wake) })
onUnmounted(() => { clearInterval(timer); window.removeEventListener('online',wake); document.removeEventListener('visibilitychange',wake) })
</script>

<template>
  <div class="app-shell">
    <header class="brand"><a href="#" @click.prevent="page='今日'" aria-label="pp daily 首页"><span class="wordmark">pp <em>daily</em></span></a><button class="icon-button" @click="page='管理'" aria-label="管理"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m10 3-.7 2.3-2 .9-2.2-.6-2 3.5 1.6 1.7v2.4L3.1 15l2 3.5 2.2-.6 2 .9.7 2.2h4l.7-2.2 2-.9 2.2.6 2-3.5-1.6-1.8v-2.4L21 9l-2-3.5-2.3.6-2-.9L14 3h-4Z"/><circle cx="12" cy="12" r="3"/></svg></button></header>
    <main>
      <div v-if="conflict" class="notice"><strong>服务器数据已恢复</strong><p>先保存本地备份，再载入新的服务器数据。</p><button @click="exportLocal">导出本地备份</button><button @click="reset">重新载入</button></div>
      <p v-if="message" class="error" role="alert">{{ message }}</p>
      <template v-if="page==='今日'">
        <section class="recent-heading"><h1>{{ Number(viewedDay.slice(0,4)) }} 年 {{ Number(viewedDay.slice(5,7)) }} 月</h1><span>{{ viewedDay === today ? '今天' : Number(viewedDay.slice(5,7))+' 月 '+Number(viewedDay.slice(8))+' 日' }} · 周{{ shortWeekday(viewedDay) }}</span></section>
        <nav class="recent-dates" aria-label="最近七天"><button v-for="day in recentDays" :key="day" :class="{selected:day===viewedDay,'actual-today':day===today}" :aria-label="day + (day===today ? ' 今天' : '')" :aria-pressed="day===viewedDay" @click="viewedDay=day"><small>{{ shortWeekday(day) }}</small><b>{{ Number(day.slice(8)) }}</b><i></i></button></nav>
        <section v-if="pendingProjects.length" class="project-group" aria-label="未完成项目">
          <SwipeComplete v-for="p in pendingProjects" :key="p.id + viewedDay" :name="p.name" :completed="false" :disabled="viewedDay !== today || working || !storageReady || conflict" @complete="action(() => complete(p.id))">
            <span class="project-avatar" :style="{'--avatar-color':p.color}" aria-hidden="true">{{ projectIcon(p) }}</span><h2 class="project-name">{{ p.name }}</h2><div class="project-streak"><strong>{{ streak(p) }}<small>天</small></strong><span>当前连续</span></div>
          </SwipeComplete>
        </section>
        <section v-if="completedProjects.length" class="completed-group project-group">
          <button class="completed-heading" :aria-expanded="completedOpen" @click="completedOpen=!completedOpen"><span>已完成</span><small>{{ completedProjects.length }} <svg viewBox="0 0 24 24" :class="{collapsed:!completedOpen}" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></small></button>
          <template v-if="completedOpen"><SwipeComplete v-for="p in completedProjects" :key="p.id" :name="p.name" :completed="true" :disabled="true"><span class="project-avatar completed-avatar" aria-hidden="true">✓</span><h2 class="project-name">{{ p.name }}</h2><div class="project-streak"><strong>{{ streak(p) }}<small>天</small></strong><span>当前连续</span></div></SwipeComplete></template>
        </section>
        <section v-if="!visibleProjects.length" class="empty"><h2>{{ viewedDay === today ? '暂无项目' : '当日暂无项目' }}</h2><button v-if="viewedDay === today" @click="page='管理'">添加项目</button></section>
      </template>
      <template v-else-if="page==='月历' || page==='统计'">
        <ProjectPicker :projects="projects" :selected="project?.id || ''" @select="selected=$event" />
        <section v-if="project && page==='月历'" class="calendar-paper">
          <div class="month-heading"><button class="icon-button" @click="shiftMonth(-1)" aria-label="上个月">‹</button><h2>{{ Number(month.slice(0,4)) }} 年 {{ Number(month.slice(5,7)) }} 月</h2><button class="icon-button" @click="shiftMonth(1)" aria-label="下个月">›</button></div>
          <div class="calendar-grid weekdays"><span v-for="d in ['一','二','三','四','五','六','日']" :key="d">{{ d }}</span></div>
          <div class="calendar-grid"><div v-for="(day,index) in cells" :key="index" class="day-cell" :class="{checked:day && done(project.id,day), muted:day && !applicable(day), today:day===today}" :aria-label="day ? day + (done(project.id,day) ? ' 已完成' : applicable(day) ? ' 未完成' : ' 不适用') : day"><span>{{ day ? Number(day.slice(8)) : '' }}</span><small v-if="day && done(project.id,day)">✓</small></div></div>
          <div class="legend"><span>● 已完成</span><span>○ 未完成</span><span class="subtle">— 不适用</span></div>
        </section>
        <section v-if="project && page==='统计'" class="stats-grid"><article v-for="(label,index) in statLabels" :key="label"><p>{{ label }}</p><strong>{{ stats[index] }}<small>天</small></strong></article></section>
        <p v-if="project && page==='统计'" class="end-note">今天未完成时，当前连续天数算到昨天。<br>归档项目算到归档当天。</p>
        <p v-if="!project" class="empty">还没有项目，去管理页创建一个吧。</p>
      </template>
      <template v-else>
        <section class="management-paper"><form @submit.prevent="saveProject"><label>项目名称<input v-model="name" maxlength="40" required placeholder="例如：阅读、散步、学英语"></label><label>图标文字<input v-model="icon" maxlength="1" :placeholder="Array.from(name.trim())[0] || '一个字，例如：读'" aria-describedby="icon-help"></label><p id="icon-help" class="subtle small">留空时使用项目名称的第一个字。</p><label class="color-row">项目颜色<input v-model="color" type="color" aria-label="项目颜色"></label><button class="primary" :disabled="working || conflict || !storageReady">{{ editing ? '保存修改' : '添加项目' }}</button><button v-if="editing" type="button" @click="editing='';name='';icon=''">取消编辑</button></form><p class="subtle small">项目管理需要连接服务器。</p></section>
        <section class="management-paper"><h2>我的项目 <small>{{ projects.length }}</small></h2><article v-for="(p,index) in projects" :key="p.id" class="project-row"><div><span class="color-dot" :style="{background:p.color}"></span><b>{{ p.name }}</b><small v-if="p.archived">已归档</small></div><div class="row-actions"><button :disabled="index===0 || working || conflict" @click="move(p,-1)" :aria-label="p.name+'上移'">↑</button><button :disabled="index===projects.length-1 || working || conflict" @click="move(p,1)" :aria-label="p.name+'下移'">↓</button><button v-if="!p.archived" :disabled="working || conflict" @click="edit(p)">编辑</button><button v-if="!p.archived" :disabled="working || conflict" @click="archive(p)">归档</button></div></article><p v-if="!projects.length" class="subtle">还没有项目。</p></section>
        <section class="management-paper"><h2>数据备份</h2><p class="subtle">完整备份包含此设备尚未同步的记录。<br>恢复会替换服务器数据，并自动保留恢复前备份。</p><div class="backup-actions"><button :disabled="!storageReady || !local.snapshot.generation" @click="exportLocal">导出完整备份 ↗</button><label class="file-button">恢复备份<input type="file" accept=".json,application/json" :disabled="working || conflict" @change="restore"></label></div></section>
        <section class="management-paper"><h2>连接与保存</h2><p>{{ status }}</p><p class="subtle">{{ local.pending.length }} 条待同步 · Asia/Shanghai</p><button :disabled="busy || conflict" @click="sync">立即同步</button><p class="subtle small">Safari → 分享 → 添加到主屏幕。<br>首次加载和同步需要私人网络连接；之后可以离线完成当天项目。</p></section>
      </template>
      <div class="sync-status" role="status"><i :class="{offline:local.pending.length || conflict}"></i>{{ busy ? '同步中…' : status }}</div>
    </main>
    <nav aria-label="主导航"><button v-for="(item,index) in ['今日','月历','统计']" :key="item" :class="{selected:page===item}" @click="page=item"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><template v-if="index===0"><rect x="4" y="4" width="16" height="16" rx="5"/><path d="m8 12 3 3 5-6"/></template><template v-else-if="index===1"><rect x="4" y="5" width="16" height="15" rx="4"/><path d="M8 3v4m8-4v4M4 10h16m-12 4h1m3 0h1m3 0h1m-9 3h1m3 0h1"/></template><template v-else><path d="M5 20V10m7 10V4m7 16v-7"/></template></svg>{{ item }}</button></nav>
  </div>
</template>
