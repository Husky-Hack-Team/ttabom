-- Sample rows. Applied by `supabase db reset` (local) or `supabase db push --include-seed` (remote).
insert into public.transactions (description, amount, created_at) values
  ('Opening deposit', 2500.00, now() - interval '5 days'),
  ('Grocery store', -84.32, now() - interval '4 days'),
  ('Coffee shop', -4.75, now() - interval '3 days'),
  ('Paycheck', 1850.00, now() - interval '2 days'),
  ('Electric bill', -112.40, now() - interval '1 day');
