// Xử lý mở modal chat khi admin click vào phòng
document.querySelectorAll('.join-room-btn').forEach(button => {
    button.addEventListener('click', function() {
        const roomName = this.parentElement.parentElement.getAttribute('data-room-name');
        openAdminChatModal(roomName);
    });
});

// Đóng modal
document.querySelector('.close-modal').addEventListener('click', function() {
    document.getElementById('admin-chat-modal').style.display = 'none';
    if (adminChatSocket) {
        adminChatSocket.close();
    }
});

let adminChatSocket;

function openAdminChatModal(roomName) {
    document.getElementById('modal-room-name').textContent = `Chat: ${roomName}`;
    document.getElementById('admin-chat-modal').style.display = 'block';
    console.log('Connecting to WS:', 'ws://' + window.location.host + '/ws/chat/' + roomName + '/');
    // Kết nối WebSocket
    adminChatSocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/chat/' + roomName + '/'
    );
    
    adminChatSocket.onmessage = function(e) {
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
        
        document.querySelector('#admin-chat-messages').appendChild(messageElement);
        document.querySelector('#admin-chat-messages').scrollTop = document.querySelector('#admin-chat-messages').scrollHeight;
    };
    
    adminChatSocket.onclose = function(e) {
        console.error('Admin chat socket closed unexpectedly');
    };
    
    document.querySelector('#admin-chat-input').focus();
    document.querySelector('#admin-chat-input').onkeyup = function(e) {
        if (e.keyCode === 13) {
            document.querySelector('#admin-chat-submit').click();
        }
    };
    
    document.querySelector('#admin-chat-submit').onclick = function(e) {
        const messageInputDom = document.querySelector('#admin-chat-input');
        const message = messageInputDom.value;
        
        if (message) {
            adminChatSocket.send(JSON.stringify({
                'message': message,
                'sender_id': currentUserId
            }));
            messageInputDom.value = '';
        }
    };
}


document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chat-button');
    const chatModal = document.getElementById('chat-modal');
    const closeModal = document.querySelector('.close-modal');
    let userChatSocket;
    
    // Mở modal chat
    chatButton.addEventListener('click', function() {
        chatModal.style.display = 'block';
        
        // Nếu là user thường, tạo room nếu chưa có
        if (!userIsAdmin) {
            createChatRoom();
        }
    });
    
    // Đóng modal
    closeModal.addEventListener('click', function() {
        chatModal.style.display = 'none';
        if (userChatSocket) {
            userChatSocket.close();
        }
    });
    
    // Đóng modal khi click bên ngoài
    window.addEventListener('click', function(event) {
        if (event.target == chatModal) {
            chatModal.style.display = 'none';
            if (userChatSocket) {
                userChatSocket.close();
            }
        }
    });
    
    // Tạo room chat cho user
    function createChatRoom() {
        fetch('/chat/api/create-room/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.room_name) {
                connectToChatRoom(data.room_name);
            }
        })
        .catch(error => {
            console.error('Error creating chat room:', error);
        });
    }
    
    // Kết nối đến room chat
    function connectToChatRoom(roomName) {
        userChatSocket = new WebSocket(
            'ws://' + window.location.host +
            '/ws/chat/' + roomName + '/'
        );
        
        userChatSocket.onmessage = function(e) {
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
            
            document.querySelector('#user-chat-messages').appendChild(messageElement);
            document.querySelector('#user-chat-messages').scrollTop = document.querySelector('#user-chat-messages').scrollHeight;
        };
        
        userChatSocket.onclose = function(e) {
            console.error('User chat socket closed unexpectedly');
        };
        
        document.querySelector('#user-chat-input').focus();
        document.querySelector('#user-chat-input').onkeyup = function(e) {
            if (e.keyCode === 13) {
                document.querySelector('#user-chat-submit').click();
            }
        };
        
        document.querySelector('#user-chat-submit').onclick = function(e) {
            const messageInputDom = document.querySelector('#user-chat-input');
            const message = messageInputDom.value;
            
            if (message) {
                userChatSocket.send(JSON.stringify({
                    'message': message,
                    'sender_id': currentUserId
                }));
                messageInputDom.value = '';
            }
        };
    }
    
    // Hàm lấy CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});