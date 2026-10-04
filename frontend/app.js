// statcard frontend — vanilla JS, no build step.

const form = document.getElementById("card-form");
const riotInput = document.getElementById("riot-id");
const regionSelect = document.getElementById("region");
const submitBtn = document.getElementById("submit-btn");
const previewImg = document.getElementById("preview");
const statusBox = document.getElementById("status");
const downloadLink = document.getElementById("download-link");

function setStatus(message, kind = "error") {
    statusBox.textContent = message;
    statusBox.className = `status visible ${kind}`;
}

function clearStatus() {
    statusBox.className = "status";
    statusBox.textContent = "";
}

function clearPreview() {
    previewImg.src = "";
    previewImg.hidden = true;
    downloadLink.hidden = true;
    downloadLink.href = "";
}

function validateRiotId(value) {
    const [name, sep, tag] = [
        value.slice(0, value.indexOf("#")),
        value.includes("#") ? "#" : "",
        value.slice(value.indexOf("#") + 1),
    ];
    return sep === "#" && name.trim().length > 0 && tag.trim().length > 0;
}

async function submitForm(event) {
    event.preventDefault();
    clearStatus();
    clearPreview();

    const riotId = riotInput.value.trim();
    if (!validateRiotId(riotId)) {
        setStatus('Invalid Riot ID. Use the format "Name#TAG".');
        return;
    }

    const region = regionSelect.value;
    const apiBase = window.STATCARD_API.replace(/\/$/, "");
    const url = `${apiBase}/api/valorant/${encodeURIComponent(riotId)}?region=${encodeURIComponent(region)}`;

    submitBtn.disabled = true;
    submitBtn.textContent = "Generating…";

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let message;
            try {
                const body = await response.json();
                message = typeof body.detail === "string" ? body.detail : body.detail?.message || "Unknown error";
            } catch {
                message = `HTTP ${response.status}`;
            }

            if (response.status === 429) {
                const retry = response.headers.get("Retry-After");
                setStatus(
                    `Rate limit reached. Try again in ${retry ?? "a few"} second${retry === "1" ? "" : "s"}.`,
                    "info"
                );
            } else if (response.status === 404) {
                setStatus(`Player "${riotId}" not found on region ${region.toUpperCase()}.`);
            } else if (response.status === 400) {
                setStatus(message);
            } else {
                setStatus(`Server error: ${message}`);
            }
            return;
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        previewImg.src = objectUrl;
        previewImg.hidden = false;

        downloadLink.href = objectUrl;
        downloadLink.download = `${riotId.replace("#", "_")}_${region}.png`;
        downloadLink.hidden = false;

        setStatus("Card generated successfully.", "info");
    } catch (err) {
        setStatus(`Network error: ${err.message}. Is the backend running?`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Generate";
    }
}

form.addEventListener("submit", submitForm);