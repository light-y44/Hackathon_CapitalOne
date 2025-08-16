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
    let res = await fetch("/submit_finance_query", { method: "POST", body: formData });
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

        await fetch("/upload_audio", {
            method: "POST",
            body: formData
        });

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
