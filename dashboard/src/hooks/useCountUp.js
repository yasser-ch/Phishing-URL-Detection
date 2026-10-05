import { useEffect, useState, useRef } from "react"

export function useCountUp(target, duration = 800) {
  const [value, setValue] = useState(0)
  const frameRef = useRef()
  const startRef = useRef(null)

  useEffect(() => {
    if (target == null || isNaN(target)) return
    startRef.current = null

    const step = (timestamp) => {
      if (startRef.current === null) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step)
      }
    }

    frameRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frameRef.current)
  }, [target, duration])

  return value
}