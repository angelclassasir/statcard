// statcard frontend — vanilla JS, no build step, no dependencies.

const form = document.getElementById("card-form");
const riotInput = document.getElementById("riot-id");
const submitBtn = document.getElementById("submit-btn");
const previewImg = document.getElementById("preview");
const skeleton = document.getElementById("skeleton");
const statusBox = document.getElementById("status");
const downloadLink = document.getElementById("download-link");
const previewSection = document.querySelector(".preview");

// Render's free tier can take ~50 s to wake up; give it some room.
const REQUEST_TIMEOUT_MS = 90000;

let countdownTimer = null;
let objectUrl = null;

function setStatus(message, kind = "error") {
    statusBox.textContent = message;
    statusBox.className = `status visible ${kind}`;
}

function clearStatus() {
    stopCountdown();
    statusBox.className = "status";
    statusBox.textContent = "";
}

function stopCountdown() {
    if (countdownTimer !== null) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
}

function startCountdown(seconds) {
    let left = seconds;
    setStatus(`Rate limit reached. Retry in ${left}s.`, "warn");
    countdownTimer = setInterval(() => {
        left -= 1;
        if (left <= 0) {
            stopCountdown();
            setStatus("You can try again now.", "info");
        } else {
            setStatus(`Rate limit reached. Retry in ${left}s.`, "warn");
        }
    }, 1000);
}

function isValidRiotId(value) {
    const hash = value.indexOf("#");
    if (hash === -1) return false;
    const name = value.slice(0, hash).trim();
    const tag = value.slice(hash + 1).trim();
    return name.length > 0 && tag.length > 0;
}

function sanitizeFilename(value) {
    return value.replace(/[\\/:*?"<>|#]/g, "_");
}

function releaseObjectUrl() {
    if (objectUrl !== null) {
        URL.revokeObjectURL(objectUrl);
        objectUrl = null;
    }
}

function setBusy(busy) {
    submitBtn.disabled = busy;
    submitBtn.textContent = busy ? "Generating…" : "Generate";
    previewSection.setAttribute("aria-busy", String(busy));
}

function clearPreview() {
    releaseObjectUrl();
    previewImg.onload = null;
    previewImg.onerror = null;
    previewImg.hidden = true;
    previewImg.classList.remove("enter");
    previewImg.removeAttribute("src");
    downloadLink.hidden = true;
    downloadLink.removeAttribute("href");
    skeleton.hidden = true;
}

riotInput.addEventListener("input", () => {
    const value = riotInput.value.trim();
    riotInput.classList.remove("is-valid", "is-invalid");
    if (value.length === 0) return;
    riotInput.classList.add(isValidRiotId(value) ? "is-valid" : "is-invalid");
});

async function readErrorBody(response) {
    try {
        return await response.json();
    } catch {
        return null;
    }
}

async function submitForm(event) {
    event.preventDefault();
    clearStatus();
    clearPreview();

    const riotId = riotInput.value.trim();
    if (!isValidRiotId(riotId)) {
        riotInput.classList.add("is-invalid");
        setStatus('Invalid Riot ID. Use the format "Name#TAG".');
        riotInput.focus();
        return;
    }

    const region = form.region.value;
    const apiBase = window.STATCARD_API.replace(/\/$/, "");
    const url = `${apiBase}/api/valorant/${encodeURIComponent(riotId)}?region=${encodeURIComponent(region)}`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    setBusy(true);
    skeleton.hidden = false;

    try {
        const response = await fetch(url, { signal: controller.signal });

        if (!response.ok) {
            skeleton.hidden = true;
            const body = await readErrorBody(response);
            const detail =
                typeof body?.detail === "string" ? body.detail : body?.detail?.message || "";

            if (response.status === 429) {
                const retry = Number(
                    body?.detail?.retry_after ??
                        response.headers.get("Retry-After") ??
                        60
                );
                startCountdown(Number.isFinite(retry) && retry > 0 ? retry : 60);
            } else if (response.status === 404) {
                setStatus(`Player "${riotId}" not found on region ${region.toUpperCase()}.`);
            } else if (response.status === 400) {
                setStatus(detail || "Invalid request.");
            } else if (response.status === 503) {
                setStatus("The stats provider is busy right now. Try again in a minute.");
            } else {
                setStatus(`Server error: ${detail || response.status}. Try again in a minute.`);
            }
            return;
        }

        const blob = await response.blob();
        releaseObjectUrl();
        objectUrl = URL.createObjectURL(blob);

        previewImg.onload = () => {
            skeleton.hidden = true;
            previewImg.hidden = false;
            previewImg.classList.add("enter");
            previewSection.setAttribute("aria-busy", "false");
        };
        previewImg.onerror = () => {
            skeleton.hidden = true;
            previewSection.setAttribute("aria-busy", "false");
            setStatus("The card could not be displayed. Please try again.");
        };
        previewImg.alt = `Valorant stat card for ${riotId}`;
        previewImg.src = objectUrl;

        downloadLink.href = objectUrl;
        downloadLink.download = `${sanitizeFilename(riotId)}_${region}.png`;
        downloadLink.hidden = false;

        setStatus("Card generated successfully.", "info");
    } catch (err) {
        skeleton.hidden = true;
        if (err.name === "AbortError") {
            setStatus(
                "The server is taking too long (it may be waking up). Try again in a moment.",
                "warn"
            );
        } else {
            setStatus(`Network error: ${err.message}. Is the backend reachable?`);
        }
    } finally {
        clearTimeout(timeout);
        setBusy(false);
    }
}

form.addEventListener("submit", submitForm);

// Game selector: only Valorant is live today; CS2 lights up in v3.
document.querySelectorAll(".game-tile").forEach((tile) => {
    tile.addEventListener("click", () => {
        if (tile.disabled) return;
        document.querySelectorAll(".game-tile").forEach((other) => {
            other.classList.toggle("is-active", other === tile);
            other.setAttribute("aria-pressed", other === tile ? "true" : "false");
        });
    });
});
