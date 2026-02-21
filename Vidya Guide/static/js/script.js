function sendMessage() {
    const msg = document.getElementById("userMsg").value;
    if (!msg) return;

    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML += `<div class='user-msg'>You: ${msg}</div>`;

    fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {
        chatBox.innerHTML += `<div class='ai-msg'>${data.reply}</div>`;
    });
}