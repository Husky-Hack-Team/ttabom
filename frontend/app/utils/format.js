const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export const formatUsd = (v) => usd.format(Number(v || 0))
export const formatInt = (v) => Number(v).toLocaleString('en-US')
export const capitalize = (s) => (s ? s[0].toUpperCase() + s.slice(1) : '')
