// static/js/notifications.js

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
        this.socket = new WebSocket(`${protocol}//${window.location.host}/ws/notifications/`);
        console.log('Connecting to WebSocket:', wsUrl);
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