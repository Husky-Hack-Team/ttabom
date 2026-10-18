const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export const formatUsd = (v) => usd.format(Number(v || 0))
export const formatInt = (v) => Number(v).toLocaleString('en-US')
export const capitalize = (s) => (s ? s[0].toUpperCase() + s.slice(1) : '')

const dt = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' })
const tm = new Intl.DateTimeFormat('en-US', { timeStyle: 'short' })
export const formatDate = (v) => (v ? dt.format(new Date(v)) : '')
export const formatTime = (v) => (v ? tm.format(new Date(v)) : '')
