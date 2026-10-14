const params = new URLSearchParams(window.location.search);

const site = params.get("site");

if (site) {
    document.getElementById("site").textContent = site;
}