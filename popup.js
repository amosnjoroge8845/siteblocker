const input = document.getElementById("websiteInput");
const button = document.getElementById("addBtn");
const list = document.getElementById("blockedList");

const HELPER_URL = "http://127.0.0.1:8765/action";

// IMPORTANT:
// Put the token from token.txt between the quotes.
// Do NOT put your PIN here.
const TOKEN = "JmpZNzBUDo0K8vgMzAVV29d8eVIa5A72h_Jt8uzUVzM";


async function helper(action, site = "") {

    const response = await fetch(HELPER_URL, {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            action: action,
            site: site,
            token: TOKEN
        })
    });

    return await response.json();
}


// Display sites
function displaySites(sites) {

    list.innerHTML = "";

    sites.forEach(function(site) {

        const item = document.createElement("li");

        item.innerHTML = `
            <span>${site}</span>
            <button class="remove" data-site="${site}">
                Remove
            </button>
        `;

        list.appendChild(item);
    });
}


// Load sites from Windows helper
async function loadSites() {

    try {

        const result = await helper("list");

        if (result.error) {
            console.error(result.error);
            return;
        }

        displaySites(result.sites || []);

    } catch (error) {

        console.error(
            "Could not connect to Windows helper:",
            error
        );

    }
}


// BLOCK WEBSITE
button.addEventListener("click", async function() {

    let site = input.value.trim();

    if (!site) {
        alert("Enter a website first.");
        return;
    }

    site = site
        .replace(/^https?:\/\//, "")
        .replace(/^www\./, "")
        .split("/")[0];

    try {

        const result =
            await helper("block", site);

        if (result.error) {

            alert(result.error);
            return;

        }

        input.value = "";

        displaySites(result.sites || []);

    } catch (error) {

        alert(
            "Could not connect to Windows blocker."
        );

        console.error(error);
    }
});


// REMOVE WEBSITE
list.addEventListener("click", async function(event) {

    if (!event.target.classList.contains("remove")) {
        return;
    }

    const site =
        event.target.dataset.site;

    const pin =
        prompt(
            "Enter your administrator PIN to unblock this website:"
        );

    if (pin === null) {
        return;
    }

    try {

        const response = await fetch(
            HELPER_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    action: "unblock",
                    site: site,
                    pin: pin,
                    token: TOKEN
                })
            }
        );

        const result =
            await response.json();

        if (result.error) {

            alert(result.error);
            return;

        }

        displaySites(
            result.sites || []
        );

    } catch (error) {

        alert(
            "Could not connect to Windows blocker."
        );

        console.error(error);
    }
});


loadSites();