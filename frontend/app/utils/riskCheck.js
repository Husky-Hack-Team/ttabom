// Deterministic risk check for a payment to a new (custom) account in /prototype.
// Plain rules, no model: the same inputs always give the same level.
//
//   answer \ amount        normal (≤ 2× typical)   high (> 2× typical)
//   in_person              low                     medium
//   unsure                 medium                  high
//   online                 high                    high
//   told                   high                    high

export const KNOW_ANSWERS = [
  { id: 'in_person', label: 'Yes, I know them in person', signal: 'You know them in person' },
  { id: 'online', label: 'I only know them online / by phone', signal: 'You only know them online or by phone' },
  { id: 'told', label: 'Someone told me to send money here', signal: 'Someone told you to send money here' },
  { id: 'unsure', label: 'Not sure', signal: 'You’re not sure who they are' }
]

export const HIGH_AMOUNT_MULTIPLE = 2

export function riskCheck({ answer, amount, typical }) {
  const known = KNOW_ANSWERS.find((a) => a.id === answer)
  const ratio = typical > 0 ? amount / typical : 0
  const highAmount = ratio > HIGH_AMOUNT_MULTIPLE
  let level
  if (answer === 'online' || answer === 'told') level = 'high'
  else if (answer === 'unsure') level = highAmount ? 'high' : 'medium'
  else level = highAmount ? 'medium' : 'low'

  const signals = [
    { id: 'new', text: 'New account: you’ve never paid it before', warn: true },
    { id: 'answer', text: known ? known.signal : 'You didn’t say how you know them', warn: answer !== 'in_person' },
    highAmount
      ? { id: 'amount', text: `Higher than your usual amount (about ${ratio.toFixed(1)}× your typical payment)`, warn: true }
      : { id: 'amount', text: 'Within your usual amount', warn: false }
  ]
  return { level, highAmount, ratio, signals }
}
