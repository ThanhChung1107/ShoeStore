console.log('✅ notifications.js loaded successfully!');
class NotificationManager {
    constructor() {
        this.socket = null;
        this.newPostCount = 0;
        this.connect();
    }

    connect() {
        // Chỉ kết nối nếu user đã đăng nhập
        if (!this.isUserLoggedIn()) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        console.log('Connecting to WebSocket:', wsUrl); // ĐÃ SỬA
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleNotification(data);
        };

        this.socket.onclose = (e) => {
            console.log('WebSocket disconnected. Attempting to reconnect...');
            setTimeout(() => this.connect(), 3000);
        };

        this.socket.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    }

    handleNotification(data) {
        switch (data.type) {
            case 'new_post':
                this.showNewPostNotification(data);
                break;
            case 'notification':
                this.showGeneralNotification(data.message);
                break;
        }
    }

    showNewPostNotification(data) {
        // Tăng counter
        this.newPostCount++;
        
        const notification = {
            title: 'Bài viết mới',
            message: `Có ${this.newPostCount} bài viết mới`,
            url: `/blog/` // Link đến trang blog chung
        };

        this.createNotification(notification);
    }
    resetNewPostCount() {
        this.newPostCount = 0;
    }

    showGeneralNotification(message) {
        this.createNotification({
            title: 'Thông báo',
            message: message,
        });
    }

    createNotification(notification) {
        // Kiểm tra xem browser có hỗ trợ Notification API không
        if (!('Notification' in window)) {
            console.log('Trình duyệt không hỗ trợ thông báo');
            return;
        }

        // Yêu cầu quyền hiển thị thông báo
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    this.showBrowserNotification(notification);
                }
            });
        } else if (Notification.permission === 'granted') {
            this.showBrowserNotification(notification);
        }

        // Hiển thị thông báo trong UI
        this.showInAppNotification(notification);
    }

    showBrowserNotification(notification) {
        const notif = new Notification(notification.title, {
            body: notification.message,
            icon: notification.icon
        });

        notif.onclick = () => {
            window.focus();
            if (notification.url) {
                window.location.href = notification.url;
            }
            notif.close();
        };

        setTimeout(() => notif.close(), 5000);
    }

    showInAppNotification(notification) {
        // Tạo và hiển thị thông báo trong giao diện app
        const notificationElement = document.createElement('div');
        notificationElement.className = 'in-app-notification';
        notificationElement.innerHTML = `
            <div class="notification-content">
                <img src="${notification.icon}" alt="Notification" class="notification-icon">
                <div class="notification-text">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                </div>
                <button class="notification-close">&times;</button>
            </div>
        `;

        notificationElement.querySelector('.notification-close').onclick = () => {
            notificationElement.remove();
        };

        if (notification.url) {
            notificationElement.style.cursor = 'pointer';
            notificationElement.onclick = () => {
                window.location.href = notification.url;
            };
        }

        document.body.appendChild(notificationElement);

        // Tự động ẩn sau 5 giây
        setTimeout(() => {
            if (notificationElement.parentNode) {
                notificationElement.remove();
            }
        }, 5000);
    }

    isUserLoggedIn() {
        // Kiểm tra xem user có đăng nhập không
        const metaTag = document.querySelector('meta[name="user-logged-in"]');
        return metaTag && metaTag.content === 'true';
    }
}

// Khởi tạo khi trang load
document.addEventListener('DOMContentLoaded', function() {
    window.notificationManager = new NotificationManager();
});

        // Global variables
        let postIdCounter = 0;

        // Modal functions
        function openPostModal() {
            document.getElementById('postModal').style.display = 'block';
            document.getElementById('postContent').focus();
        }

        function closePostModal() {
            document.getElementById('postModal').style.display = 'none';
            document.getElementById('postContent').value = '';
            document.getElementById('imageInput').value = '';
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('uploadText').style.display = 'block';
            document.getElementById('imageUpload').classList.remove('has-image');
            document.getElementById('submitPost').disabled = true;
        }

        // Image preview functions
        // JavaScript để xử lý form submission
function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    const uploadText = document.getElementById('uploadText');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            uploadText.style.display = 'none';
        }
        
        reader.readAsDataURL(input.files[0]);
        document.getElementById('submitPost').disabled = false;
    }
}

