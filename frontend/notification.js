// ============================================================
// BUGFLOW - REAL-TIME NOTIFICATION BADGES
// ============================================================

const BUGFLOW_WS =
    "ws://127.0.0.1:8000/api/v1/notifications/ws";

const bugflowNotificationToken =
    localStorage.getItem("access_token");

let notificationBadgeSocket = null;


// ============================================================
// UPDATE BADGES
// ============================================================

async function updateNotificationCount() {

    if (!bugflowNotificationToken) {
        return;
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/api/v1/notifications/unread-count",
            {
                method: "GET",
                headers: {
                    "Authorization":
                        `Bearer ${bugflowNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        const count =
            Number(data.unread_count || 0);


        // Sidebar badge
        const sidebarBadge =
            document.getElementById(
                "sidebarNotificationBadge"
            );

        if (sidebarBadge) {

            sidebarBadge.textContent = count;

            sidebarBadge.style.display =
                count > 0 ? "flex" : "none";
        }


        // Top-right badge
        const topBadge =
            document.getElementById(
                "topNotificationBadge"
            );

        if (topBadge) {

            topBadge.textContent = count;

            topBadge.style.display =
                count > 0
                    ? "inline-flex"
                    : "none";
        }

    } catch (error) {

        console.error(
            "Notification badge error:",
            error
        );

    }
}


// ============================================================
// REAL-TIME WEBSOCKET
// ============================================================

function connectNotificationBadgeWebSocket() {

    if (!bugflowNotificationToken) {
        return;
    }

    notificationBadgeSocket =
        new WebSocket(BUGFLOW_WS);


    notificationBadgeSocket.onopen =
        function () {

            console.log(
                "Notification badge WebSocket connected."
            );

            // Send JWT
            notificationBadgeSocket.send(
                bugflowNotificationToken
            );

        };


    notificationBadgeSocket.onmessage =
        function (event) {

            try {

                const data =
                    JSON.parse(event.data);

                console.log(
                    "Real-time badge update:",
                    data
                );


                // New notification arrived
                updateNotificationCount();

            } catch (error) {

                console.error(
                    "Badge WebSocket message error:",
                    error
                );

            }

        };


    notificationBadgeSocket.onclose =
        function () {

            console.log(
                "Badge WebSocket disconnected. Reconnecting..."
            );

            setTimeout(
                connectNotificationBadgeWebSocket,
                3000
            );

        };


    notificationBadgeSocket.onerror =
        function (error) {

            console.error(
                "Badge WebSocket error:",
                error
            );

        };
}


// ============================================================
// START
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateNotificationCount();

        connectNotificationBadgeWebSocket();

    }
);