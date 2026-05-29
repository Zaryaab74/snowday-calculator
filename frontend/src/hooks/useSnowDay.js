import { useState, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export function useSnowDay() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  // ── Auto Mode ──────────────────────────────────────────────────────────────
  const predict = useCallback(async ({ zipCode, snowDaysThisYear, schoolType }) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          zip_code:            zipCode,
          snow_days_this_year: Number(snowDaysThisYear),
          school_type:         schoolType,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Something went wrong')
      }
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Manual Mode ────────────────────────────────────────────────────────────
  const predictManual = useCallback(async (formData) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const res = await fetch(`${API_BASE}/predict/manual`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          storm_type:          formData.stormType,
          storm_chance:        Number(formData.stormChance),
          start_period:        formData.startPeriod,
          end_period:          formData.endPeriod,
          temp_f:              Number(formData.tempF),
          day_of_week:         formData.dayOfWeek,
          school_type:         formData.schoolType,
          snow_days_this_year: Number(formData.snowDaysThisYear),
          leniency:            formData.leniency,
          mountainous:         formData.mountainous,
          special_event:       formData.specialEvent,
          hype:                Number(formData.hype),
          country:             formData.country,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Something went wrong')
      }
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  return { data, loading, error, predict, predictManual }
}
