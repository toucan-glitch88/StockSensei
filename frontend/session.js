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

}

// ---------------------------
// Login Modal
// ---------------------------

function showLoginModal() {

    document.body.style.overflow = "hidden";

    if (document.getElementById("loginOverlay"))
        return;

    const overlay = document.createElement("div");

    overlay.id = "loginOverlay";

    overlay.innerHTML = `
        <div class="login-popup">

            <h2>🔒 Login Required</h2>

            <p>
                Please log in to access this page and your
                personalized StockSensei dashboard.
            </p>

            <button id="loginNow">
                Login
            </button>

            <button id="goHome">
                Go Home
            </button>

        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById("loginNow").onclick = () => {
        window.location.href = "login.html";
    };

    document.getElementById("goHome").onclick = () => {
        window.location.href = "index.html";
    };

}

// ---------------------------
// Logout
// ---------------------------

async function logout() {

    await window.supabaseClient.auth.signOut();

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

}