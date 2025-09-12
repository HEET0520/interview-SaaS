-- Create users table to store public user data synced from Clerk
-- The user_id is the primary key and matches Clerk's user ID.
create table users (
    id text primary key, -- Clerk User ID
    name text,
    email text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create resumes table
create table resumes (
    id uuid primary key default gen_random_uuid(),
    user_id text references users(id) on delete cascade not null,
    file_name text not null,
    resume_text text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create interviews table to store session data and transcripts
create table interviews (
    id uuid primary key default gen_random_uuid(),
    user_id text references users(id) on delete cascade not null,
    resume_id uuid references resumes(id) on delete set null,
    interview_type text not null, -- 'role-based' or 'resume-based'
    role text,
    difficulty text,
    experience text,
    transcript jsonb, -- To store the full Q&A transcript with scores
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create analysis_reports table to store the final AI-generated report
create table analysis_reports (
    id uuid primary key default gen_random_uuid(),
    interview_id uuid references interviews(id) on delete cascade not null,
    strengths text,
    weaknesses text,
    improvement_suggestions text,
    recommended_resources text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    constraint unique_interview_id unique (interview_id)
);