<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { COMPLETION_THRESHOLD, SwipeGesture } from './swipe'

const props = defineProps<{ name: string; completed: boolean; disabled: boolean }>()
const emit = defineEmits<{ complete: [] }>()
const track = ref<HTMLElement>()
const progress = ref(0), travel = ref(0), dragging = ref(false), awaiting = ref(false)
const gesture = new SwipeGesture()
let pointer: number | null = null
const blocked = computed(() => props.completed || props.disabled || awaiting.value)
const ready = computed(() => progress.value >= COMPLETION_THRESHOLD)
const label = computed(() => props.completed ? '已完成' : awaiting.value ? '正在保存…' : ready.value ? (dragging.value ? '松开完成' : '按 Enter 完成') : '向右滑动完成')

function measure() {
  travel.value = Math.min(140, (track.value?.clientWidth || 0) * 0.45)
}
function cancel() {
  if (pointer !== null && track.value?.hasPointerCapture(pointer)) track.value.releasePointerCapture(pointer)
  pointer = null; dragging.value = false; progress.value = 0; gesture.cancel()
}
function start(event: PointerEvent) {
  if (blocked.value || pointer !== null || !event.isPrimary || event.button !== 0) return
  measure()
  gesture.begin(event.clientX,event.clientY,travel.value)
  pointer = event.pointerId; dragging.value = true
  track.value?.setPointerCapture(event.pointerId)
}
function move(event: PointerEvent) {
  if (pointer !== event.pointerId || blocked.value) return
  progress.value = gesture.move(event.clientX,event.clientY)
}
function finish(event: PointerEvent) {
  if (pointer !== event.pointerId) return
  gesture.move(event.clientX,event.clientY)
  const completed = !blocked.value && gesture.finish()
  cancel()
  if (completed) commit()
}
function commit() {
  if (blocked.value) return
  progress.value = 1; awaiting.value = true
  emit('complete')
}
function keyboard(event: KeyboardEvent) {
  if (blocked.value) return
  if (!['ArrowRight','ArrowLeft','Home','End','Enter',' ','Escape'].includes(event.key)) return
  event.preventDefault(); measure()
  if (event.key === 'ArrowRight') progress.value = Math.min(1,progress.value + 0.1)
  else if (event.key === 'ArrowLeft') progress.value = Math.max(0,progress.value - 0.1)
  else if (event.key === 'End') progress.value = 1
  else if (event.key === 'Home' || event.key === 'Escape') cancel()
  else if (ready.value && !event.repeat) commit()
}
watch(() => [props.completed,props.disabled], () => {
  if (props.completed || props.disabled) cancel()
  if (!props.disabled) awaiting.value = false
})
onMounted(() => window.addEventListener('resize',cancel))
onUnmounted(() => { window.removeEventListener('resize',cancel); cancel() })
</script>

<template>
  <div ref="track" class="swipe-row" :class="{'is-dragging':dragging,'is-ready':ready,'is-complete':completed,'is-disabled':disabled}" :style="{'--swipe-offset':progress * travel + 'px'}"
    :role="completed || disabled ? undefined : 'slider'" :tabindex="completed || disabled ? undefined : 0" :aria-label="completed || disabled ? undefined : name + '：整行向右滑动完成'" :aria-valuemin="completed || disabled ? undefined : 0" :aria-valuemax="completed || disabled ? undefined : 100" :aria-valuenow="completed || disabled ? undefined : Math.round(progress * 100)" :aria-valuetext="completed || disabled ? undefined : label" :aria-disabled="blocked" aria-orientation="horizontal"
    @pointerdown="start" @pointermove="move" @pointerup="finish" @pointercancel="cancel" @lostpointercapture="cancel" @keydown="keyboard" @blur="cancel" @contextmenu.prevent>
    <div v-if="!completed && !disabled" class="row-reveal" aria-hidden="true"><span>✓</span><small>{{ ready ? '松开完成' : '完成' }}</small></div>
    <div class="row-content"><slot /></div>
  </div>
</template>
