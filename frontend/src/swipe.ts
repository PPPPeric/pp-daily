export const COMPLETION_THRESHOLD = 0.86

/** A gesture must start on the project row and move predominantly to the right. */
export class SwipeGesture {
  private originX = 0
  private originY = 0
  private travel = 0
  private direction: 'pending' | 'horizontal' | 'cancelled' = 'cancelled'
  progress = 0

  begin(x: number, y: number, travel: number) {
    this.originX = x
    this.originY = y
    this.travel = Number.isFinite(travel) ? Math.max(0, travel) : 0
    this.progress = 0
    this.direction = this.travel > 0 ? 'pending' : 'cancelled'
  }

  move(x: number, y: number) {
    if (this.direction === 'cancelled') return 0
    const dx = x - this.originX, dy = y - this.originY
    if (!Number.isFinite(dx) || !Number.isFinite(dy)) { this.cancel(); return 0 }
    if (this.direction === 'pending') {
      if (Math.max(Math.abs(dx), Math.abs(dy)) < 8) return 0
      if (Math.abs(dy) > Math.abs(dx)) { this.cancel(); return 0 }
      this.direction = 'horizontal'
    }
    this.progress = Math.min(1, Math.max(0, dx / this.travel))
    return this.progress
  }

  finish() {
    const completed = this.direction === 'horizontal' && this.progress >= COMPLETION_THRESHOLD
    this.cancel()
    return completed
  }

  cancel() { this.direction = 'cancelled'; this.progress = 0 }
}
