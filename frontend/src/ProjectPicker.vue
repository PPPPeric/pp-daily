<script setup lang="ts">
import { computed, ref } from 'vue'
import { projectIcon, type Project } from './domain'
const props = defineProps<{ projects: Project[]; selected: string }>()
const emit = defineEmits<{ select: [id: string] }>()
const panel = ref<HTMLDialogElement>()
const current = computed(() => props.projects.find(p => p.id === props.selected))
function choose(id: string) { emit('select',id); panel.value?.close() }
</script>

<template>
  <button class="picker-trigger" aria-label="选择项目" aria-haspopup="dialog" :disabled="!projects.length" @click="panel?.showModal()">
    <span class="picker-avatar" :style="{color:current?.color}" aria-hidden="true">{{ current ? projectIcon(current) : 'p' }}</span>
    <span class="picker-name">{{ current?.name || '暂无项目' }}<small v-if="current?.archived">已归档</small></span>
    <svg class="picker-chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5"/></svg>
  </button>
  <dialog ref="panel" class="project-picker-panel" aria-label="选择项目" @click="($event.target === panel) && panel?.close()">
    <div class="picker-sheet">
      <header><h2>选择项目</h2><button aria-label="关闭项目选择" @click="panel?.close()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 7 10 10M7 17 17 7"/></svg></button></header>
      <div class="picker-options">
        <button v-for="p in projects" :key="p.id" :aria-pressed="p.id===selected" :class="{chosen:p.id===selected}" @click="choose(p.id)">
          <span class="picker-avatar" :style="{color:p.color}" aria-hidden="true">{{ projectIcon(p) }}</span>
          <span class="picker-name">{{ p.name }}<small v-if="p.archived">已归档</small></span><svg v-if="p.id===selected" class="picker-check" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4 10-10"/></svg>
        </button>
      </div>
    </div>
  </dialog>
</template>

<style scoped>
svg{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.picker-trigger{width:100%;display:flex;align-items:center;gap:12px;min-height:68px;background:#fffdf7;border:1px solid #e3e4d8;border-radius:20px;padding:12px 16px;margin-bottom:20px;text-align:left;color:#294535}
.picker-avatar{font-size:17px;font-weight:500;width:36px;height:36px;border-radius:50%;background:#e8eddf;display:grid;place-items:center;flex-shrink:0}.picker-avatar svg{width:21px;height:21px}.picker-name{font-size:16px;flex:1;min-width:0;overflow-wrap:anywhere}.picker-name small{display:block;font-size:10px;color:#788276;margin-top:3px}.picker-chevron{width:20px;height:20px;color:#788276;flex-shrink:0}
.project-picker-panel{padding:0;border:0;background:transparent;color:#294535;width:calc(100% - 24px);max-width:492px;margin:auto auto max(12px,env(safe-area-inset-bottom));overflow:visible;max-height:none}.project-picker-panel::backdrop{background:#1f362959;backdrop-filter:blur(3px)}.picker-sheet{background:#f7f4ec;border-radius:26px;box-shadow:0 20px 60px #15251c2b;padding:12px 12px 16px}.picker-sheet header{display:flex;align-items:center;justify-content:space-between;padding:0 8px 9px 12px}.picker-sheet h2{font-size:15px;font-weight:500}.picker-sheet header button{width:44px;height:44px;display:grid;place-items:center;padding:10px;border:0;border-radius:50%;color:#788276}.picker-sheet header svg{width:20px;height:20px}.picker-options{max-height:60dvh;overflow:auto;overscroll-behavior:contain;display:grid;gap:4px}.picker-options button{display:flex;align-items:center;gap:12px;padding:12px;min-height:62px;border:0;border-radius:16px;color:#294535;text-align:left}.picker-options button.chosen{background:#e8eddf}.picker-options button.chosen .picker-avatar{background:#fffdf7}.picker-check{width:21px;height:21px;color:#315b43;flex-shrink:0}
@media(min-width:600px){.project-picker-panel{margin:auto;max-width:420px}}
</style>
