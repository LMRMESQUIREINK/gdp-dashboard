-- Creator Empire AI -- Cloud Edition schema.
-- Never run against a live Supabase project from this sandbox (no
-- project exists here) -- written against Supabase's real, documented
-- RLS pattern (auth.uid() against an owner_id column) and checked by
-- reading, not by executing against a live database.

create table if not exists public.projects (
  project_id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  brand text not null check (char_length(brand) between 1 and 200),
  product text not null check (char_length(product) between 1 and 200),
  audience text not null check (char_length(audience) between 1 and 200),
  benefit text not null check (char_length(benefit) between 1 and 200),
  duration_seconds smallint not null check (duration_seconds in (15, 40, 60)),
  aspect_ratio text not null check (aspect_ratio in ('9:16', '1:1', '16:9')),
  modules jsonb not null default '{
    "hooks": [], "selected_hook": null, "sales_script": [],
    "storyboard": [], "beat_map": null, "ad_creatives": []
  }'::jsonb,
  status text not null default 'draft' check (status in ('draft', 'ready', 'exported')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists projects_owner_id_idx on public.projects(owner_id);

alter table public.projects enable row level security;

-- A user can only ever see, insert, update, or delete their own rows.
-- The service-role key used by the server-side Supabase client
-- (lib/supabase.ts's createServerSupabaseClient) bypasses RLS entirely,
-- which is exactly why that client is server-only and never shipped to
-- the browser.

create policy "select own projects"
  on public.projects for select
  using (auth.uid() = owner_id);

create policy "insert own projects"
  on public.projects for insert
  with check (auth.uid() = owner_id);

create policy "update own projects"
  on public.projects for update
  using (auth.uid() = owner_id)
  with check (auth.uid() = owner_id);

create policy "delete own projects"
  on public.projects for delete
  using (auth.uid() = owner_id);

-- Keep updated_at honest without trusting the client to set it.
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger projects_set_updated_at
  before update on public.projects
  for each row execute function public.set_updated_at();
