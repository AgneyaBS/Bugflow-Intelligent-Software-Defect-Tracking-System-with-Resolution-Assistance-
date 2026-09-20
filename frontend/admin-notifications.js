// ============================================================
// BUGFLOW - ADMIN NOTIFICATIONS
// ============================================================

const ADMIN_API_BASE =
    "http://127.0.0.1:8000";

const ADMIN_WS =
    "ws://127.0.0.1:8000/api/v1/notifications/ws";

const adminNotificationToken =
    localStorage.getItem("access_token");

let adminNotificationSocket = null;


// ============================================================
// UPDATE ADMIN NOTIFICATION BADGES
// ============================================================

async function updateAdminNotificationCount() {

    if (!adminNotificationToken) {
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/unread-count`,
            {
                method: "GET",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {
            console.error(
                "Unable to load admin notification count:",
                response.status
            );
            return;
        }

        const data = await response.json();

        const count =
            Number(data.unread_count || 0);


        // ====================================================
        // SIDEBAR BADGE
        // ====================================================

        const sidebarBadge =
            document.getElementById(
                "sidebarNotificationBadge"
            );

        if (sidebarBadge) {

            sidebarBadge.textContent = count;

            sidebarBadge.style.display =
                count > 0 ? "flex" : "none";
        }


        // ====================================================
        // TOP-RIGHT BADGE
        // ====================================================

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
            "Admin notification badge error:",
            error
        );
    }
}


// ============================================================
// LOAD ADMIN NOTIFICATIONS
// ============================================================

async function loadAdminNotifications() {

    const notificationsList =
        document.getElementById("notificationsList");

    // This allows the same JS file to work on
    // other Admin pages that only have the badge.
    if (!notificationsList) {
        return;
    }

    if (!adminNotificationToken) {
        showAdminNoNotifications(
            "Please login to view notifications."
        );
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/`,
            {
                method: "GET",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {

            console.error(
                "Unable to load notifications:",
                response.status
            );

            showAdminNoNotifications(
                "Unable to load notifications."
            );

            return;
        }

        const notifications =
            await response.json();

        displayAdminNotifications(
            notifications
        );

        updateAdminNotificationCount();

    } catch (error) {

        console.error(
            "Notification loading error:",
            error
        );

        showAdminNoNotifications(
            "Unable to connect to the BugFlow server."
        );
    }
}


// ============================================================
// NOTIFICATION ICON
// ============================================================

function getAdminNotificationIcon(type) {

    const notificationType =
        String(type || "").toUpperCase();

    if (
        notificationType.includes("ISSUE") ||
        notificationType.includes("BUG")
    ) {
        return "fa-solid fa-bug";
    }

    if (
        notificationType.includes("ASSIGN")
    ) {
        return "fa-solid fa-user-check";
    }

    if (
        notificationType.includes("RESOLVE")
    ) {
        return "fa-solid fa-circle-check";
    }

    if (
        notificationType.includes("COMMENT")
    ) {
        return "fa-solid fa-comment";
    }

    if (
        notificationType.includes("SYSTEM")
    ) {
        return "fa-solid fa-gear";
    }

    return "fa-solid fa-bell";
}


// ============================================================
// FORMAT NOTIFICATION TIME
// ============================================================

function formatAdminNotificationTime(
    createdAt
) {

    if (!createdAt) {
        return "";
    }

    const date =
        new Date(createdAt);

    if (Number.isNaN(date.getTime())) {
        return "";
    }

    const now =
        new Date();

    const diff =
        Math.floor(
            (now.getTime() - date.getTime())
            / 1000
        );

    if (diff < 60) {
        return "Just now";
    }

    if (diff < 3600) {
        return `${Math.floor(diff / 60)} min ago`;
    }

    if (diff < 86400) {
        return `${Math.floor(diff / 3600)} hr ago`;
    }

    if (diff < 604800) {
        return `${Math.floor(diff / 86400)} days ago`;
    }

    return date.toLocaleDateString();
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeAdminHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value == null ? "" : String(value);

    return div.innerHTML;
}


// ============================================================
// DISPLAY ADMIN NOTIFICATIONS
// ============================================================

function displayAdminNotifications(
    notifications
) {

    const notificationsList =
        document.getElementById(
            "notificationsList"
        );

    if (!notificationsList) {
        return;
    }

    if (
        !Array.isArray(notifications) ||
        notifications.length === 0
    ) {

        showAdminNoNotifications(
            "No notifications yet."
        );

        return;
    }


    notificationsList.innerHTML =
        notifications.map(
            notification => {

                const unreadClass =
                    notification.is_read
                        ? ""
                        : "unread";

                const icon =
                    getAdminNotificationIcon(
                        notification.notification_type
                    );

                const issueText =
                    notification.issue_id
                        ? `Issue #${notification.issue_id}`
                        : "";

                return `
                    <div
                        class="notification-item ${unreadClass}"
                        data-id="${notification.id}"
                    >

                        <div class="notification-icon">
                            <i class="${icon}"></i>
                        </div>

                        <div class="notification-content">

                            <strong>
                                ${escapeAdminHtml(
                                    notification.title
                                )}
                            </strong>

                            <p>
                                ${escapeAdminHtml(
                                    notification.message
                                )}
                            </p>

                            <small>
                                ${issueText}
                                ${issueText ? " • " : ""}
                                ${formatAdminNotificationTime(
                                    notification.created_at
                                )}
                            </small>

                        </div>

                        <div class="notification-actions">

                            ${
                                !notification.is_read
                                    ? `
                                    <button
                                        type="button"
                                        onclick="markAdminNotificationRead(${notification.id})"
                                        title="Mark as read"
                                    >
                                        <i class="fa-solid fa-check"></i>
                                    </button>
                                    `
                                    : ""
                            }

                            <button
                                type="button"
                                onclick="deleteAdminNotification(${notification.id})"
                                title="Delete"
                            >
                                <i class="fa-solid fa-trash"></i>
                            </button>

                        </div>

                    </div>
                `;
            }
        ).join("");
}


// ============================================================
// NO NOTIFICATIONS MESSAGE
// ============================================================

function showAdminNoNotifications(
    message = "No notifications yet."
) {

    const notificationsList =
        document.getElementById(
            "notificationsList"
        );

    if (!notificationsList) {
        return;
    }

    notificationsList.innerHTML = `
        <div class="no-notifications">

            <i class="fa-regular fa-bell-slash"></i>

            <h3>No Notifications</h3>

            <p>
                ${escapeAdminHtml(message)}
            </p>

        </div>
    `;
}


// ============================================================
// MARK ONE NOTIFICATION AS READ
// ============================================================

async function markAdminNotificationRead(
    notificationId
) {

    if (!adminNotificationToken) {
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/${notificationId}/read`,
            {
                method: "PATCH",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {

            console.error(
                "Unable to mark notification as read:",
                response.status
            );

            return;
        }

        await loadAdminNotifications();

        updateAdminNotificationCount();

    } catch (error) {

        console.error(
            "Mark notification read error:",
            error
        );
    }
}


// ============================================================
// MARK ALL NOTIFICATIONS AS READ
// ============================================================

async function markAllAdminNotificationsRead() {

    if (!adminNotificationToken) {
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/read-all`,
            {
                method: "PATCH",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {

            console.error(
                "Unable to mark all notifications as read:",
                response.status
            );

            return;
        }

        await loadAdminNotifications();

        updateAdminNotificationCount();

    } catch (error) {

        console.error(
            "Mark all notifications read error:",
            error
        );
    }
}


// ============================================================
// DELETE ONE NOTIFICATION
// ============================================================

async function deleteAdminNotification(
    notificationId
) {

    if (!adminNotificationToken) {
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/${notificationId}/delete`,
            {
                method: "DELETE",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {

            console.error(
                "Unable to delete notification:",
                response.status
            );

            return;
        }

        await loadAdminNotifications();

        updateAdminNotificationCount();

    } catch (error) {

        console.error(
            "Delete notification error:",
            error
        );
    }
}


// ============================================================
// DELETE ALL NOTIFICATIONS
// ============================================================

async function clearAdminNotifications() {

    if (!adminNotificationToken) {
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/`,
            {
                method: "DELETE",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!response.ok) {

            console.error(
                "Unable to clear notifications:",
                response.status
            );

            return;
        }

        await loadAdminNotifications();

        updateAdminNotificationCount();

    } catch (error) {

        console.error(
            "Clear notifications error:",
            error
        );
    }
}


// ============================================================
// DELETE SELECTED NOTIFICATIONS
// ============================================================

async function deleteSelectedAdminNotifications(
    notificationIds
) {

    if (!adminNotificationToken) {
        return;
    }

    if (
        !Array.isArray(notificationIds) ||
        notificationIds.length === 0
    ) {
        return;
    }

    try {

        const response = await fetch(
            `${ADMIN_API_BASE}/api/v1/notifications/selected`,
            {
                method: "DELETE",
                headers: {
                    "Authorization":
                        `Bearer ${adminNotificationToken}`,
                    "Content-Type":
                        "application/json",
                    "Accept":
                        "application/json"
                },
                body: JSON.stringify(
                    notificationIds
                )
            }
        );

        if (!response.ok) {

            console.error(
                "Unable to delete selected notifications:",
                response.status
            );

            return;
        }

        await loadAdminNotifications();

        updateAdminNotificationCount();

    } catch (error) {

        console.error(
            "Delete selected notifications error:",
            error
        );
    }
}


// ============================================================
// REAL-TIME ADMIN WEBSOCKET
// ============================================================

function connectAdminNotificationWebSocket() {

    if (!adminNotificationToken) {
        return;
    }

    // Prevent duplicate WebSocket connections.
    if (
        adminNotificationSocket &&
        adminNotificationSocket.readyState === WebSocket.OPEN
    ) {
        return;
    }

    adminNotificationSocket =
        new WebSocket(ADMIN_WS);


    adminNotificationSocket.onopen =
        function () {

            console.log(
                "Admin notification WebSocket connected."
            );

            adminNotificationSocket.send(
                adminNotificationToken
            );
        };


    adminNotificationSocket.onmessage =
        function (event) {

            try {

                const data =
                    JSON.parse(event.data);

                console.log(
                    "Admin real-time notification:",
                    data
                );

                updateAdminNotificationCount();

                // If we are currently on the Admin
                // Notifications page, refresh the list.
                if (
                    document.getElementById(
                        "notificationsList"
                    )
                ) {
                    loadAdminNotifications();
                }

            } catch (error) {

                console.error(
                    "Admin notification message error:",
                    error
                );
            }
        };


    adminNotificationSocket.onclose =
        function () {

            console.log(
                "Admin notification WebSocket disconnected. Reconnecting..."
            );

            setTimeout(
                connectAdminNotificationWebSocket,
                3000
            );
        };


    adminNotificationSocket.onerror =
        function (error) {

            console.error(
                "Admin notification WebSocket error:",
                error
            );
        };
}


// ============================================================
// START ADMIN NOTIFICATIONS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateAdminNotificationCount();

        loadAdminNotifications();

        connectAdminNotificationWebSocket();

    }
);