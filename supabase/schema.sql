-- supabase/schema.sql
-- Run this SQL in your Supabase SQL editor to create needed tables

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  clerk_user_id text unique,
  created_at timestamptz default now()
);

create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  clerk_user_id text references users(clerk_user_id) on delete set null,
  filename text,
  content text,
  created_at timestamptz default now()
);

create table if not exists interviews (
  id text primary key,
  clerk_user_id text references users(clerk_user_id) on delete cascade,
  mode text, -- 'role' or 'resume'
  role text,
  difficulty text,
  experience_level text,
  resume_id uuid references resumes(id),
  created_at timestamptz default now()
);

create table if not exists transcripts (
  id uuid primary key default gen_random_uuid(),
  interview_id text references interviews(id) on delete cascade,
  actor text, -- 'ai' or 'user'
  text text,
  created_at timestamptz default now()
);

create table if not exists analysis_reports (
  id uuid primary key default gen_random_uuid(),
  interview_id text references interviews(id) on delete cascade,
  strengths text[],
  weaknesses text[],
  improvements text,
  resources text[],
  created_at timestamptz default now()
);
