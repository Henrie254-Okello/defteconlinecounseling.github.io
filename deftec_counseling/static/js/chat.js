const appointmentId = JSON.parse(document.getElementById('appointment-id').textContent);
const chatSocket = new WebSocket(
    'ws://' + window.location.host +
    '/ws/chat/' + appointmentId + '/'
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'chat_message') {
        document.querySelector('#chat-messages').innerHTML += '<p><strong>' + data.sender + ':</strong> ' + data.message + '</p>';
    } else if (data.type === 'chat_history') {
        data.messages.forEach(msg => {
            document.querySelector('#chat-messages').innerHTML += '<p><strong>' + msg.sender + ':</strong> ' + msg.message + '</p>';
        });
    } else if (data.type === 'offer' || data.type === 'answer' || data.type === 'ice_candidate') {
        // Handle WebRTC signaling (see webrtc.js)
        handleSignaling(data);
    }
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'message': message
    }));
    messageInputDom.value = '';
};