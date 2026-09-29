/* =========================================================
   BUGFLOW - SHARED USER PROFILE SYNC
   ========================================================= */

const BUGFLOW_API_BASE_URL = "http://127.0.0.1:8000";


/* =========================================================
   TOKEN
   ========================================================= */

function getBugFlowToken() {
    return localStorage.getItem("access_token");
}


/* =========================================================
   STORED USER
   ========================================================= */

function getBugFlowStoredUser() {
    const storedUser = localStorage.getItem("user");

    if (!storedUser) {
        return null;
    }

    try {
        return JSON.parse(storedUser);
    } catch (error) {
        console.error("Invalid stored BugFlow user:", error);
        localStorage.removeItem("user");
        return null;
    }
}


/* =========================================================
   SAVE USER
   ========================================================= */

function saveBugFlowUser(user) {
    if (!user) {
        return;
    }

    localStorage.setItem(
        "user",
        JSON.stringify(user)
    );

    /*
     * Notify every component on the current page.
     * This is useful if another script changes the profile.
     */
    window.dispatchEvent(
        new CustomEvent("bugflow:user-updated", {
            detail: user
        })
    );
}


/* =========================================================
   INITIALS
   ========================================================= */

function getBugFlowInitials(name) {

    if (!name) {
        return "U";
    }

    const parts = name
        .trim()
        .split(/\s+/)
        .filter(Boolean);

    if (parts.length === 0) {
        return "U";
    }

    if (parts.length === 1) {
        return parts[0]
            .substring(0, 2)
            .toUpperCase();
    }

    return (
        parts[0][0] +
        parts[parts.length - 1][0]
    ).toUpperCase();
}


/* =========================================================
   PROFILE IMAGE URL
   ========================================================= */

function getBugFlowProfileImageUrl(profilePicture) {

    if (!profilePicture) {
        return null;
    }

    if (
        profilePicture.startsWith("http://") ||
        profilePicture.startsWith("https://") ||
        profilePicture.startsWith("data:")
    ) {
        return profilePicture;
    }

    if (profilePicture.startsWith("/")) {
        return `${BUGFLOW_API_BASE_URL}${profilePicture}`;
    }

    return `${BUGFLOW_API_BASE_URL}/${profilePicture}`;
}


/* =========================================================
   UPDATE ALL AVATARS ON CURRENT PAGE
   ========================================================= */

function updateBugFlowAvatars(user) {

    if (!user) {
        return;
    }

    const name =
        user.full_name ||
        user.username ||
        "User";

    const role =
        user.role ||
        "TESTER";

    const imageUrl =
        getBugFlowProfileImageUrl(
            user.profile_picture
        );


    /* -----------------------------------------------------
       UPDATE EVERY AVATAR

       IMPORTANT:
       We use querySelectorAll instead of only
       #userAvatar because some pages may have
       different avatar IDs.
    ----------------------------------------------------- */

    const avatarElements =
        document.querySelectorAll(
            ".user-avatar, #userAvatar, #profileAvatar"
        );


    avatarElements.forEach(avatar => {
        avatar.style.width = "40px";
avatar.style.height = "40px";
avatar.style.minWidth = "40px";
avatar.style.minHeight = "40px";
avatar.style.borderRadius = "50%";
avatar.style.overflow = "hidden";
avatar.style.display = "flex";
avatar.style.alignItems = "center";
avatar.style.justifyContent = "center";

        /*
         * Remove old image completely.
         * This fixes the problem where an old picture
         * remains after profile picture deletion.
         */
        avatar.innerHTML = "";


        if (imageUrl) {

            const img =
                document.createElement("img");

            img.src = imageUrl;

            img.alt = "Profile Picture";

            img.style.width = "100%";
            img.style.height = "100%";
            img.style.objectFit = "cover";
            img.style.display = "block";
            img.style.borderRadius = "50%";


            img.onerror = function() {

                avatar.innerHTML = "";

                avatar.textContent =
                    getBugFlowInitials(name);
            };


            avatar.appendChild(img);

        } else {

            /*
             * profile_picture is null/empty.
             * Show initials instead.
             */
            avatar.textContent =
                getBugFlowInitials(name);
        }
    });


    /* -----------------------------------------------------
       UPDATE USER NAME
    ----------------------------------------------------- */

    const nameElements =
        document.querySelectorAll(
            "#topUserName, .user-name, #profileUserName"
        );

    nameElements.forEach(element => {
        element.textContent = name;
    });


    /* -----------------------------------------------------
       UPDATE USER ROLE
    ----------------------------------------------------- */

    const roleElements =
        document.querySelectorAll(
            "#topUserRole, .user-role, #profileUserRole"
        );

    roleElements.forEach(element => {
        element.textContent = role;
    });
}


/* =========================================================
   LOAD LATEST USER FROM BACKEND
   ========================================================= */

async function loadBugFlowCurrentUser() {

    const token =
        getBugFlowToken();

    if (!token) {
        return null;
    }


    try {

        const response =
            await fetch(
                `${BUGFLOW_API_BASE_URL}/api/v1/profile/`,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );


        /* -------------------------------------------------
           AUTH FAILURE
        ------------------------------------------------- */

        if (
            response.status === 401 ||
            response.status === 403
        ) {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "user"
            );

            window.location.href =
                "index.html";

            return null;
        }


        /* -------------------------------------------------
           OTHER ERROR
        ------------------------------------------------- */

        if (!response.ok) {

            console.warn(
                "BugFlow profile API returned:",
                response.status
            );

            return getBugFlowStoredUser();
        }


        const user =
            await response.json();


        /*
         * VERY IMPORTANT:
         *
         * Save the newest backend profile.
         *
         * If profile_picture was deleted and backend
         * returns null, localStorage is also updated
         * to null.
         */
        saveBugFlowUser(user);


        return user;

    } catch (error) {

        console.warn(
            "Unable to load BugFlow current user:",
            error
        );

        return getBugFlowStoredUser();
    }
}


/* =========================================================
   INITIALIZE PROFILE ON PAGE
   ========================================================= */

async function initializeBugFlowProfile() {

    /*
     * 1. Show cached user immediately.
     */
    const storedUser =
        getBugFlowStoredUser();

    if (storedUser) {
        updateBugFlowAvatars(
            storedUser
        );
    }


    /*
     * 2. Fetch latest profile from backend.
     */
    const currentUser =
        await loadBugFlowCurrentUser();


    /*
     * 3. Replace cached information with
     *    latest backend information.
     */
    if (currentUser) {

        updateBugFlowAvatars(
            currentUser
        );
    }
}


/* =========================================================
   PROFILE UPDATE EVENT
   ========================================================= */

window.addEventListener(
    "bugflow:user-updated",
    function(event) {

        if (
            event.detail
        ) {

            updateBugFlowAvatars(
                event.detail
            );
        }
    }
);


/* =========================================================
   PAGE LOAD
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        initializeBugFlowProfile();

    }
);