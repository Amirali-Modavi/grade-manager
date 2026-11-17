const apiStatus = document.querySelector("#api-status");
const pageLinks = [...document.querySelectorAll(".nav-link[data-view]")];
const dashboardView = document.querySelector("#dashboard-view");
const reportsView = document.querySelector("#reports-view");
const pageTitle = document.querySelector("#page-title");
let currentView = null;

function setApiStatus(state, message) {
    if (!apiStatus) return;
    apiStatus.className = `api-status ${state}`.trim();
    apiStatus.replaceChildren();
    const indicator = document.createElement("i");
    indicator.setAttribute("aria-hidden", "true");
    apiStatus.append(indicator, document.createTextNode(message));
}

async function checkBackendConnection() {
    try {
        const response = await fetch("/api/health");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        await response.json();
        setApiStatus("online", "Backend connected");
    } catch (error) {
        setApiStatus("offline", "API unavailable");
        console.error("API connection error:", error);
    }
}

function showPage(view, updateHistory = true) {
    const selectedView = view === "reports" ? "reports" : "dashboard";
    const viewChanged = selectedView !== currentView;
    currentView = selectedView;

    dashboardView.hidden = selectedView !== "dashboard";
    reportsView.hidden = selectedView !== "reports";
    pageTitle.textContent = selectedView === "reports" ? "Grade reports" : "Dashboard";

    pageLinks.forEach((link) => {
        const isActive = link.dataset.view === selectedView;
        link.classList.toggle("active", isActive);
        if (isActive) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
    });

    if (updateHistory && window.location.hash !== `#${selectedView}`) {
        window.history.pushState({ view: selectedView }, "", `#${selectedView}`);
    }

    // Notify data modules without depending on their script load order.
    if (viewChanged) {
        window.dispatchEvent(new CustomEvent("grade-manager:view-change", {
            detail: { view: selectedView },
        }));
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

checkBackendConnection();
showPage(window.location.hash.slice(1) || "dashboard", false);
