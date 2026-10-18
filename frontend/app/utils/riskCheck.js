// Custom-recipient check for /prototype: plain rules, no model.
// Every answer leads to the same "Take a moment before you send" screen; the
// answer only changes the wording, and the signals explain what we noticed.

export const KNOW_ANSWERS = [
  {
    id: 'in_person',
    label: 'Yes, I know them in person',
    signal: 'You know them in person',
    caution: 'New account. Double-check the account number with them directly.'
  },
  {
    id: 'online',
    label: 'I only know them online / by phone',
    signal: 'You only know them online or by phone',
    caution: 'People you’ve only met online or by phone are the most common source of scams.'
  },
  {
    id: 'told',
    label: 'Someone told me to send money here',
    signal: 'Someone told you to send money here',
    caution: 'If someone is pressuring you to send money, it’s likely a scam. Sound will never ask you to move money.'
  },
  // "Not sure" keeps the screen's standard tips with no extra line.
  { id: 'unsure', label: 'Not sure', signal: 'You’re not sure who they are', caution: '' }
]

export const HIGH_AMOUNT_MULTIPLE = 2

// What the "Take a moment" screen lists: always a new account, the answer, and
// the amount compared with Linda's typical payment (high = more than 2×).
export function customSignals({ answer, amount, typical }) {
  const known = KNOW_ANSWERS.find((a) => a.id === answer)
  const ratio = typical > 0 ? amount / typical : 0
  const highAmount = ratio > HIGH_AMOUNT_MULTIPLE
  return [
    { id: 'new', text: 'New account: you’ve never paid it before', warn: true },
    { id: 'answer', text: known ? known.signal : 'You didn’t say how you know them', warn: answer !== 'in_person' },
    highAmount
      ? { id: 'amount', text: `Higher than your usual amount (about ${ratio.toFixed(1)}× your typical payment)`, warn: true }
      : { id: 'amount', text: 'Within your usual amount', warn: false }
  ]
}
