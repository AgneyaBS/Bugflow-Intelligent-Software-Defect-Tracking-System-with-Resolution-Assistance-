const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// CHECK LOGIN
// ============================================================

const token = localStorage.getItem("access_token");
const storedUser = localStorage.getItem("user");

if (!token || !storedUser) {

    window.location.href = "index.html";

}


// ============================================================
// USER INFORMATION
// ============================================================

const user = JSON.parse(storedUser);

if (user.role !== "ADMIN") {

    alert("Access denied. Admin privileges required.");

    window.location.href = "user-dashboard.html";

}


// ============================================================
// DISPLAY ADMIN INFORMATION
// ============================================================

document.getElementById("adminName").textContent =
    user.full_name || user.username;

document.getElementById("adminUsername").textContent =
    user.username;

document.getElementById("adminRole").textContent =
    user.role;

document.getElementById("systemRole").textContent =
    user.role;


// ============================================================
// LOGOUT
// ============================================================

function logout() {

    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    window.location.href = "index.html";
}


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/api/v1/issues`,
            {
                method: "GET",

                headers: {
                    "Accept": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            }
        );


        if (!response.ok) {

            console.error(
                "Failed to load issues:",
                response.status
            );

            return;
        }


        const issues = await response.json();

        console.log("Issues received:", issues);


        // ----------------------------------------------------
        // STATISTICS
        // ----------------------------------------------------

        document.getElementById("totalIssues").textContent =
            issues.length;


        const reported = issues.filter(
            issue => issue.status === "REPORTED"
        ).length;

        const inProgress = issues.filter(
            issue =>
                issue.status === "IN_PROGRESS" ||
                issue.status === "ASSIGNED"
        ).length;

        const resolved = issues.filter(
            issue => issue.status === "RESOLVED"
        ).length;


        document.getElementById("reportedIssues").textContent =
            reported;

        document.getElementById("inProgressIssues").textContent =
            inProgress;

        document.getElementById("resolvedIssues").textContent =
            resolved;


        // ----------------------------------------------------
        // RECENT ISSUES
        // ----------------------------------------------------

        displayRecentIssues(issues);


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }

}


// ============================================================
// DISPLAY RECENT ISSUES
// ============================================================

function displayRecentIssues(issues) {

    const table =
        document.getElementById("recentIssuesTable");


    if (!issues || issues.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    No issues found.
                </td>
            </tr>
        `;

        return;
    }


    const recentIssues =
        issues.slice(-5).reverse();


    table.innerHTML =
        recentIssues.map(issue => `

            <tr>

                <td>#${issue.id}</td>

                <td>
                    ${escapeHtml(issue.title || "Untitled")}
                </td>

                <td>
                    <span class="status-badge severity-${String(issue.severity || "").toLowerCase()}">
                        ${issue.severity || "-"}
                    </span>
                </td>

                <td>
                    ${issue.priority || "-"}
                </td>

                <td>
                    <span class="status-badge">
                        ${issue.status || "-"}
                    </span>
                </td>

                <td>
                    ${issue.assignee_id || "Unassigned"}
                </td>

            </tr>

        `).join("");

}


// ============================================================
// HTML SAFETY
// ============================================================

function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// START
// ============================================================

loadDashboard();