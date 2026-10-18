// Static data for /prototype only: Linda's recipient picker and the custom
// recipient risk check. Margaret and Daniel are fictional; their account numbers
// are made up, with routing numbers in the unassigned 9x range (valid checksum,
// belongs to no real institution). Tommy reuses the walkthrough's synthetic data so his story is
// unchanged.
import demo from '~/data/demo.json'

const { scam } = demo
const tommy = scam.contact

export const RECIPIENTS = [
  {
    id: 'tommy',
    name: tommy.name,
    firstName: tommy.name,
    relationship: 'Grandson',
    possessive: 'his',
    subject: 'he',
    memberRole: 'grandmother', // who Linda is to them, for Sound's call script
    phone_masked: tommy.phone_masked,
    phone_on_file_since_label: tommy.phone_on_file_since_label,
    verified_accounts: tommy.verified_accounts,
    // The scam story: the account number the caller gave Linda.
    differentAccount: { ...scam.payment.recipient, label: 'Try the number the caller gave' }
  },
  {
    id: 'margaret',
    name: 'Margaret Lee',
    firstName: 'Margaret',
    relationship: 'Sister',
    possessive: 'her',
    subject: 'she',
    memberRole: 'sister',
    phone_masked: '(•••) •••-2187',
    phone_on_file_since_label: 'Mar 2019',
    verified_accounts: [{ routing_number: '914071552', account_number: '4410395520', account_masked: '••••5520' }],
    differentAccount: { routing_number: '925000321', account_number: '7782014469', account_masked: '••••4469', label: 'Try a different account' }
  },
  {
    id: 'daniel',
    name: 'Daniel Brooks',
    firstName: 'Daniel',
    relationship: 'Neighbor',
    possessive: 'their',
    subject: 'they',
    memberRole: 'neighbor',
    phone_masked: '(•••) •••-6034',
    phone_on_file_since_label: 'Jun 2022',
    verified_accounts: [{ routing_number: '931004515', account_number: '2209871306', account_masked: '••••1306' }],
    differentAccount: { routing_number: '943072917', account_number: '6650042288', account_masked: '••••2288', label: 'Try a different account' }
  }
]

export const recipientById = (id) => RECIPIENTS.find((r) => r.id === id) ?? RECIPIENTS[0]

// One-tap sample for "+ Custom recipient".
export const CUSTOM_SAMPLE = { name: 'Alex Kim', routing: '954021766', account: '3301457790', amount: '400' }

// Linda's typical payment: the dataset's 12-month 90th-percentile outgoing
// payment, recovered from the $8,500 wire and its amount_to_baseline_ratio.
export const TYPICAL_PAYMENT = Math.round(scam.payment.amount / scam.payment.amount_to_baseline_ratio)
