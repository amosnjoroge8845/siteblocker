chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {

    if (!tab.url) {
        return;
    }

    try {

        const url = new URL(tab.url);

        const hostname =
            url.hostname.replace(/^www\./, "");

        chrome.storage.local.get(
            "blockedSites",
            function(result) {

                const sites =
                    result.blockedSites || [];

                const blocked =
                    sites.some(function(site) {

                        return hostname === site ||
                               hostname.endsWith("." + site);

                    });

                if (blocked) {

                    const blockedPage =
                        chrome.runtime.getURL("blocked.html");

                    const redirectURL =
                        blockedPage +
                        "?site=" +
                        encodeURIComponent(hostname);

                    chrome.tabs.update(tabId, {
                        url: redirectURL
                    });

                }

            }
        );

    } catch (error) {

        console.log("SiteBlocker error:", error);

    }

});