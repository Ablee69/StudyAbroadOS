-- Run this once in Supabase SQL Editor.
-- It lets all signed-in users view shared program rows, while only the creator
-- can edit or delete them.

alter table public.programs add column if not exists source_url text;
alter table public.programs add column if not exists verified_date date;
alter table public.programs add column if not exists is_shared boolean not null default false;
create index if not exists idx_programs_shared_deadline on public.programs(is_shared, deadline);

drop policy if exists programs_select_own on public.programs;
drop policy if exists programs_select_accessible on public.programs;
drop policy if exists programs_insert_own on public.programs;
drop policy if exists programs_update_own on public.programs;
drop policy if exists programs_delete_own on public.programs;

create policy programs_select_accessible on public.programs
for select using (
  auth.uid() = user_id
  or (auth.role() = 'authenticated' and is_shared = true)
);
create policy programs_insert_own on public.programs for insert with check (auth.uid() = user_id);
create policy programs_update_own on public.programs for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy programs_delete_own on public.programs for delete using (auth.uid() = user_id);

-- Optional: if you already imported the 30 GPT-sourced school rows and want
-- every signed-in user to see them, run this too.
-- update public.programs set is_shared = true where source_url is not null and verified_date is not null;
