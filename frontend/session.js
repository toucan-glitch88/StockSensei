const publicPages = [
    "login.html",
    "index.html",
    "about.html",
];

window.addEventListener("load", checkSession);

async function checkSession() {

    if (!window.supabaseClient) {
        console.error("Supabase client not initialized.");
        return;
    }

    const {
        data: { session },
        error
    } = await window.supabaseClient.auth.getSession();

    if (error) {
        console.error(error);
        return;
    }

    const page = window.location.pathname
        .split("/")
        .pop()
        .toLowerCase();

    const userArea = document.getElementById("userArea");

    // --------------------
    // Logged In
    // --------------------

    if (session) {

        setupNavbar(session.user);
        return;

    }

    // --------------------
    // Logged Out Navbar
    // --------------------

    if (userArea) {

        userArea.innerHTML = `
            <a class="login-btn" href="login.html">
                Login
            </a>
        `;

    }

    // --------------------
    // Public Pages
    // --------------------

    if (publicPages.includes(page))
        return;

    // --------------------
    // Protected Page
    // --------------------

    showLoginModal();

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

// ---------------------------
// Navbar
// ---------------------------

function setupNavbar(user) {

    const userArea = document.getElementById("userArea");

    if (!userArea) return;


    const email = user.email;

    const username = email.split("@")[0];


    // Create 2 initials
    const initials = username
        .split(/[._\-]/)
        .filter(Boolean)
        .map(part => part[0].toUpperCase())
        .join("")
        .substring(0, 2);


    // If email has no separator (example: eashantilaye@gmail.com)
    // use first two letters
    const finalInitials = initials.length >= 2
        ? initials
        : username.substring(0,2).toUpperCase();



    // Generate consistent avatar color
    const colors = [
        "#2563eb",
        "#059669",
        "#dc2626",
        "#9333ea",
        "#ea580c",
        "#0891b2",
        "#e11d48",
        "#4f46e5"
    ];


    let hash = 0;

    for (const char of email) {
        hash += char.charCodeAt(0);
    }


    const color = colors[hash % colors.length];



    userArea.innerHTML = `

<div class="profile-menu">


<button class="profile-button">

<div class="avatar"
style="background:${color};">

${finalInitials}

</div>

</button>



<div class="dropdown">


<div class="dropdown-top">


<div class="avatar big"
style="background:${color};">

${finalInitials}

</div>


<h3>
${username}
</h3>


<p>
${email}
</p>


</div>



<a href="profile.html">
👤 Profile
</a>


<button onclick="logout()">
🚪 Logout
</button>


</div>


</div>

`;

window.logout = logout;
window.addEventListener("load", checkSession);
