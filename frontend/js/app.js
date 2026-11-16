async function checkBackendConnection() {
    const status = document.querySelector("#api-status");
    const stat = document.querySelector("#api-stat");

    try {
        const response = await fetch("/api/health");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        await response.json();
        status.className = "api-status online";
        status.innerHTML = "<i></i> Backend connected";
        stat.textContent = "Online";
    } catch (error) {
        status.className = "api-status offline";
        status.innerHTML = "<i></i> API unavailable";
        stat.textContent = "Offline";
        console.error("API connection error:", error);
    }
}

checkBackendConnection();
