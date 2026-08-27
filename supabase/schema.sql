-- Execute no SQL Editor do Supabase antes de habilitar a sincronização.
create table if not exists public.radar_desk_changes (
    entity_type text not null,
    entity_id text not null,
    operation text not null,
    payload jsonb not null default '{}'::jsonb,
    local_version integer not null default 1,
    updated_at timestamptz not null default now(),
    primary key (entity_type, entity_id)
);

alter table public.radar_desk_changes enable row level security;

-- Para produção, substitua esta política por regras vinculadas aos usuários do projeto.
create policy "radar_desk_authenticated_access"
on public.radar_desk_changes
for all
to authenticated
using (true)
with check (true);
