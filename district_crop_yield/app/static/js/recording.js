// Handle text query submission
document.getElementById("queryForm").onsubmit = async (e) => {
    e.preventDefault();

    let formData = new FormData(e.target);
    let query = formData.get("query");

    // Append user message to chat box
    let messagesDiv = document.getElementById("messages");
    let userMsg = document.createElement("div");
    userMsg.classList.add("message", "user");
    userMsg.textContent = query;
    messagesDiv.appendChild(userMsg);

    // Clear input box
    e.target.query.value = "";
    
    document.getElementById("thinkingLoader").style.display = "flex";

    // Send query to backend
    let res = await fetch("/submit_query", { method: "POST", body: formData });
    let data = await res.json();

    document.getElementById("thinkingLoader").style.display = "none";

    // Append bot response to chat box
    let botMsg = document.createElement("div");
    botMsg.classList.add("message", "bot");
    botMsg.textContent = data.message;
    messagesDiv.appendChild(botMsg);

    // Auto-scroll to latest message
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
};


// helper: create notification DOM element from predicted_yield object
function createNotificationElement(baseline, recommendations) {
    const a = document.createElement("a");
    a.href = "#";
    a.className = "notification-item";

    const gross_revenue = baseline.gross_revenue ?? "N/A";
    const net_rev_after_market = baseline.net_revenue_after_marketing ?? "N/A";
    const net_farm_income = baseline.net_farm_income ?? "N/A";
    const seasonal_off_farm_income = baseline.seasonal_offfarm_income ?? "N/A";
    const total_available = baseline.total_available ?? "N/A";
    const seasonal_household_need = baseline.seasonal_household_need ?? "N/A";
    const emi_monthly_baseline = baseline.emi_monthly_baseline ?? "N/A";
    const seasonal_loan_outflow_baseline = baseline.seasonal_loan_outflow_baseline ?? "N/A";
    const seasonal_surplus_before_loan = baseline.surplus_before_loan ?? "N/A";
    const seasonal_surplus_after_loan = baseline.surplus_after_loan ?? "N/A";
    const debt_sustainability_index = baseline.debt_sustainability_index ?? "N/A";

    a.innerHTML = `
        <div>
            <strong>Net Farm Income:</strong> ${net_farm_income} &nbsp; | &nbsp; 
            <strong>Gross Revenue:</strong> ${gross_revenue} &nbsp; | &nbsp; 
            <strong>EMI (Monthly Baseline):</strong> ${emi_monthly_baseline}
        </div>`;

    a.addEventListener("click", (e) => {
        e.preventDefault();
        const params = new URLSearchParams({
            gross_revenue: gross_revenue !== "N/A" ? gross_revenue : "",
            net_revenue_after_marketing: net_rev_after_market !== "N/A" ? net_rev_after_market : "",
            net_farm_income: net_farm_income !== "N/A" ? net_farm_income : "",
            seasonal_offfarm_income: seasonal_off_farm_income !== "N/A" ? seasonal_off_farm_income : "",
            total_available: total_available !== "N/A" ? total_available : "",
            seasonal_household_need: seasonal_household_need !== "N/A" ? seasonal_household_need : "",
            emi_monthly_baseline: emi_monthly_baseline !== "N/A" ? emi_monthly_baseline : "",
            seasonal_loan_outflow_baseline: seasonal_loan_outflow_baseline !== "N/A" ? seasonal_loan_outflow_baseline : "",
            surplus_before_loan: seasonal_surplus_before_loan !== "N/A" ? seasonal_surplus_before_loan : "",
            surplus_after_loan: seasonal_surplus_after_loan !== "N/A" ? seasonal_surplus_after_loan : "",
            debt_sustainability_index: debt_sustainability_index !== "N/A" ? debt_sustainability_index : "",
            recommendations: recommendations ?? []

        });
        window.location.href = `/notification_page?${params.toString()}`;
    });

    return a;
}



// helper: show a short-lived submitted toast inside notification box
function showSubmittedToast(message = "Submitted") {
    const notifBox = document.getElementById("notificationList");
    if (!notifBox) return;

    const toast = document.createElement("div");
    toast.className = "toast-submitted";
    toast.textContent = message;

    // put on top
    notifBox.insertBefore(toast, notifBox.firstChild);

    // remove after 2.5s
    setTimeout(() => {
        if (toast && toast.parentNode) toast.parentNode.removeChild(toast);
    }, 2500);
}

