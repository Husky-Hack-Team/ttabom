<script setup>
import demo from '~/data/demo.json'
import PhoneTwoViews from '~/components/phone/PhoneTwoViews.vue'

const emit = defineEmits(['go'])
const { scam } = demo
const p = scam.payment
const contact = scam.contact

const view = ref('linda') // linda | tommy
const answer = ref(null) // null | yes | no
</script>

<template>
  <StepLayout
    :number="3"
    wide
    title="Two views: the member and the employee"
    :data="['contacts_overlay', 'recipients_overlay', 'recipient_numbers', 'payment_rail', 'days_since_last_same_rail']"
    next="Legit path"
    @next="emit('go', 4)"
  >
    <template #explain>
      <p>
        {{ contact.name }} sees only the amount, the bank and the last 4 digits, and answers one question: is this your account? The answer goes
        to {{ scam.member_name }}. {{ contact.name }} can’t approve or cancel anything.
      </p>
      <p>
        At the same time a Sound employee gets a case with the hold timer, the mismatch, and a calm, non-judgmental way to open the conversation.
      </p>
      <p class="text-base text-muted">Switch phones below, tap {{ contact.name }}’s answer, and watch both screens update.</p>
    </template>

    <div class="w-full max-w-[390px]">
      <div class="mb-4 flex justify-center">
        <div class="inline-flex rounded-full border-2 border-line bg-white p-1" role="group" aria-label="Whose phone">
          <button
            v-for="v in [{ id: 'linda', label: scam.member_name }, { id: 'tommy', label: contact.name }]"
            :key="v.id"
            type="button"
            class="min-h-[44px] rounded-full px-6 text-lg font-semibold"
            :class="view === v.id ? 'bg-navy text-white' : 'text-accent'"
            :aria-pressed="view === v.id ? 'true' : 'false'"
            @click="view = v.id"
          >
            {{ v.label }}
          </button>
        </div>
      </div>

      <PhoneFrame :label="view === 'tommy' ? `${contact.name}'s phone` : `${scam.member_name}'s phone`" :time="p.time_label.replace(/ [AP]M/, '')">
        <PhoneTwoViews v-model:view="view" v-model:answer="answer" @go="emit('go', $event)" />
      </PhoneFrame>
    </div>
    <EmployeeCase :answer="answer" />
  </StepLayout>
</template>
