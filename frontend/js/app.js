async function checkBackendConnection() {
    const status = document.querySelector("#api-status");
    const stat = document.querySelector("#api-stat");

    try {
        const response = await fetch("/api/health");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        await response.json();
        status.className = "api-status online";
        status.innerHTML = "<i></i> Backend connected";
        if (stat) stat.textContent = "Online";
    } catch (error) {
        status.className = "api-status offline";
        status.innerHTML = "<i></i> API unavailable";
        if (stat) stat.textContent = "Offline";
        console.error("API connection error:", error);
    }
}

checkBackendConnection();


// Simple client-side navigation between the dashboard and reports views.
const pageLinks = [...document.querySelectorAll(".nav-link[data-view]")];
const dashboardView = document.querySelector("#dashboard-view");
const reportsView = document.querySelector("#reports-view");
const pageTitle = document.querySelector(".topbar h1");
const pageEyebrow = document.querySelector(".topbar .eyebrow");

function showPage(view, updateHistory = true) {
    const selectedView = view === "reports" ? "reports" : "dashboard";
    dashboardView.hidden = selectedView !== "dashboard";
    reportsView.hidden = selectedView !== "reports";

    pageLinks.forEach((link) => {
        const isActive = link.dataset.view === selectedView;
        link.classList.toggle("active", isActive);
        if (isActive) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
    });

    pageTitle.textContent = selectedView === "reports" ? "Grade Reports" : "Dashboard";
    pageEyebrow.textContent = selectedView === "reports" ? "ACADEMIC PERFORMANCE" : "OVERVIEW";

    if (updateHistory && window.location.hash !== `#${selectedView}`) {
        window.history.pushState({ view: selectedView }, "", `#${selectedView}`);
    }
    if (selectedView === "reports" && typeof loadStudents === "function") {
        loadStudents();
    }
}

pageLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
        event.preventDefault();
        showPage(link.dataset.view);
    });
});

window.addEventListener("popstate", () => showPage(window.location.hash.slice(1), false));
window.addEventListener("hashchange", () => showPage(window.location.hash.slice(1), false));
showPage(window.location.hash.slice(1) || "dashboard", false);
