const SUPABASE_URL = "https://TON-PROJET.supabase.co";

const SUPABASE_KEY = "TON-PUBLISHABLE-KEY";

const supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_KEY
);