function removeImage(event) {
    event.stopPropagation();
    const preview = document.getElementById('imagePreview');
    const uploadText = document.getElementById('uploadText');
    const imageInput = document.getElementById('imageInput');
    
    preview.style.display = 'none';
    uploadText.style.display = 'block';
    imageInput.value = '';
    
    // Kiểm tra nếu không có nội dung và không có ảnh thì disable nút đăng
    const content = document.getElementById('postContent').value.trim();
    if (!content) {
        document.getElementById('submitPost').disabled = true;
    }
}

// Xử lý sự kiện input trên textarea
document.getElementById('postContent').addEventListener('input', function() {
    const content = this.value.trim();
    const imageInput = document.getElementById('imageInput');
    const hasImage = imageInput.files.length > 0;
    
    document.getElementById('submitPost').disabled = !(content || hasImage);
});

// Xử lý submit form
document.getElementById('postForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitBtn = document.getElementById('submitPost');
    
    // Hiển thị loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang đăng...';
    
    // Gửi request AJAX
    fetch('/blog/post/create-ajax/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Đóng modal và làm mới trang hoặc thêm bài viết mới vào DOM
            closePostModal();
            alert(data.message);
            window.location.reload(); // Hoặc cập nhật DOM động
        } else {
            alert(data.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Đăng';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi đăng bài');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Đăng';
    });
});


        function checkSubmitButton() {
            const content = document.getElementById('postContent').value.trim();
            const hasImage = document.getElementById('imagePreview').style.display === 'block';
            document.getElementById('submitPost').disabled = !content && !hasImage;
        }

        // Create post function
        function createPost() {
    const content = document.getElementById('postContent').value.trim();
    const imageFile = document.getElementById('imageInput').files[0];
    
    if (!content && !imageFile) return;

    // Show loading
    const submitBtn = document.getElementById('submitPost');
    const originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<div class="loading"></div>';
    submitBtn.disabled = true;

    // Simulate posting delay
    setTimeout(() => {
        const postsContainer = document.querySelector('.posts-container');
        const newPost = document.createElement('div');
        newPost.className = 'post';
        
        let imageHTML = '';
        if (imageFile) {
            const imageURL = URL.createObjectURL(imageFile);
            imageHTML = `<div class="post-image"><img src="${imageURL}" alt="User uploaded image"></div>`;
        }

        postIdCounter++;
        newPost.innerHTML = `
            <div class="post-header">
                <div class="post-avatar">TN</div>
                <div class="post-author-info">
                    <h4>Tên người dùng</h4>
                    <div class="post-time">Vừa xong</div>
                </div>
            </div>
            <div class="post-content">
                ${content ? `<div class="post-text">${content}</div>` : ''}
                ${imageHTML}
            </div>
            <div class="post-stats">
                <div class="like-count" onclick="toggleLike(this.closest('.post').querySelector('.action-btn'))">
                    <div class="like-icon">❤</div>
                    <span>0</span>
                </div>
                <div>0 bình luận</div>
            </div>
            <div class="post-actions">
                <button class="action-btn" onclick="toggleLike(this)">
                    <i class="far fa-heart"></i>
                    Thích
                </button>
                <button class="action-btn" onclick="toggleComments(this)">
                    <i class="far fa-comment"></i>
                    Bình luận
                </button>
                <button class="action-btn">
                    <i class="far fa-share"></i>
                    Chia sẻ
                </button>
            </div>
            <div class="comments-section" style="display: none;">
                <div class="comment-form">
                    <div class="comment-avatar">TN</div>
                    <input type="text" class="comment-input" placeholder="Viết bình luận..." onkeypress="handleCommentSubmit(event, this)">
                    <button class="comment-submit" onclick="submitComment(this)">Gửi</button>
                </div>
            </div>
        `;

        // Insert new post at the beginning
        postsContainer.insertBefore(newPost, postsContainer.firstChild);
        
        // Reset form and close modal
        submitBtn.innerHTML = originalText;
        closePostModal();
        
        // Show success message
        showNotification('Bài viết đã được đăng thành công!');
    }, 1000);
} // <-- ĐÂY LÀ DẤU ĐÓNG NGOẶC BỊ THIẾU

