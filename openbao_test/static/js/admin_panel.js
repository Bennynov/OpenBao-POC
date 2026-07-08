(function () {
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

    const sections = Array.isArray(payload.sections) ? payload.sections : [];
    const sectionsById = sections.reduce((lookup, section) => {
        lookup[section.id] = section;
        return lookup;
    }, {});

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

    const activeSecretBySection = {};
    let activeSectionId = null;
    let activeSecret = null;
    let isSubmitting = false;

    function getSection(sectionId) {
        return sectionsById[sectionId] || null;
    }

    function getSectionSecrets(sectionId) {
        const section = getSection(sectionId);
        if (!section || !Array.isArray(section.secrets)) {
            return [];
        }
        return section.secrets;
    }

    function updateHeader(section) {
        workspaceTitle.textContent = section.workspace_title;
        workspaceSubtitle.textContent = section.workspace_subtitle;
        workspaceIcon.textContent = section.icon;
    }

    function setActiveMenuItem(secretId) {
        secretMenuList.querySelectorAll(".secret-menu-item").forEach((item) => {
            item.classList.toggle("is-active", item.getAttribute("data-secret-id") === secretId);
        });
    }

    function showEditorEmptyState(show) {
        secretEditorEmpty.classList.toggle("is-hidden", !show);
        secretEditorForm.classList.toggle("is-hidden", show);
    }

    function triggerLogout() {
        const logoutForm = document.querySelector(".logout-inline-form");
        if (logoutForm) {
            logoutForm.requestSubmit();
        }
    }

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

    function openOverlay(sectionId) {
        if (!getSection(sectionId)) {
            return;
        }

        overlay.classList.add("is-open");
        overlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("overlay-open");
        renderSection(sectionId);
    }

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

    cards.forEach((card) => {
        card.addEventListener("click", function () {
            const sectionId = card.getAttribute("data-section-id");
            openOverlay(sectionId);
        });
    });

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
