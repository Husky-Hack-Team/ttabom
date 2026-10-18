-- One-file version of supabase/migrations + supabase/seed.sql, for pasting into
-- the Supabase SQL Editor. Prefer `supabase db push` (see README).
create table if not exists public.transactions (
  id bigint generated always as identity primary key,
  description text not null,
  amount numeric(12, 2) not null,
  created_at timestamptz not null default now()
);

-- The backend uses the service role key, which bypasses RLS. Enabling RLS with
-- no policies keeps the table closed to the public anon key.
create index if not exists transactions_created_at_idx
  on public.transactions (created_at desc, id desc);

alter table public.transactions enable row level security;

insert into public.transactions (description, amount, created_at) values
  ('Opening deposit', 2500.00, now() - interval '5 days'),
  ('Grocery store', -84.32, now() - interval '4 days'),
  ('Coffee shop', -4.75, now() - interval '3 days'),
  ('Paycheck', 1850.00, now() - interval '2 days'),
  ('Electric bill', -112.40, now() - interval '1 day');
