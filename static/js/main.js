document.addEventListener("DOMContentLoaded", () => {
    const chatIcon = document.getElementById("chatbot-icon");
    const chatWindow = document.getElementById("chat-window");
    const chatLog = document.getElementById("chat-log");
    const userInput = document.getElementById("user-input");

    
    chatWindow.style.display = "none";

    chatIcon.addEventListener("click", () => {
        chatWindow.style.display = chatWindow.style.display === "none" ? "block" : "none";
    });

    // --- Initial Bot Greeting ---
    if(userInput && chatLog) {
        chatLog.innerHTML = `<div><b>Bot:</b> Hi ${userInput.dataset.username}! Thanks for logging in.</div>`;
    }

    // --- Flash Alerts (SweetAlert) ---
    const flashDataElem = document.getElementById("flash-data");
    if(flashDataElem) {
        const flashData = JSON.parse(flashDataElem.textContent || "[]");
        flashData.forEach(msg => {
            Swal.fire({
                icon: msg[0] === "success" ? "success" : msg[0] === "danger" ? "warning" : "info",
                title: msg[1],
                timer: 2000,
                showConfirmButton: false
            });
        });
    }

    // --- Send Chat Message ---
    function sendMessage() {
        const msg = userInput.value.trim();
        if (!msg) return;

        chatLog.innerHTML += `<div><b>You:</b> ${msg}</div>`;
        userInput.value = "";
        chatLog.scrollTop = chatLog.scrollHeight;

        fetch("/chatbot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        })
        .then(res => res.json())
        .then(data => {
            chatLog.innerHTML += `<div><b>Bot:</b> ${data.reply}</div>`;
            chatLog.scrollTop = chatLog.scrollHeight;
        });
    }

    // --- Enter Key Listener ---
    if(userInput) {
        userInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                sendMessage();
                e.preventDefault();
            }
        });
    }

    // Expose globally for button click
    window.sendMessage = sendMessage;
});
