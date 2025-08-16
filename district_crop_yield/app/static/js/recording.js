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

    queryInput.value = "";
    queryInput.placeholder = "Type your question...";
    
    // Send query to backend
    let res = await fetch("/submit_query", { method: "POST", body: formData });
    let data = await res.json();

    // Append bot response to chat box
    let botMsg = document.createElement("div");
    botMsg.classList.add("message", "bot");
    botMsg.textContent = data.message;
    messagesDiv.appendChild(botMsg);

    // Clear input box
    e.target.query.value = "";

    // Auto-scroll to latest message
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
};


// Initial Inputs
document.getElementById("infoForm").onsubmit = async (e) => {
    e.preventDefault();
    let formData = new FormData(e.target);
    let res = await fetch("/submit_initial_inputs", { method: "POST", body: formData });
    let data = await res.json();
    alert(data.message);
};


// Voice Recording
let mediaRecorder;
let audioChunks = [];

document.getElementById("startBtn").onclick = async () => {
    let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
        let blob = new Blob(audioChunks, { type: 'audio/webm' });
        let formData = new FormData();
        formData.append("audio", blob, "recording.webm");

        const response = await fetch("/upload_audio", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        const hindi_msg = data.hindi_text;

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

document.querySelectorAll('.notification-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault(); // prevent default anchor behavior

        // Get data attributes from the link
        const revenue = this.dataset.revenue;
        const expenses = this.dataset.expenses;
        const netCashFlow = this.dataset.net_cash_flow;
        const loanRepayment = this.dataset.loan_repayment;

        // Build correct URL for your Flask route
        const url = `/notification_page?revenue=${encodeURIComponent(revenue)}&expenses=${encodeURIComponent(expenses)}&net_cash_flow=${encodeURIComponent(netCashFlow)}&loan_repayment=${encodeURIComponent(loanRepayment)}`;

        window.location.href = url;
    });
});

