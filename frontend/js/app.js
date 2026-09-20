const API_BASE_URL = "http://127.0.0.1:8000";

/* ============================================================
   LOGIN
   ============================================================ */

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        /* ----------------------------------------------------
           Get login fields
           ---------------------------------------------------- */

        const usernameInput =
            document.getElementById("username");

        const passwordInput =
            document.getElementById("password");

        const message =
            document.getElementById("loginMessage");


        /* ----------------------------------------------------
           Safety check
           ---------------------------------------------------- */

        if (!usernameInput || !passwordInput) {

            console.error(
                "Login fields not found in index.html"
            );

            return;
        }


        /* ----------------------------------------------------
           Get values
           ---------------------------------------------------- */

        const username =
            usernameInput.value.trim();

        const password =
            passwordInput.value;


        if (message) {
            message.textContent = "Logging in...";
        }


        /* ----------------------------------------------------
           Send login request
           ---------------------------------------------------- */

        try {

            console.log("Attempting login for:", username);

            const response = await fetch(
                `${API_BASE_URL}/api/v1/auth/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },

                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                }
            );


            /* ------------------------------------------------
               Read response
               ------------------------------------------------ */

            const data = await response.json();

            console.log("Login response:", data);


            /* ------------------------------------------------
               Handle backend error
               ------------------------------------------------ */

            if (!response.ok) {

                if (message) {

                    message.textContent =
                        data.detail ||
                        "Login failed.";

                }

                console.error(
                    "Login failed:",
                    data
                );

                return;
            }


            /* ------------------------------------------------
               Make sure token exists
               ------------------------------------------------ */

            if (!data.access_token) {

                console.error(
                    "No access token received:",
                    data
                );

                if (message) {
                    message.textContent =
                        "Login failed: no access token received.";
                }

                return;
            }


            /* ------------------------------------------------
               Save JWT
               ------------------------------------------------ */

            localStorage.setItem(
                "access_token",
                data.access_token
            );


            /* ------------------------------------------------
               Save user information
               ------------------------------------------------ */

            localStorage.setItem(
                "user",
                JSON.stringify(data.user)
            );


            console.log(
                "Login successful:",
                data.user
            );


            if (message) {
                message.textContent =
                    "Login successful!";
            }


            /* ------------------------------------------------
               Redirect according to role
               ------------------------------------------------ */

            if (
                data.user &&
                data.user.role === "ADMIN"
            ) {

                console.log(
                    "Admin detected. Redirecting..."
                );

                window.location.href =
                    "admin-dashboard.html";

            } else {

                console.log(
                    "Non-admin user detected. Redirecting..."
                );

                window.location.href = "user-dashboard.html";
            }

        } catch (error) {

            console.error(
                "Login error:",
                error
            );

            if (message) {

                message.textContent =
                    "Unable to connect to BugFlow server.";

            }

        }

    });
}


/* ============================================================
   SHOW / HIDE PASSWORD
   ============================================================ */

const passwordInput =
    document.getElementById("password");

const togglePassword =
    document.getElementById("togglePassword");


if (passwordInput && togglePassword) {

    togglePassword.addEventListener(
        "click",
        function () {

            if (passwordInput.type === "password") {

                passwordInput.type = "text";

                togglePassword.textContent = "🙈";

                togglePassword.setAttribute(
                    "aria-label",
                    "Hide password"
                );

                togglePassword.setAttribute(
                    "title",
                    "Hide password"
                );

            } else {

                passwordInput.type = "password";

                togglePassword.textContent = "👁";

                togglePassword.setAttribute(
                    "aria-label",
                    "Show password"
                );

                togglePassword.setAttribute(
                    "title",
                    "Show password"
                );

            }

        }
    );
}