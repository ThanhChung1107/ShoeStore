// Sử dụng biến đã được định nghĩa trong template
document.addEventListener('DOMContentLoaded', function() {
    console.log('Script loaded');
    // Kiểm tra xem các biến đã được định nghĩa chưa
    if (typeof roomName === 'undefined') {
        console.error('roomName is not defined');
        return;
    }
    
    if (typeof currentUserId === 'undefined') {
        console.error('currentUserId is not defined');
        return;
    }

    const chatSocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/chat/' + roomName + '/'
    );
    console.log('Connecting to WebSocket at:', 'ws://' + window.location.host + '/ws/chat/' + roomName + '/');


    const chatMessages = document.querySelector('#chat-messages');
    const messageInput = document.querySelector('#chat-message-input');
    const messageSubmit = document.querySelector('#chat-message-submit');

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        
        if (data.sender_id == currentUserId) {
            messageElement.classList.add('my-message');
        } else {
            messageElement.classList.add('other-message');
        }
        
        messageElement.innerHTML = `
            <div class="message-content">${data.message}</div>
            <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
        `;
        
        chatMessages.appendChild(messageElement);
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    messageInput.focus();
    messageInput.onkeyup = function(e) {
        if (e.keyCode === 13) {  // enter key
            messageSubmit.click();
        }
    };

    messageSubmit.onclick = function(e) {
        const message = messageInput.value;
        
        if (message) {
            chatSocket.send(JSON.stringify({
                'message': message,
                'sender_id': currentUserId
            }));
            messageInput.value = '';
        }
    };
});