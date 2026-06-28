--only run this once if you intentionally want to delete data.

DROP TABLE IF EXISTS news_articles CASCADE;
DROP TABLE IF EXISTS nlp_queries CASCADE;
DROP TABLE IF EXISTS destination_scores CASCADE;
DROP TABLE IF EXISTS destination_map_scores CASCADE;
DROP TABLE IF EXISTS map_advisories CASCADE;
DROP TABLE IF EXISTS destinations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE EXTENSION IF NOT EXISTS vector;

-- Store user accounts--
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PARENTS destinations --
CREATE TABLE destinations (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(3) NOT NULL UNIQUE,
    country_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    latitude NUMERIC,
    longitude NUMERIC,
    news_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- destination scores for destination dashbaord --
CREATE TABLE destination_scores (
    id SERIAL PRIMARY KEY,
    destination_id INTEGER NOT NULL UNIQUE REFERENCES destinations(id) ON DELETE CASCADE,
    travel_score INTEGER NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    condition_summary TEXT,
    weather_summary TEXT,
    advisory_summary TEXT,
    news_summary TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- map scores for map coloring and tooltip --
CREATE TABLE destination_map_scores (
    id SERIAL PRIMARY KEY,
    destination_id INTEGER NOT NULL UNIQUE REFERENCES destinations(id) ON DELETE CASCADE,
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    map_score INTEGER,
    risk_level VARCHAR(50),
    condition_summary TEXT,
    advisory_level INTEGER,
    advisory_summary TEXT,
    source VARCHAR(100),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- for nlp --
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,

    title TEXT NOT NULL,
    original_description TEXT,
    url TEXT,
    source_name VARCHAR(100),
    published_at TIMESTAMPTZ,

    is_relevant BOOLEAN DEFAULT FALSE,
    abstracted_summary TEXT,
    embedding VECTOR(768),
    rank_position INTEGER,

    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    UNIQUE(destination_id, url)
);

-- for nlp --
CREATE TABLE nlp_queries (
    id SERIAL PRIMARY KEY,
    query_name VARCHAR(100) NOT NULL UNIQUE,
    query_text TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);