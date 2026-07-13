const publicPages = new Set([
    "",
    "index.html",
    "login.html",
    "about.html",
    "learn.html",
    "explore.html"
]);


window.addEventListener("load", checkSession);


async function checkSession() {

    if (!window.supabaseClient) {
        console.error("Supabase client missing");
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



    if (session) {

        renderLoggedInNav(session.user);

        return;
    }



    renderLoggedOutNav();



    if (!publicPages.has(page)) {
        showLoginModal();
    }

}




function renderLoggedOutNav(){

    const userArea = document.getElementById("userArea");

    if(!userArea) return;


    userArea.innerHTML = `
        <a class="login-btn" href="login.html">
            Login
        </a>
    `;
}





function renderLoggedInNav(user){

    const userArea=document.getElementById("userArea");

    if(!userArea)return;


    const username=user.email.split("@")[0];


    const initials=username
        .substring(0,2)
        .toUpperCase();


    userArea.innerHTML=`

    <div class="profile-menu">

        <button class="profile-button">

            <div class="avatar">
                ${initials}
            </div>

        </button>


        <div class="dropdown">

            <h3>${username}</h3>

            <p>${user.email}</p>


            <a href="profile.html">
                Profile
            </a>


            <a href="watchlist.html">
                Watchlist
            </a>


            <a href="Predict.html">
                Predictions
            </a>


            <button onclick="logout()">
                Logout
            </button>


        </div>

    </div>
    `;


    document.querySelector(".profile-button")
    .onclick=()=>{

        document.querySelector(".dropdown")
        .classList.toggle("show");

    };


}





function showLoginModal(){

    if(document.getElementById("loginOverlay"))
        return;


    const overlay=document.createElement("div");

    overlay.id="loginOverlay";


    overlay.innerHTML=`

    <div class="login-popup">

        <h2>
            Login Required
        </h2>

        <p>
        Please log in to access StockSensei tools.
        </p>


        <button onclick="location.href='login.html'">
            Login
        </button>


        <button onclick="location.href='index.html'">
            Go Home
        </button>


    </div>

    `;


    document.body.appendChild(overlay);

}




async function logout(){

    await window.supabaseClient.auth.signOut();

    window.location.href="login.html";

}


window.logout=logout;