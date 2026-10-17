create table if not exists public.camping_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  campground_id text not null,
  campground_name text not null,
  campground_address text not null default '',
  region_id text not null,
  plan_date date not null,
  campground_data jsonb not null,
  created_at timestamptz not null default now(),
  unique (user_id, campground_id, plan_date)
);

alter table public.camping_plans enable row level security;

create policy "Users can read their own camping plans"
  on public.camping_plans for select
  using (auth.uid() = user_id);

create policy "Users can insert their own camping plans"
  on public.camping_plans for insert
  with check (auth.uid() = user_id);

create policy "Users can delete their own camping plans"
  on public.camping_plans for delete
  using (auth.uid() = user_id);

create index if not exists camping_plans_user_date_idx
  on public.camping_plans (user_id, plan_date);

create table if not exists public.regional_forecast_mapping (
  region_id text primary key,
  region_name text not null,
  map_x double precision not null,
  map_y double precision not null,
  land_reg_id text not null,
  temperature_reg_id text not null
);

insert into public.regional_forecast_mapping
  (region_id, region_name, map_x, map_y, land_reg_id, temperature_reg_id)
values
  ('seoul', '서울', 126.9780, 37.5665, '11B00000', '11B10101'),
  ('gyeonggi', '경기', 127.0286, 37.2636, '11B00000', '11B20601'),
  ('gangneung', '강원도', 128.8761, 37.7519, '11D20000', '11D20501'),
  ('daejeon', '대전', 127.3845, 36.3504, '11C20000', '11C20401'),
  ('gwangju', '광주', 126.8526, 35.1595, '11F20000', '11F20501'),
  ('daegu', '대구', 128.6014, 35.8714, '11H10000', '11H10701'),
  ('busan', '부산', 129.0756, 35.1796, '11H20000', '11H20201'),
  ('jeju', '제주', 126.5312, 33.4996, '11G00000', '11G00201')
on conflict (region_id) do update set
  region_name = excluded.region_name,
  map_x = excluded.map_x,
  map_y = excluded.map_y,
  land_reg_id = excluded.land_reg_id,
  temperature_reg_id = excluded.temperature_reg_id;
