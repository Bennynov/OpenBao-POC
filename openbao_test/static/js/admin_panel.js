/**
 * @file Admin panel UI: opens a section's editor overlay, lists its
 * secrets and saves new values.
 *
 * Reads the section data that the server renders with json_script
 * (id "adminPanelData"). Before showing a secret's current value it asks
 * /introspect/ whether the user's roles are still valid, and logs the user
 * out if they aren't.
 */

/**
 * A secret as sent by build_sections_payload.
 * @typedef {Object} Secret
 * @property {string} id Secret id, unique within its section.
 * @property {string} label Name shown in the secret list.
 * @property {string} description Explanation shown in the editor.
 * @property {string} value Current value from OpenBao.
 */

/**
 * A section as sent by build_sections_payload.
 * @typedef {Object} Section
 * @property {string} id Section id.
 * @property {string} title Name shown on the card.
 * @property {string} icon Emoji shown on the card and header.
 * @property {string} workspace_title Heading of the overlay.
 * @property {string} workspace_subtitle Subheading of the overlay.
 * @property {Secret[]} secrets Editable secrets in this section.
 */

(function () {
    // --- Load the server data ------------------------------------------------

    const payloadElement = document.getElementById("adminPanelData");
    if (!payloadElement) {
        return;
    }

    let payload;
    try {
        payload = JSON.parse(payloadElement.textContent);
    } catch (_error) {
        return;
    }

    /** @type {Section[]} */
    const sections = Array.isArray(payload.sections) ? payload.sections : [];
    /** @type {Object<string, Section>} */
    const sectionsById = sections.reduce((lookup, section) => {
        lookup[section.id] = section;
        return lookup;
    }, {});

    // --- DOM references ------------------------------------------------------

    const cards = document.querySelectorAll(".section-card");

    const overlay = document.getElementById("workspaceOverlay");
    const overlayCloseButton = document.getElementById("overlayCloseButton");
    const workspaceTitle = document.getElementById("workspaceTitle");
    const workspaceSubtitle = document.getElementById("workspaceSubtitle");
    const workspaceIcon = document.getElementById("workspaceIcon");

    const secretMenuList = document.getElementById("secretMenuList");
    const secretEditorForm = document.getElementById("secretEditorForm");
    const secretEditorEmpty = document.getElementById("secretEditorEmpty");
    const activeSectionIdInput = document.getElementById("activeSectionId");
    const activeSecretIdInput = document.getElementById("activeSecretId");
    const activeSecretLabel = document.getElementById("activeSecretLabel");
    const activeSecretDescription = document.getElementById("activeSecretDescription");
    const activeSecretValue = document.getElementById("activeSecretValue");
    const activeSecretMessage = document.getElementById("activeSecretMessage");

    if (!overlay || !overlayCloseButton || !secretEditorForm) {
        return;
    }

    const saveButton = secretEditorForm.querySelector("button[type='submit']");

    // --- UI state ------------------------------------------------------------

    /** Last selected secret id per section, so reopening a section restores it. */
    const activeSecretBySection = {};
    /** @type {?string} */
    let activeSectionId = null;
    /** @type {?Secret} */
    let activeSecret = null;
    /** Prevents double submits while a save is in progress. */
    let isSubmitting = false;

    // --- Helpers -------------------------------------------------------------

    /**
     * Look up a section by id.
     * @param {string} sectionId
     * @returns {?Section} The section, or null if unknown.
     */
    function getSection(sectionId) {
        return sectionsById[sectionId] || null;
    }

    /**
     * Get the secrets of a section.
     * @param {string} sectionId
     * @returns {Secret[]} The secrets, or an empty array if none.
     */
    function getSectionSecrets(sectionId) {
        const section = getSection(sectionId);
        if (!section || !Array.isArray(section.secrets)) {
            return [];
        }
        return section.secrets;
    }

    /**
     * Show a section's title, subtitle and icon in the overlay header.
     * @param {Section} section
     */
    function updateHeader(section) {
        workspaceTitle.textContent = section.workspace_title;
        workspaceSubtitle.textContent = section.workspace_subtitle;
        workspaceIcon.textContent = section.icon;
    }

    /**
     * Highlight the selected secret in the secret list.
     * @param {string} secretId
     */
    function setActiveMenuItem(secretId) {
        secretMenuList.querySelectorAll(".secret-menu-item").forEach((item) => {
            item.classList.toggle("is-active", item.getAttribute("data-secret-id") === secretId);
        });
    }

    /**
     * Toggle between the editor form and the "no secrets" message.
     * @param {boolean} show True to show the empty state and hide the form.
     */
    function showEditorEmptyState(show) {
        secretEditorEmpty.classList.toggle("is-hidden", !show);
        secretEditorForm.classList.toggle("is-hidden", show);
    }

    /**
     * Log the user out by submitting the sign-out form (POST with CSRF token).
     */
    function triggerLogout() {
        const logoutForm = document.querySelector(".logout-inline-form");
        if (logoutForm) {
            logoutForm.requestSubmit();
        }
    }

    /**
     * Ask the server whether the user's roles are still valid.
     * Logs the user out if they aren't or if the request fails (fail closed).
     * @param {Function} onSuccess Called when the roles are confirmed.
     */
    function checkIntrospection(onSuccess) {
        const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
        const token = csrfInput ? csrfInput.value : "";
        fetch("/introspect/", {
            method: "POST",
            headers: { "X-CSRFToken": token },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === "logout") {
                    triggerLogout();
                } else {
                    onSuccess();
                }
            })
            .catch(() => {
                triggerLogout();
            });
    }

    // --- Rendering -----------------------------------------------------------

    /**
     * Select a secret and load it into the editor.
     * The current value is only shown after the roles are confirmed.
     * @param {Secret} secret
     */
    function setActiveSecret(secret) {
        activeSecret = secret;
        activeSecretBySection[activeSectionId] = secret.id;

        setActiveMenuItem(secret.id);
        showEditorEmptyState(false);

        activeSecretIdInput.value = secret.id;
        activeSecretLabel.textContent = secret.label;
        activeSecretDescription.textContent = secret.description || "";
        activeSecretValue.value = "";
        activeSecretValue.placeholder = "Verifying access...";
        activeSecretMessage.textContent = "";
        activeSecretMessage.className = "message";

        checkIntrospection(() => {
            activeSecretValue.placeholder = `Current: ${secret.value || ""}`;
        });
    }

    /**
     * Build the clickable secret list for a section.
     * Labels use textContent, so config values are never parsed as HTML.
     * @param {Secret[]} sectionSecrets
     */
    function renderSecretMenu(sectionSecrets) {
        secretMenuList.innerHTML = "";

        sectionSecrets.forEach((secret) => {
            const item = document.createElement("button");
            item.type = "button";
            item.className = "secret-menu-item";
            item.setAttribute("data-secret-id", secret.id);

            const label = document.createElement("span");
            label.className = "secret-menu-label";
            label.textContent = secret.label;

            item.appendChild(label);
            item.addEventListener("click", function () {
                setActiveSecret(secret);
            });

            secretMenuList.appendChild(item);
        });
    }

    /**
     * Fill the overlay with a section: header, secret list and editor.
     * Reselects the secret that was last open in this section, or the first one.
     * @param {string} sectionId
     */
    function renderSection(sectionId) {
        const section = getSection(sectionId);
        if (!section) {
            return;
        }

        activeSectionId = sectionId;
        if (activeSectionIdInput) {
            activeSectionIdInput.value = sectionId;
        }
        updateHeader(section);

        cards.forEach((card) => {
            card.classList.toggle("is-active", card.getAttribute("data-section-id") === sectionId);
        });

        const sectionSecrets = getSectionSecrets(sectionId);
        if (!sectionSecrets.length) {
            secretMenuList.innerHTML = '<div class="secret-menu-empty">No editable secrets in this section.</div>';
            activeSecret = null;
            showEditorEmptyState(true);
            return;
        }

        renderSecretMenu(sectionSecrets);

        const rememberedSecretId = activeSecretBySection[sectionId];
        const initialSecret = sectionSecrets.find((secret) => secret.id === rememberedSecretId) || sectionSecrets[0];
        setActiveSecret(initialSecret);
    }

    // --- Overlay -------------------------------------------------------------

    /**
     * Open the editor overlay for a section and lock page scrolling.
     * @param {string} sectionId
     */
    function openOverlay(sectionId) {
        if (!getSection(sectionId)) {
            return;
        }

        overlay.classList.add("is-open");
        overlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("overlay-open");
        renderSection(sectionId);
    }

    /**
     * Close the editor overlay and reset the selection state.
     */
    function closeOverlay() {
        overlay.classList.remove("is-open");
        overlay.setAttribute("aria-hidden", "true");
        document.body.classList.remove("overlay-open");

        cards.forEach((card) => card.classList.remove("is-active"));

        activeSectionId = null;
        activeSecret = null;
        if (activeSectionIdInput) {
            activeSectionIdInput.value = "";
        }
    }

    // --- Event listeners -----------------------------------------------------

    // Open a section when its card is clicked.
    cards.forEach((card) => {
        card.addEventListener("click", function () {
            const sectionId = card.getAttribute("data-section-id");
            openOverlay(sectionId);
        });
    });

    // Close with the × button, a click on the backdrop, or the Escape key.
    overlayCloseButton.addEventListener("click", closeOverlay);

    overlay.addEventListener("click", function (event) {
        if (event.target.hasAttribute("data-overlay-close")) {
            closeOverlay();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && overlay.classList.contains("is-open")) {
            closeOverlay();
        }
    });

    // Save the new value as JSON to the current page (secret_updater POST).
    secretEditorForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (!activeSecret || isSubmitting) {
            return;
        }

        const sectionId = (activeSectionIdInput && activeSectionIdInput.value) || activeSectionId;
        const secretId = activeSecretIdInput.value;
        const value = activeSecretValue.value;
        const token = secretEditorForm.querySelector("[name=csrfmiddlewaretoken]").value;

        if (!sectionId || !secretId) {
            activeSecretMessage.textContent = "Secret selection is missing. Please reselect and try again.";
            activeSecretMessage.className = "message error";
            return;
        }

        isSubmitting = true;
        if (saveButton) {
            saveButton.disabled = true;
        }

        activeSecretMessage.textContent = "Saving...";
        activeSecretMessage.className = "message";

        try {
            const response = await fetch(window.location.pathname, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": token,
                },
                body: JSON.stringify({ section_id: sectionId, secret_id: secretId, value }),
            });

            // Error pages can be HTML or plain text, so only parse JSON
            // when the server says it is JSON.
            let data = { message: "Request failed" };
            const contentType = response.headers.get("content-type") || "";

            if (contentType.includes("application/json")) {
                try {
                    data = await response.json();
                } catch (_parseError) {
                    data = { message: "Received invalid JSON response" };
                }
            } else {
                const textResponse = await response.text();
                if (textResponse && textResponse.trim()) {
                    data = { message: textResponse.trim() };
                }
            }

            if (data.status === "logout") {
                triggerLogout();
                return;
            }

            activeSecretMessage.textContent = data.message;
            activeSecretMessage.className = "message " + (response.ok ? "success" : "error");

            if (response.ok) {
                activeSecret.value = value;
                activeSecretValue.value = "";
                activeSecretValue.placeholder = `Current: ${value}`;
            }
        } catch (error) {
            activeSecretMessage.textContent = "Error: request failed";
            activeSecretMessage.className = "message error";
        } finally {
            isSubmitting = false;
            if (saveButton) {
                saveButton.disabled = false;
            }
        }
    });

    // Enter saves; Shift+Enter inserts a new line.
    activeSecretValue.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") {
            return;
        }

        if (event.shiftKey) {
            return;
        }

        event.preventDefault();
        secretEditorForm.requestSubmit();
    });
})();
