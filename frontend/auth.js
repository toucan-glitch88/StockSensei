function showMessage(message, type = "error") {
    const box = document.getElementById("message");
    if (!box) return;

    box.className = type;
    box.textContent = message;
}

function setLoading(isLoading) {
    const spinner = document.getElementById("spinner");
    const text = document.getElementById("loginText");
    const button = document.querySelector(".primary-btn");

    if (!spinner || !text || !button) return;

    spinner.style.display = isLoading ? "block" : "none";
    text.textContent = isLoading ? "Please Wait..." : "Login";
    button.disabled = isLoading;
}

// ---------------------------
// SIGN UP
// ---------------------------

async function signup() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!email || !password) {
        showMessage("Please enter your email and password.");
        return;
    }

    setLoading(true);

    try {

        const { error } = await window.supabaseClient.auth.signUp({
            email,
            password
        });

        setLoading(false);

        if (error) {
            showMessage(error.message);
            return;
        }

        showMessage(
            "Account created! Check your email to verify it.",
            "success"
        );

    } catch (err) {
        setLoading(false);
        showMessage(err.message);
    }
}

// ---------------------------
// LOGIN
// ---------------------------

async function login() {

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!email || !password) {
        showMessage("Please fill in all fields.");
        return;
    }

    setLoading(true);

    try {

        const { error } =
            await window.supabaseClient.auth.signInWithPassword({

                email,
                password

            });

        setLoading(false);

        if (error) {
            showMessage(error.message);
            return;
        }

        if (document.getElementById("remember")?.checked) {
            localStorage.setItem("stocksenseiRemember", "true");
        }

        showMessage("Login successful!", "success");

        setTimeout(() => {
            window.location.href = "index.html";
        }, 800);

    } catch (err) {

        setLoading(false);
        showMessage(err.message);

    }

}

// ---------------------------
// RESET PASSWORD
// ---------------------------

async function resetPassword() {

    const email = document.getElementById("email").value.trim();

    if (!email) {
        showMessage("Enter your email first.");
        return;
    }

    const { error } =
        await window.supabaseClient.auth.resetPasswordForEmail(email);

    if (error) {
        showMessage(error.message);
    } else {
        showMessage(
            "Password reset email sent.",
            "success"
        );
    }

}

// ---------------------------
// LOGOUT
// ---------------------------

async function logout() {

    await window.supabaseClient.auth.signOut();

    localStorage.removeItem("stocksenseiRemember");

    window.location.href = "login.html";

}

// ---------------------------
// AUTO LOGIN
// ---------------------------

window.addEventListener("load", async () => {

    try {

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

        if (
            session &&
            window.location.pathname.includes("login")
        ) {
            window.location.href = "index.html";
        }

    } catch (err) {
        console.error(err);
    }

});