const SUPABASE_URL = "https://ekkqbtvnktiorxgavknv.supabase.co";
const SUPABASE_KEY = "sb_publishable_BQpzrsXqalj1-TQ_jCgD8Q_oZGNrUOC";

window.supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_KEY
);

console.log("Supabase initialized");