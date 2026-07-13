function getSupabaseClient() {
  if (!window.supabaseClient) {
    showMessage("Login is not ready yet. Refresh the page and try again.");
    return null;
  }
  return window.supabaseClient;
}

function showMessage(message, type = "error") {
  const box = document.getElementById("message");
  if (!box) return;
  box.className = `message ${type}`;
  box.textContent = message;
}

function setLoading(isLoading, label = "Login") {
  const spinner = document.getElementById("spinner");
  const text = document.getElementById("loginText");
  const loginButton = document.getElementById("loginButton");
  const signupButton = document.getElementById("signupButton");

  if (spinner) spinner.style.display = isLoading ? "block" : "none";
  if (text) text.textContent = isLoading ? "Please wait..." : label;
  if (loginButton) loginButton.disabled = isLoading;
  if (signupButton) signupButton.disabled = isLoading;
}

function getCredentials() {
  return {
    email: document.getElementById("email")?.value.trim() || "",
    password: document.getElementById("password")?.value || ""
  };
}

function validateCredentials(email, password, forSignup = false) {
  if (!email || !password) {
    showMessage("Please enter both email and password.");
    return false;
  }

  if (!email.includes("@")) {
    showMessage("Please enter a valid email address.");
    return false;
  }

  if (forSignup && password.length < 8) {
    showMessage("Use at least 8 characters for your password.");
    return false;
  }

  return true;
}

async function ensureProfile(user) {
  const client = getSupabaseClient();
  if (!client || !user) return;

  const username = user.email ? user.email.split("@")[0] : "stocksensei-user";

  try {
    await client
      .from("profiles")
      .upsert({
        id: user.id,
        username,
        display_name: username,
        email: user.email,
        updated_at: new Date().toISOString()
      }, { onConflict: "id" });
  } catch (error) {
    console.warn("Profile table is not ready yet:", error);
  }
}

async function signup() {
  const client = getSupabaseClient();
  if (!client) return;

  const { email, password } = getCredentials();
  if (!validateCredentials(email, password, true)) return;

  setLoading(true, "Login");

  try {
    const { data, error } = await client.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: new URL("index.html", window.location.href).href
      }
    });

    if (error) {
      showMessage(error.message);
      return;
    }

    await ensureProfile(data.user);

    if (data.session) {
      showMessage("Account created. Taking you to StockSensei...", "success");
      setTimeout(() => { window.location.href = "index.html"; }, 700);
    } else {
      showMessage("Account created. Check your email to verify it, then log in.", "success");
    }
  } catch (error) {
    showMessage(error.message || "Could not create account.");
  } finally {
    setLoading(false, "Login");
  }
}

async function login() {
  const client = getSupabaseClient();
  if (!client) return;

  const { email, password } = getCredentials();
  if (!validateCredentials(email, password)) return;

  setLoading(true, "Login");

  try {
    const { data, error } = await client.auth.signInWithPassword({ email, password });

    if (error) {
      showMessage(error.message);
      return;
    }

    await ensureProfile(data.user);

    if (document.getElementById("remember")?.checked) {
      localStorage.setItem("stocksenseiRemember", "true");
    } else {
      localStorage.removeItem("stocksenseiRemember");
    }

    showMessage("Login successful. Opening your dashboard...", "success");
    setTimeout(() => { window.location.href = "index.html"; }, 650);
  } catch (error) {
    showMessage(error.message || "Could not log in.");
  } finally {
    setLoading(false, "Login");
  }
}

async function resetPassword() {
  const client = getSupabaseClient();
  if (!client) return;

  const email = document.getElementById("email")?.value.trim();
  if (!email) {
    showMessage("Enter your email first.");
    return;
  }

  const { error } = await client.auth.resetPasswordForEmail(email, {
    redirectTo: new URL("login.html", window.location.href).href
  });

  if (error) {
    showMessage(error.message);
  } else {
    showMessage("Password reset email sent.", "success");
  }
}

async function logout() {
  const client = getSupabaseClient();
  if (client) await client.auth.signOut();
  localStorage.removeItem("stocksenseiRemember");
  window.location.href = "login.html";
}

function togglePassword() {
  const input = document.getElementById("password");
  const icon = document.getElementById("eyeIcon");
  if (!input || !icon) return;

  const showing = input.type === "text";
  input.type = showing ? "password" : "text";
  icon.className = showing ? "fa-solid fa-eye" : "fa-solid fa-eye-slash";
}

function updatePasswordStrength() {
  const password = document.getElementById("password");
  const strength = document.getElementById("strength");
  if (!password || !strength) return;

  const value = password.value;
  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value)) score++;
  if (/[0-9]/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;

  const text = ["", "Weak", "Fair", "Good", "Strong"];
  const className = ["", "weak", "fair", "good", "strong"];
  strength.className = className[score];
  strength.textContent = value ? `${text[score]} password` : "";
}

window.addEventListener("load", async () => {
  document.getElementById("password")?.addEventListener("input", updatePasswordStrength);

  const client = getSupabaseClient();
  if (!client) return;

  const { data } = await client.auth.getSession();
  if (data.session && window.location.pathname.toLowerCase().endsWith("login.html")) {
    window.location.href = "index.html";
  }
});

window.signup = signup;
window.login = login;
window.logout = logout;
window.resetPassword = resetPassword;
window.togglePassword = togglePassword;
