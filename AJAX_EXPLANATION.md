# 📡 Giải Thích AJAX trong product.html

File `product.html` sử dụng AJAX để tạo trải nghiệm người dùng mượt mà mà **không cần reload trang**. Có 3 phần AJAX chính:

---

## 1️⃣ **AJAX Tìm Kiếm - Lịch Sử & Gợi Ý**

### A. Load Lịch Sử Tìm Kiếm
```javascript
function loadSearchHistory() {
    fetch('/products/get-search-history/')
        .then(response => response.json())
        .then(data => {
            if (data.history && data.history.length > 0) {
                displaySearchHistory(data.history);
                showSearchDropdown();
            }
        })
        .catch(error => console.error('Error:', error));
}
```

**Cách hoạt động:**
- **Khi nào:** User click vào ô tìm kiếm
- **Gửi:** GET request tới `/products/get-search-history/`
- **Nhận về:** JSON `{history: [{id, query}, ...]}`
- **Làm gì:** Hiển thị dropdown danh sách tìm kiếm trước đó
- **Lợi ích:** User thấy ngay lịch sử mà không cần submit form

---

### B. Fetch Gợi Ý Tìm Kiếm
```javascript
function fetchSuggestions(query) {
    fetch(`/products/search-suggestions/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
                showSearchDropdown();
            }
        })
        .catch(error => console.error('Error:', error));
}
```

**Cách hoạt động:**
- **Khi nào:** User gõ ký tự vào ô tìm kiếm
- **Gửi:** GET request với `q=từkhoá` (VD: `/products/search-suggestions/?q=giay`)
- **Nhận về:** JSON `{suggestions: [{id, name, ...}, ...]}`
- **Làm gì:** Hiển thị dropdown gợi ý sản phẩm real-time
- **Lợi ích:** Autocomplete gợi ý khi đang gõ (UX tốt)

---

## 2️⃣ **AJAX Lọc Sản Phẩm - Filter**

### Hàm Chính
```javascript
function applyFiltersAjax() {
    // Bước 1: Thu thập các filter đã chọn
    const categories = [];
    const brands = [];
    const priceRanges = [];

    document.querySelectorAll('input[name="category"]:checked').forEach(cb => {
        if (cb.value !== 'all') categories.push(cb.value);
    });

    document.querySelectorAll('input[name="brand"]:checked').forEach(cb => {
        if (cb.value !== 'all') brands.push(cb.value);
    });

    document.querySelectorAll('input[name="price"]:checked').forEach(cb => {
        priceRanges.push(cb.value);
    });

    // Bước 2: Tạo URL parameters
    const params = new URLSearchParams();
    if (categories.length > 0) {
        categories.forEach(cat => params.append('categories[]', cat));
    }
    if (brands.length > 0) {
        brands.forEach(brand => params.append('brands[]', brand));
    }
    if (priceRanges.length > 0) {
        params.append('price_range', priceRanges[0]);
    }

    // Bước 3: Gửi AJAX request
    const filterUrl = '{% url "filter_products" %}';
    
    fetch(`${filterUrl}?${params.toString()}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        updateProductsDisplay(data);  // Bước 4: Cập nhật giao diện
    })
    .catch(error => console.error('Error:', error));
}
```

**Cách hoạt động chi tiết:**

| Bước | Mô Tả |
|------|-------|
| 1️⃣ Người dùng chọn checkbox filter (danh mục, thương hiệu, giá) | |
| 2️⃣ JavaScript lắng nghe sự kiện `change` | |
| 3️⃣ Gọi `applyFiltersAjax()` | |
| 4️⃣ Thu thập tất cả checkbox đã chọn | |
| 5️⃣ Tạo URL params như: `?categories[]=1&categories[]=2&brands[]=5&price_range=300000-500000` | |
| 6️⃣ Gửi GET request tới backend | |
| 7️⃣ Backend nhận filter → query DB → trả JSON | |
| 8️⃣ Frontend nhận dữ liệu → Cập nhật grid sản phẩm | |

### Hàm Cập Nhật Giao Diện
```javascript
function updateProductsDisplay(data) {
    const productsGrid = document.getElementById('productsGrid');
    
    // Cập nhật số lượng kết quả
    resultsCount.textContent = `Hiển thị ${data.count} sản phẩm`;
    
    // Parse JSON products từ backend
    const products = JSON.parse(data.products);
    
    // Fade out sản phẩm cũ
    productsGrid.style.opacity = '0.5';
    
    setTimeout(() => {
        // Xóa sản phẩm cũ
        productsGrid.innerHTML = '';
        
        // Thêm sản phẩm mới với animation
        products.forEach((productData, index) => {
            const productCard = createProductCard(product, productData.pk);
            productsGrid.appendChild(productCard);
            
            // Animation phần từ mới
            setTimeout(() => {
                productCard.style.opacity = '1';
                productCard.style.transform = 'translateY(0)';
            }, index * 100);  // Hiệu ứng dò
        });
        
        productsGrid.style.opacity = '1';
    }, 300);
}
```

**Lợi ích:**
- ✅ Không cần reload trang
- ✅ Animation mượt khi cập nhật
- ✅ UX tuyệt vời: thấy ngay kết quả filter

---

## 3️⃣ **AJAX Xóa Lịch Sử**

### A. Xóa Một Item
```javascript
function deleteHistoryItem(id, event) {
    event.stopPropagation();
    
    const deleteUrl = '/products/delete-search-history/';
    
    fetch(deleteUrl, {
        method: 'POST',  // POST vì là action (DELETE/modify)
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken'),  // ⚠️ Bảo mật CSRF
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `id=${id}`
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.warn('Xóa không thành công:', data.error);
        }
    })
    .catch(error => console.error('Lỗi:', error));
}
```

### B. Xóa Toàn Bộ
```javascript
function clearAllHistory() {
    if (!confirm('Bạn có chắc muốn xóa toàn bộ lịch sử?')) {
        return;
    }
    
    fetch('/products/clear-search-history/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Ẩn dropdown
            document.getElementById('searchDropdown').style.display = 'none';
        }
    });
}
```

**Điểm quan trọng:**
- ⚠️ **CSRF Token:** Luôn gửi kèm token để bảo mật
- 🔍 **POST vs GET:** DELETE/MODIFY = POST, chỉ lấy dữ liệu = GET
- 💾 **Backend:** Cập nhật database mà không cần reload

---

## 📊 **So Sánh: Cách Cũ vs AJAX**

### ❌ Cách Cũ (Form Submit)
```html
<form method="POST" action="/products/filter/">
    <input type="checkbox" name="category" value="1"> Danh mục 1
    <button type="submit">Lọc</button>
</form>
```
- Reload trang hoàn toàn
- Chậm, nháy nháy
- Mất URL history

### ✅ AJAX (Hiện Tại)
```javascript
// Checkbox tự động trigger filter
document.querySelectorAll('input').addEventListener('change', () => {
    applyFiltersAjax();  // Không reload, chỉ cập nhật
});
```
- Không reload
- Mượt, hiệu ứng animation
- URL không thay đổi

---

## 🔑 **Các Khái Niệm Chính**

### 1. `fetch()` API
```javascript
fetch(url, {options})
    .then(response => response.json())  // Parse JSON
    .then(data => {})                   // Xử lý data
    .catch(error => {})                 // Xử lý lỗi
```

### 2. HTTP Headers
```javascript
headers: {
    'X-Requested-With': 'XMLHttpRequest',  // Báo backend là AJAX
    'X-CSRFToken': csrfToken,               // Bảo mật CSRF
    'Content-Type': 'application/x-www-form-urlencoded'
}
```

### 3. URLSearchParams
```javascript
const params = new URLSearchParams();
params.append('key', 'value');
params.append('key', 'value2');  // Multiple values
// ?key=value&key=value2
```

### 4. Debounce (Trong Filter)
```javascript
input.addEventListener('input', debounce(applyFiltersAjax, 500));
// Chỉ gọi applyFiltersAjax 500ms sau khi user dừng gõ
```

---

## 🎯 **Tóm Tắt Quy Trình AJAX**

```
User Action
    ↓
JavaScript Event (change, input, click)
    ↓
Gọi hàm AJAX → Tạo params
    ↓
fetch() gửi request tới backend
    ↓
Backend xử lý → Trả JSON
    ↓
JavaScript nhận JSON → Parse
    ↓
Update DOM (innerHTML, style, attribute)
    ↓
Animation/Transition
    ↓
Cập nhật giao diện (không reload)
```

---

## 💡 **Lợi Ích của AJAX trong File Này**

| Feature | Lợi ích |
|---------|---------|
| **Filter Products** | Lọc ngay mà không reload |
| **Search Suggestions** | Autocomplete real-time |
| **Search History** | Nhanh chóng truy cập tìm kiếm cũ |
| **Delete History** | Xóa từng item mà không phải refresh |
| **No Page Reload** | Giữ scroll position, state |
| **Animation** | Trải nghiệm mềm mại |

---

**Kết luận:** AJAX trong file này tạo trải nghiệm "single-page app" (SPA) mà vẫn dùng Django template. Người dùng thấy kết quả ngay mà không cần chờ reload!
