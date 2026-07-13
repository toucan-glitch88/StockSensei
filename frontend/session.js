const publicPages = new Set([
  "",
  "index.html",
  "login.html",
  "about.html",
  "learn.html",
  "explore.html"
]);

function currentPage() {
  return window.location.pathname.split("/").pop().toLowerCase();
}

function initialsFromEmail(email) {
  const username = (email || "user").split("@")[0];
  return username
    .split(/[._-]/)
    .filter(Boolean)
    .map(part => part[0].toUpperCase())
    .join("")
    .substring(0, 2) || "SS";
}

function colorFromEmail(email) {
  const colors = ["#2563eb", "#059669", "#dc2626", "#9333ea", "#ea580c", "#0891b2", "#e11d48", "#4f46e5"];
  let hash = 0;
  for (const char of email || "user") hash += char.charCodeAt(0);
  return colors[hash % colors.length];
}

function renderLoggedOutNav() {
  const userArea = document.getElementById("userArea");
  if (!userArea) return;
  userArea.innerHTML = '<a class="login-btn" href="login.html">Login</a>';
}

function renderLoggedInNav(user) {
  const userArea = document.getElementById("userArea");
  if (!userArea) return;

  const username = user.email.split("@")[0];
  const initials = initialsFromEmail(user.email);
  const color = colorFromEmail(user.email);

  userArea.innerHTML = `
    <div class="profile-menu">
      <button class="profile-button" type="button" aria-label="Open profile menu">
        <div class="avatar" style="background:${color};">${initials}</div>
      </button>
      <div class="dropdown">
        <div class="dropdown-top">
          <div class="avatar big" style="background:${color};">${initials}</div>
          <h3>${username}</h3>
          <p>${user.email}</p>
        </div>
        <a href="profile.html">Profile</a>
        <a href="watchlist.html">Watchlist</a>
        <a href="Predict.html">Predictions</a>
        <button type="button" onclick="logout()">Logout</button>
      </div>
    </div>
  `;
}

function showLoginModal() {
  if (document.getElementById("loginOverlay")) return;

  document.body.style.overflow = "hidden";
  const overlay = document.createElement("div");
  overlay.id = "loginOverlay";
  overlay.innerHTML = `
    <div class="login-popup">
      <h2>Login Required</h2>
      <p>Please log in to access this page and your personalized StockSensei tools.</p>
      <button id="loginNow" type="button">Login</button>
      <button id="goHome" type="button">Go Home</button>
    </div>
  `;
  document.body.appendChild(overlay);
  document.getElementById("loginNow").onclick = () => { window.location.href = "login.html"; };
  document.getElementById("goHome").onclick = () => { window.location.href = "index.html"; };
}

async function logout() {
  if (window.supabaseClient) await window.supabaseClient.auth.signOut();
  localStorage.removeItem("stocksenseiRemember");
  window.location.href = "login.html";
}

async function checkSession() {
  if (!window.supabaseClient) {
    renderLoggedOutNav();
    return;
  }

  const { data, error } = await window.supabaseClient.auth.getSession();
  if (error) {
    console.error(error);
    renderLoggedOutNav();
    return;
  }

  if (data.session) {
    renderLoggedInNav(data.session.user);
    return;
  }

  renderLoggedOutNav();
  if (!publicPages.has(currentPage())) showLoginModal();
}

window.logout = logout;
window.addEventListener("load", checkSession);
