let currentUser = null;

function showMessage(text, type = "error") {
  const box = document.getElementById("message");
  if (!box) return;
  box.textContent = text;
  box.className = `message ${type}`;
}

function initials(email) {
  return (email || "SS")
    .split("@")[0]
    .split(/[._-]/)
    .filter(Boolean)
    .map(part => part[0].toUpperCase())
    .join("")
    .substring(0, 2) || "SS";
}

async function loadProfile() {
  if (!window.supabaseClient) {
    showMessage("Login is not ready. Refresh the page.");
    return;
  }

  const { data, error } = await window.supabaseClient.auth.getSession();
  if (error || !data.session) {
    window.location.href = "login.html";
    return;
  }

  currentUser = data.session.user;
  document.getElementById("email").textContent = currentUser.email;
  document.getElementById("avatar").textContent = initials(currentUser.email);

  const fallbackName = currentUser.email.split("@")[0];

  try {
    const { data: profile, error: profileError } = await window.supabaseClient
      .from("profiles")
      .select("*")
      .eq("id", currentUser.id)
      .maybeSingle();

    if (profileError) throw profileError;

    document.getElementById("username").value = profile?.username || fallbackName;
    document.getElementById("displayName").value = profile?.display_name || fallbackName;
  } catch (error) {
    document.getElementById("username").value = fallbackName;
    document.getElementById("displayName").value = fallbackName;
    showMessage("Profile table is not ready yet, but you can still edit locally.", "error");
  }

  loadWatchCount();
}

async function saveProfile() {
  if (!currentUser) return;

  const username = document.getElementById("username").value.trim();
  const displayName = document.getElementById("displayName").value.trim();

  if (!username || !displayName) {
    showMessage("Username and display name are required.");
    return;
  }

  const { error } = await window.supabaseClient
    .from("profiles")
    .upsert({
      id: currentUser.id,
      username,
      display_name: displayName,
      email: currentUser.email,
      updated_at: new Date().toISOString()
    }, { onConflict: "id" });

  if (error) {
    showMessage(error.message);
    return;
  }

  showMessage("Profile updated.", "success");
}

async function changePassword() {
  const password = document.getElementById("newPassword").value;
  if (!password || password.length < 8) {
    showMessage("Use at least 8 characters for your new password.");
    return;
  }

  const { error } = await window.supabaseClient.auth.updateUser({ password });

  if (error) {
    showMessage(error.message);
    return;
  }

  document.getElementById("newPassword").value = "";
  showMessage("Password changed.", "success");
}

async function loadWatchCount() {
  if (!currentUser) return;

  try {
    const { count } = await window.supabaseClient
      .from("watchlist")
      .select("*", { count: "exact", head: true })
      .eq("user_id", currentUser.id);

    document.getElementById("watchCount").textContent = count || 0;
  } catch (error) {
    document.getElementById("watchCount").textContent = "0";
  }
}

window.saveProfile = saveProfile;
window.changePassword = changePassword;
window.addEventListener("load", loadProfile);
