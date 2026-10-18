-- Transactions used by the FastAPI backend (backend/api/index.py).
create table if not exists public.transactions (
  id bigint generated always as identity primary key,
  description text not null,
  amount numeric(12, 2) not null,
  created_at timestamptz not null default now()
);

-- Speeds up "newest first" listing.
create index if not exists transactions_created_at_idx
  on public.transactions (created_at desc, id desc);

-- The backend uses the service role key, which bypasses RLS. Enabling RLS with
-- no policies keeps the table closed to the public anon key.
alter table public.transactions enable row level security;
