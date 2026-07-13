const SUPABASE_URL = "https://ekkqbtvnktiorxgavknv.supabase.co";
const SUPABASE_KEY = "sb_publishable_BQpzrsXqalj1-TQ_jCgD8Q_oZGNrUOC";

window.supabaseClient = null;

if (!window.supabase) {
  console.error("Supabase library did not load. Check your internet connection.");
} else {
  window.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true
    }
  });
}
