// statcard frontend — vanilla JS, no build step, no dependencies.

const form = document.getElementById("card-form");
const riotInput = document.getElementById("riot-id");
const submitBtn = document.getElementById("submit-btn");
const previewImg = document.getElementById("preview");
const skeleton = document.getElementById("skeleton");
const statusBox = document.getElementById("status");
const downloadLink = document.getElementById("download-link");

let countdownTimer = null;

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

riotInput.addEventListener("input", () => {
    const value = riotInput.value.trim();
    riotInput.classList.remove("is-valid", "is-invalid");
    if (value.length === 0) return;
    riotInput.classList.add(isValidRiotId(value) ? "is-valid" : "is-invalid");
});

function clearPreview() {
    previewImg.hidden = true;
    previewImg.classList.remove("enter");
    previewImg.src = "";
    downloadLink.hidden = true;
    downloadLink.href = "";
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

    submitBtn.disabled = true;
    submitBtn.textContent = "Generating…";
    skeleton.hidden = false;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            skeleton.hidden = true;
            let detail;
            try {
                const body = await response.json();
                detail = typeof body.detail === "string" ? body.detail : body.detail?.message || "";
            } catch {
                detail = "";
            }

            if (response.status === 429) {
                let retry = 60;
                try {
                    retry = (await response.clone().json()).detail.retry_after ?? 60;
                } catch {
                    retry = parseInt(response.headers.get("Retry-After") ?? "60", 10);
                }
                setStatus(`Rate limit reached. Retry in ${retry}s.`, "warn");
                startCountdown(retry);
            } else if (response.status === 404) {
                setStatus(`Player "${riotId}" not found on region ${region.toUpperCase()}.`);
            } else if (response.status === 400) {
                setStatus(detail || "Invalid request.");
            } else {
                setStatus(`Server error: ${detail || response.status}. Try again in a minute.`);
            }
            return;
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);

        previewImg.onload = () => {
            skeleton.hidden = true;
            previewImg.hidden = false;
            previewImg.classList.add("enter");
        };
        previewImg.alt = `Valorant stat card for ${riotId}`;
        previewImg.src = objectUrl;

        downloadLink.href = objectUrl;
        downloadLink.download = `${riotId.replace("#", "_")}_${region}.png`;
        downloadLink.hidden = false;

        setStatus("Card generated successfully.", "info");
    } catch (err) {
        skeleton.hidden = true;
        setStatus(`Network error: ${err.message}. Is the backend reachable?`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Generate";
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