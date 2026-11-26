const API_URL = "http://localhost:8000/api/analyses";

const form = document.getElementById("analysisForm");
const button = document.getElementById("analyzeButton");
const statusBox = document.getElementById("analysisStatus");

async function submitAnalysis(form) {
    const formData = new FormData(form);

    const response = await fetch(API_URL, {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "API request failed");
    }

    return data;
}

form.addEventListener("submit", async (event) => {

    // MUST prevent the browser's native form submission
    event.preventDefault();
    event.stopPropagation();

    console.log("Form submit intercepted");

    button.disabled = true;
    button.textContent = "Uploading...";

    statusBox.textContent = "Sending request...";
    statusBox.className = "api-status loading";

    try {

        const result = await submitAnalysis(form);

        statusBox.className = "api-status success";

        statusBox.textContent =
            `Success! Analysis ID: ${result.analysis_id}, Status: ${result.status}`;

    } catch (error) {

        statusBox.className = "api-status error";
        statusBox.textContent = error.message;

        console.error("Request error:", error);

    } finally {

        button.disabled = false;
        button.textContent = "Analyze Corporate Action";

    }

});