-- Data replay tables for the Verified Contact Payment check (analysis/replay.py).
-- Synthetic data, about 41% scam victims by design. Not a measure of real-world performance.
-- Loaded by analysis/load_supabase.py (idempotent upserts). RLS is on with no
-- policies, so only the backend's service role can read them.

-- What Sound could observe: the HuskyHack v2 events, unchanged.
create table if not exists public.sim_events (
  event_id text primary key,
  synthetic_member_id text not null,
  event_sequence integer not null,
  event_timestamp timestamp not null,
  day_of_week text,
  event_category text,
  event_type text not null,
  channel text,
  payment_id text,
  payment_rail text,
  amount numeric(12, 2),
  transaction_direction text,
  recipient_id text,
  recipient_status text,
  recipient_age_days integer,
  days_since_last_same_rail integer,
  amount_to_baseline_ratio numeric,
  amount_vs_member_baseline text,
  payment_velocity_band text,
  available_balance_after numeric(12, 2),
  profile_change_recent text,
  password_reset_recent text,
  trusted_contact_enrolled text,
  warning_displayed text,
  member_response text,
  employee_interaction text,
  case_open text,
  payment_status text,
  event_note text
);
create index if not exists sim_events_member_seq_idx on public.sim_events (synthetic_member_id, event_sequence);
create index if not exists sim_events_payment_idx on public.sim_events (payment_id);

-- Ground truth. Used for scoring only; never returned by a member-facing endpoint.
create table if not exists public.sim_member_key (
  synthetic_member_id text primary key,
  anchor_persona text,
  scenario_type text,
  scenario_subtype text,
  is_legitimate_lookalike text,
  journey_summary text,
  incident_start timestamp,
  first_intervention timestamp,
  journey_outcome text,
  scam_payment_ids text,
  dollars_attempted numeric(12, 2),
  dollars_sent numeric(12, 2),
  dollars_prevented numeric(12, 2),
  dollars_recovered numeric(12, 2),
  net_member_loss numeric(12, 2),
  intervention_candidate text
);

-- One row per Payment Initiated event: our check next to what happened.
create table if not exists public.sim_decisions (
  payment_id text primary key,
  synthetic_member_id text not null,
  event_timestamp timestamp not null,
  channel text,
  payment_rail text,
  amount numeric(12, 2),
  recipient_id text,
  recipient_status text,
  decision text not null,
  reasons jsonb not null default '[]',
  contact_asked jsonb,
  hold_window text,
  signals_used jsonb not null default '[]',
  -- Scoring columns below come from the Member Key via the oracle.
  is_scam_payment boolean not null,
  member_group text not null,
  simulated_answer text,
  paused_before_money_moved boolean not null,
  friction_minutes integer not null,
  stop_probability numeric,
  expected_dollars_stopped numeric(12, 2),
  actual_final_status text,
  actual_money_moved boolean,
  actual_intervened boolean,
  actual_member_response text,
  actual_first_intervention_ts timestamp,
  disclaimer text not null
);
create index if not exists sim_decisions_member_idx on public.sim_decisions (synthetic_member_id, event_timestamp);

create table if not exists public.sim_member_summary (
  synthetic_member_id text primary key,
  anchor_persona text,
  member_group text not null,
  scenario_type text,
  scenario_subtype text,
  payments_initiated integer,
  scam_payments integer,
  scam_payments_paused integer,
  scam_dollars_attempted numeric(12, 2),
  scam_dollars_paused numeric(12, 2),
  expected_dollars_stopped numeric(12, 2),
  key_dollars_attempted numeric(12, 2),
  key_dollars_sent numeric(12, 2),
  key_dollars_prevented numeric(12, 2),
  key_journey_outcome text,
  incident_start timestamp,
  key_first_intervention timestamp,
  our_first_intervention timestamp,
  key_minutes_to_intervention integer,
  our_minutes_to_intervention integer,
  payments_flagged integer,
  non_scam_payments_flagged integer,
  friction_minutes integer,
  non_scam_friction_minutes integer,
  decisions text,
  disclaimer text not null
);
create index if not exists sim_member_summary_group_idx on public.sim_member_summary (member_group);

create table if not exists public.sim_metrics (
  id text primary key,
  metrics jsonb not null,
  walkthroughs text,
  loaded_at timestamptz not null default now()
);

alter table public.sim_events enable row level security;
alter table public.sim_member_key enable row level security;
alter table public.sim_decisions enable row level security;
alter table public.sim_member_summary enable row level security;
alter table public.sim_metrics enable row level security;
