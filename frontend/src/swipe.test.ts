import { describe, expect, it } from 'vitest'
import { SwipeGesture } from './swipe'

describe('swipe completion gesture', () => {
  it('does not complete on a tap or a short drag', () => {
    const gesture = new SwipeGesture()
    gesture.begin(20,50,240); expect(gesture.finish()).toBe(false)
    gesture.begin(20,50,240); gesture.move(100,52); expect(gesture.finish()).toBe(false)
  })
  it('requires a rightward drag reaching the threshold on release', () => {
    const gesture = new SwipeGesture()
    gesture.begin(20,50,240); gesture.move(228,54); expect(gesture.finish()).toBe(true)
    expect(gesture.finish()).toBe(false)
  })
  it('does not complete when dragged back before release', () => {
    const gesture = new SwipeGesture()
    gesture.begin(20,50,240); gesture.move(260,52); gesture.move(120,52)
    expect(gesture.finish()).toBe(false)
  })
  it('cancels vertical scrolling even if the gesture later moves right', () => {
    const gesture = new SwipeGesture()
    gesture.begin(20,50,240); gesture.move(23,90); gesture.move(270,92)
    expect(gesture.finish()).toBe(false)
  })
  it('rejects leftward and cancelled gestures', () => {
    const gesture = new SwipeGesture()
    gesture.begin(20,50,240); expect(gesture.move(-40,50)).toBe(0); expect(gesture.finish()).toBe(false)
    gesture.begin(20,50,240); gesture.move(270,50); gesture.cancel(); expect(gesture.finish()).toBe(false)
  })
  it('handles resize travel and clamps overshoot', () => {
    const gesture = new SwipeGesture()
    gesture.begin(20,50,120); expect(gesture.move(300,50)).toBe(1); expect(gesture.finish()).toBe(true)
    gesture.begin(20,50,0); gesture.move(300,50); expect(gesture.finish()).toBe(false)
  })
})