// Like functionality
function toggleLike(button, postId) {
    fetch(`/blog/post/${postId}/like/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"), // lấy token csrf
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const post = button.closest('.post');
            const likeCountElement = post.querySelector('.like-count span');
            const likeIcon = button.querySelector('i');

            // Cập nhật icon theo trạng thái liked
            if (data.liked) {
                button.classList.add('liked');
                likeIcon.className = 'fas fa-heart';
                
                // animation
                button.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 200);
            } else {
                button.classList.remove('liked');
                likeIcon.className = 'far fa-heart';
            }

            // Luôn update số lượng từ server (tránh sai lệch)
            likeCountElement.textContent = data.total_likes;
        } else {
            alert("Lỗi: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error:", err);
    });
}
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

// Thêm debug để kiểm tra
function handleCommentSubmit(event, input, postId) {
    console.log('Post ID:', postId); // Debug
    if (event.key === 'Enter') {
        event.preventDefault();
        submitComment(input, postId);
    }
}

// Gửi comment
function submitComment(button, postId) {
    if (!isUserLoggedIn()) {
        alert('Vui lòng đăng nhập để bình luận');
        return;
    }

    let input;
    if (button.tagName === 'BUTTON') {
        input = button.previousElementSibling;
    } else {
        input = button;
        button = input.nextElementSibling;
    }
    
    const commentText = input.value.trim();
    
    if (!commentText) {
        alert('Vui lòng nhập nội dung bình luận');
        return;
    }
    
    // Vô hiệu hóa nút gửi tạm thời
    button.disabled = true;
    button.textContent = 'Đang gửi...';
    
    fetch(`/blog/${postId}/comment/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: commentText
        })
    })
    .then(response => response.json())
    .then(data => {
        button.disabled = false;
        button.textContent = 'Gửi';
        
        if (data.success) {
            // Thêm comment mới vào DOM
            const commentsSection = button.closest('.comments-section');
            const commentForm = commentsSection.querySelector('.comment-form');
            
            const newComment = document.createElement('div');
            newComment.className = 'comment';
            newComment.innerHTML = `
                <div class="comment-avatar">${data.user_avatar}</div>
                <div class="comment-content">
                    <div class="comment-bubble">
                        <div class="comment-author">${data.user_name}</div>
                        <div class="comment-text">${data.content}</div>
                    </div>
                    <div class="comment-time">${data.created_at}</div>
                </div>
            `;
            
            commentsSection.insertBefore(newComment, commentForm);
            input.value = '';
            
            // Cập nhật số lượng comment
            const commentCountElement = button.closest('.post').querySelector('.post-stats div:nth-child(2)');
            const currentCount = parseInt(commentCountElement.textContent) || 0;
            commentCountElement.textContent = `${currentCount + 1} bình luận`;
            
        } else {
            alert('Lỗi khi gửi bình luận: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.disabled = false;
        button.textContent = 'Gửi';
        alert('Có lỗi xảy ra khi gửi bình luận');
    });
}

// Hiển thị/ẩn comments
function toggleComments(button) {
    const commentsSection = button.closest('.post').querySelector('.comments-section');
    if (commentsSection.style.display === 'none') {
        commentsSection.style.display = 'block';
        button.innerHTML = '<i class="far fa-comment"></i> Ẩn bình luận';
    } else {
        commentsSection.style.display = 'none';
        button.innerHTML = '<i class="far fa-comment"></i> Bình luận';
    }
}


        // Utility functions
        function showNotification(message) {
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #42a5f5;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                font-weight: 600;
                animation: slideInRight 0.3s ease-out;
            `;
            notification.textContent = message;
            
            // Add animation keyframes if not exist
            if (!document.querySelector('#notification-styles')) {
                const style = document.createElement('style');
                style.id = 'notification-styles';
                style.textContent = `
                    @keyframes slideInRight {
                        from {
                            transform: translateX(100%);
                            opacity: 0;
                        }
                        to {
                            transform: translateX(0);
                            opacity: 1;
                        }
                    }
                    @keyframes slideOutRight {
                        from {
                            transform: translateX(0);
                            opacity: 1;
                        }
                        to {
                            transform: translateX(100%);
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(notification);
            
            // Remove after 3 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOutRight 0.3s ease-in forwards';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }

        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }

        // Add auto-resize to modal textarea
        document.getElementById('postContent').addEventListener('input', function() {
            autoResize(this);
        });

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Blog Community loaded successfully!');
            
            // Add some interactivity to existing posts
            document.querySelectorAll('.comment-input').forEach(input => {
                input.addEventListener('keypress', function(event) {
                    if (event.key === 'Enter') {
                        event.preventDefault();
                        submitComment(this.nextElementSibling);
                    }
                });
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            // Escape to close modal
            if (event.key === 'Escape') {
                if (document.getElementById('postModal').style.display === 'block') {
                    closePostModal();
                }
            }
            
            // Ctrl/Cmd + Enter to submit post
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                if (document.getElementById('postModal').style.display === 'block') {
                    if (!document.getElementById('submitPost').disabled) {
                        createPost();
                    }
                }
            }
        });

        // Smooth scrolling for new posts
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }

        // Add some sample interactions for demo
        setTimeout(() => {
            showNotification('Chào mừng bạn đến với Blog Community! 👋');
        }, 1000)
// Toggle reply form
function toggleReplyForm(commentId) {
    if (!isUserLoggedIn()) {
        alert('Vui lòng đăng nhập để phản hồi');
        return;
    }
    
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    replyForm.style.display = replyForm.style.display === 'none' ? 'flex' : 'none';
}

// Gửi reply
function submitReply(button, postId, parentCommentId) {
    const input = button.previousElementSibling;
    const replyText = input.value.trim();
    
    if (!replyText) {
        alert('Vui lòng nhập nội dung phản hồi');
        return;
    }
    
    button.disabled = true;
    button.textContent = 'Đang gửi...';
    
    fetch(`/blog/post/${postId}/comment/${parentCommentId}/reply/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: replyText
        })
    })
    .then(response => response.json())
    .then(data => {
        button.disabled = false;
        button.textContent = 'Gửi';
        
        if (data.success) {
            // Thêm reply vào DOM
            const commentElement = document.querySelector(`[data-comment-id="${parentCommentId}"]`);
            const repliesContainer = commentElement.querySelector('.comment-replies');
            
            const newReply = document.createElement('div');
            newReply.className = 'comment reply';
            newReply.innerHTML = `
                <div class="comment-avatar">${data.user_avatar || data.user_name.slice(0, 2).toUpperCase()}</div>
                <div class="comment-content">
                    <div class="comment-bubble">
                        <div class="comment-author">${data.user_name}</div>
                        <div class="comment-text">${data.content}</div>
                        <div class="comment-actions">
                            <button class="comment-action-btn" onclick="toggleLikeComment(${data.comment_id})">
                                <i class="far fa-heart"></i> Like
                            </button>
                            <span class="comment-likes">0 likes</span>
                        </div>
                    </div>
                    <div class="comment-time">${data.created_at}</div>
                </div>
            `;
            
            repliesContainer.appendChild(newReply);
            input.value = '';
            document.getElementById(`reply-form-${parentCommentId}`).style.display = 'none';
            
        } else {
            alert('Lỗi: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.disabled = false;
        button.textContent = 'Gửi';
        alert('Có lỗi xảy ra khi gửi phản hồi');
    });
}

// Like comment
function toggleLikeComment(commentId) {
    if (!isUserLoggedIn()) {
        alert('Vui lòng đăng nhập để thích bình luận');
        return;
    }
    
    fetch(`/blog/comment/${commentId}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cập nhật số like
            const likesElement = document.querySelector(`[data-comment-id="${commentId}"] .comment-likes`) || 
                                document.querySelector(`.comment[data-comment-id="${commentId}"] .comment-likes`);
            if (likesElement) {
                likesElement.textContent = `${data.total_likes} likes`;
            }
        } else {
            alert('Lỗi: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Xử lý submit reply bằng Enter
function handleReplySubmit(event, input, postId, parentCommentId) {
    if (event.key === 'Enter') {
        event.preventDefault();
        submitReply(input.nextElementSibling, postId, parentCommentId);
    }
}
