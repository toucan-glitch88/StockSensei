let currentUser;


window.addEventListener("load", loadProfile);



async function loadProfile(){


const {
data:{
session
}
}
=
await window.supabaseClient.auth.getSession();



if(!session){

window.location.href="login.html";

return;

}



currentUser=session.user;



document.getElementById("email").textContent =
currentUser.email;



const {
data:profile,
error
}
=
await window.supabaseClient
.from("profiles")
.select("*")
.eq("id", currentUser.id)
.single();



if(error){

console.log(error);

return;

}



document.getElementById("username").value =
profile.username || "";


document.getElementById("displayName").value =
profile.display_name || "";



loadWatchCount();


}




async function saveProfile(){


const username =
document.getElementById("username").value;


const display =
document.getElementById("displayName").value;



const {
error
}
=
await window.supabaseClient
.from("profiles")
.update({

username:username,
display_name:display

})
.eq("id",currentUser.id);



if(error){

showMessage(error.message);

return;

}



showMessage(
"Profile updated!",
"success"
);


}




async function changePassword(){


const password =
document.getElementById("newPassword").value;



const {
error
}
=
await window.supabaseClient.auth.updateUser({

password:password

});



if(error){

showMessage(error.message);

return;

}



showMessage(
"Password changed!",
"success"
);



}




async function loadWatchCount(){


const {
count
}
=
await window.supabaseClient
.from("watchlist")
.select("*",{count:"exact",head:true})
.eq("user_id",currentUser.id);



document.getElementById("watchCount")
.textContent=count || 0;


}




function showMessage(text,type="error"){


const box=document.getElementById("message");

box.textContent=text;

box.className=type;


}