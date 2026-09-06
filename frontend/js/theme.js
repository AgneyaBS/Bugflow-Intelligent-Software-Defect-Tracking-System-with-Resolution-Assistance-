function applyBugFlowTheme() {
    const theme = localStorage.getItem("bugflow_theme") || "light";

    document.documentElement.setAttribute("data-theme", theme);
    document.body.classList.toggle("dark-mode", theme === "dark");
}

applyBugFlowTheme();

document.addEventListener("DOMContentLoaded", function () {
    applyBugFlowTheme();
});