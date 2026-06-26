-- Run this once in Supabase SQL Editor if your programs table already exists.
alter table public.programs add column if not exists source_url text;
alter table public.programs add column if not exists verified_date date;