// New infoForm handler
document.getElementById("infoForm").onsubmit = async (e) => {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting...";
    }

    // show immediate submitted toast
    showSubmittedToast("Submitted — fetching prediction...");

    try {
        let formData = new FormData(e.target);

        // call backend
        const res = await fetch("/submit_initial_inputs", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            // server error: show a failure notification
            const notifBox = document.querySelector(".notification-box");
            const errDiv = document.createElement("div");
            errDiv.className = "notification-item";
            errDiv.textContent = `Error: server responded with status ${res.status}`;
            notifBox.insertBefore(errDiv, notifBox.firstChild);
            return;
        }

        const data = await res.json();

        // data.predicted_yield expected to be an object with relevant fields
        const recommendations = data.recommendations || {};
        const baseline = data.baseline || {};

        // Append new notification to notification-box
        const notifBox = document.getElementById("notificationList");
        if (notifBox) {
            const el = createNotificationElement(baseline, recommendations);
            notifBox.insertBefore(el, notifBox.firstChild);
        }

        // optional: show a confirmation toast
        showSubmittedToast("Prediction received!");

    } catch (err) {
        console.error(err);
        const notifBox = document.getElementById("notificationList");

        if (notifBox) {
            const errDiv = document.createElement("div");
            errDiv.className = "notification-item";
            errDiv.textContent = `Network error: ${err.message}`;
            notifBox.insertBefore(errDiv, notifBox.firstChild);
        }
    } finally {
        // re-enable submit button
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit";
        }
    }
};


// Voice Recording
let mediaRecorder;
let audioChunks = [];

document.getElementById("startBtn").onclick = async () => {
    let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    document.getElementById("recordingLoader").style.display = "flex";

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
        document.getElementById("recordingLoader").style.display = "none";
        let blob = new Blob(audioChunks, { type: 'audio/webm' });
        let formData = new FormData();
        formData.append("audio", blob, "recording.webm");

        const response = await fetch("/upload_audio", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        const hindi_msg = data.hindi_text;
        const english_msg = data.english_text;

        // Create a new user message bubble
        let messagesDiv = document.getElementById("messages");
        let userBubble = document.createElement("div");
        userBubble.classList.add("message", "user");

        // Add audio player
        const audioElem = document.createElement("audio");
        audioElem.controls = true;
        audioElem.src = URL.createObjectURL(blob);
        userBubble.appendChild(audioElem);

        // Add Hindi transcription below audio
        const textElem = document.createElement("div");
        textElem.textContent = hindi_msg;
        textElem.style.marginTop = "5px"; // spacing below audio
        userBubble.appendChild(textElem);

        // Append to chat
        messagesDiv.appendChild(userBubble);

        document.getElementById("thinkingLoader").style.display = "flex";

        
        // --- Call /submit_query with English text ---
        let queryFormData = new FormData();
        queryFormData.append("query", english_msg);

        const queryResponse = await fetch("/submit_query", {
            method: "POST",
            body: queryFormData
        });

        document.getElementById("thinkingLoader").style.display = "none";

        const queryData = await queryResponse.json();

        // Append bot response to chat box
        let botMsg = document.createElement("div");
        botMsg.classList.add("message", "bot");
        botMsg.textContent = queryData.message;
        messagesDiv.appendChild(botMsg);
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Clear audio chunks
        audioChunks = [];
    };

    

    document.getElementById("stopBtn").disabled = false;
    document.getElementById("startBtn").disabled = true;
};

document.getElementById("stopBtn").onclick = () => {
    mediaRecorder.stop();
    document.getElementById("stopBtn").disabled = true;
    document.getElementById("startBtn").disabled = false;
};

const STORAGE_KEY = "repayment_notifications_v1";

function saveNotifList(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}
function loadNotifList() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}

// On DOMContentLoaded hydrate saved notifications
document.addEventListener("DOMContentLoaded", () => {
  const saved = loadNotifList();
  const container = document.getElementById("notificationList");
  saved.reverse().forEach(pred => { container.appendChild(createNotificationElement(pred)); });
});

// after inserting `el`:
let saved = loadNotifList(); saved.push(predicted); saveNotifList(saved);


