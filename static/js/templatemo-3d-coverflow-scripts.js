
        // Coverflow functionality
        const items = document.querySelectorAll('.coverflow-item');
        const dotsContainer = document.getElementById('dots');
        const currentTitle = document.getElementById('current-title');
        const currentDescription = document.getElementById('current-description');
        const container = document.querySelector('.coverflow-container');
        let currentIndex = 3;
        let isAnimating = false;

        const imageData = [
            {
                title: "Football Shoes",
                description: "Giày đá bóng năng động, bám sân tốt cho mọi trận đấu"
            },
            {
                title: "Badminton Shoes",
                description: "Giày cầu lông nhẹ, linh hoạt, thích hợp cho luyện tập"
            },
            {
                title: "Sandals",
                description: "Dép thoải mái, tiện lợi cho đi chơi hoặc đi biển"
            },
            {
                title: "Sneakers",
                description: "Giày thể thao phong cách streetwear, năng động và thời trang"
            },
            {
                title: "Running Shoes",
                description: "Giày chạy bộ êm ái, hỗ trợ vận động hàng ngày"
            },
            {
                title: "Formal Shoes",
                description: "Giày tây lịch sự, thích hợp đi làm hoặc dự tiệc"
            },
            {
                title: "Casual Sandals",
                description: "Dép xỏ ngón, phong cách thoải mái, thời trang"
            }
        ];


        // Create dots
        items.forEach((_, index) => {
            const dot = document.createElement('div');
            dot.className = 'dot';
            dot.onclick = () => goToIndex(index);
            dotsContainer.appendChild(dot);
        });

        const dots = document.querySelectorAll('.dot');
        let autoplayInterval = null;
        let isPlaying = true;
        const playIcon = document.querySelector('.play-icon');
        const pauseIcon = document.querySelector('.pause-icon');

        function updateCoverflow() {
            if (isAnimating) return;
            isAnimating = true;

            items.forEach((item, index) => {
                let offset = index - currentIndex;
                
                if (offset > items.length / 2) {
                    offset = offset - items.length;
                }
                else if (offset < -items.length / 2) {
                    offset = offset + items.length;
                }
                
                const absOffset = Math.abs(offset);
                const sign = Math.sign(offset);
                
                let translateX = offset * 220;
                let translateZ = -absOffset * 200;
                let rotateY = -sign * Math.min(absOffset * 60, 60);
                let opacity = 1 - (absOffset * 0.2);
                let scale = 1 - (absOffset * 0.1);

                if (absOffset > 3) {
                    opacity = 0;

                    translateX = sign * 800;
                }

                item.style.transform = `
                    translateX(${translateX}px) 
                    translateZ(${translateZ}px) 
                    rotateY(${rotateY}deg)
                    scale(${scale})
                `;
                item.style.opacity = opacity;
                item.style.zIndex = 100 - absOffset;

                item.classList.toggle('active', index === currentIndex);
            });

            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === currentIndex);
            });

            const currentData = imageData[currentIndex];
            currentTitle.textContent = currentData.title;
            currentDescription.textContent = currentData.description;
            
            currentTitle.style.animation = 'none';
            currentDescription.style.animation = 'none';
            setTimeout(() => {
                currentTitle.style.animation = 'fadeIn 0.6s forwards';
                currentDescription.style.animation = 'fadeIn 0.6s forwards';
            }, 10);

            setTimeout(() => {
                isAnimating = false;
            }, 600);
        }

        function navigate(direction) {
            if (isAnimating) return;
            
            currentIndex = currentIndex + direction;
            
            if (currentIndex < 0) {
                currentIndex = items.length - 1;
            } else if (currentIndex >= items.length) {
                currentIndex = 0;
            }
            
            updateCoverflow();
        }

        function goToIndex(index) {
            if (isAnimating || index === currentIndex) return;
            currentIndex = index;
            updateCoverflow();
        }

        // Keyboard navigation
        container.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') navigate(-1);
            if (e.key === 'ArrowRight') navigate(1);
        });

        // Click on items to select
        items.forEach((item, index) => {
            item.addEventListener('click', () => goToIndex(index));
        });

        // Touch/swipe support
        let touchStartX = 0;
        let touchEndX = 0;
        let touchStartY = 0;
        let touchEndY = 0;
        let isSwiping = false;

        container.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
            isSwiping = true;
        }, { passive: true });

        container.addEventListener('touchmove', (e) => {
            if (!isSwiping) return;
            
            const currentX = e.changedTouches[0].screenX;
            const diff = currentX - touchStartX;
            
            if (Math.abs(diff) > 10) {
                e.preventDefault();
            }
        }, { passive: false });

        container.addEventListener('touchend', (e) => {
            if (!isSwiping) return;
            
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleSwipe();
            isSwiping = false;
        }, { passive: true });

        function handleSwipe() {
            const swipeThreshold = 30;
            const diffX = touchStartX - touchEndX;
            const diffY = touchStartY - touchEndY;
            
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > swipeThreshold) {
                handleUserInteraction();
                
                if (diffX > 0) {
                    navigate(1);
                } else {
                    navigate(-1);
                }
            }
        }

        // Initialize images and reflections
        items.forEach((item, index) => {
            const img = item.querySelector('img');
            const reflection = item.querySelector('.reflection');
            
            img.onload = function() {

                this.parentElement.classList.remove('image-loading');
                reflection.style.setProperty('--bg-image', `url(${this.src})`);
                reflection.style.backgroundImage = `url(${this.src})`;
                reflection.style.backgroundSize = 'cover';
                reflection.style.backgroundPosition = 'center';
            };
            
            img.onerror = function() {
                this.parentElement.classList.add('image-loading');
            };
        });

        // Autoplay functionality
        function startAutoplay() {
            autoplayInterval = setInterval(() => {
                currentIndex = (currentIndex + 1) % items.length;
                updateCoverflow();
            }, 4000);
            isPlaying = true;
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
        }

        function stopAutoplay() {
            if (autoplayInterval) {
                clearInterval(autoplayInterval);
                autoplayInterval = null;
            }
            isPlaying = false;
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }

        function toggleAutoplay() {
            if (isPlaying) {
                stopAutoplay();
            } else {
                startAutoplay();
            }
        }

        function handleUserInteraction() {
            stopAutoplay();
        }

        // Add event listeners to stop autoplay on manual navigation
        items.forEach((item) => {
            item.addEventListener('click', handleUserInteraction);
        });

        document.querySelector('.nav-button.prev').addEventListener('click', handleUserInteraction);
        document.querySelector('.nav-button.next').addEventListener('click', handleUserInteraction);
        
        dots.forEach((dot) => {
            dot.addEventListener('click', handleUserInteraction);
        });

        container.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                handleUserInteraction();
            }
        });

        // Update active menu item on scroll
    

        // Smooth scroll to section

        // Scroll to top button

        // Form submission
        function handleSubmit(event) {
            event.preventDefault();
            alert('Thank you for your message! We\'ll get back to you soon.');
            event.target.reset();
        }

        // Initialize
        updateCoverflow();
        startAutoplay();

document.addEventListener('DOMContentLoaded', function() {
    const track = document.querySelector('.slider-track');
    const items = document.querySelectorAll('.slider-item');
    const prevBtn = document.querySelector('.slider-prev');
    const nextBtn = document.querySelector('.slider-next');
    const dotsContainer = document.getElementById('sliderDots');
    
    if (!track || !items.length) return;
    
    let currentPosition = 0;
    let currentIndex = 0;
    const itemWidth = items[0].offsetWidth + 20; // width + gap
    
    // Create dots
    items.forEach((_, index) => {
        const dot = document.createElement('div');
        dot.className = 'slider-dot';
        if (index === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToSlide(index));
        dotsContainer.appendChild(dot);
    });
    
    const dots = document.querySelectorAll('.slider-dot');
    
    function updateSlider() {
        track.style.transform = `translateX(-${currentPosition}px)`;
        
        // Update active dot
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentIndex);
        });
    }
    
    function goToSlide(index) {
        currentIndex = index;
        currentPosition = index * itemWidth;
        updateSlider();
    }
    
    function nextSlide() {
        const maxIndex = Math.floor((items.length * itemWidth - track.offsetWidth) / itemWidth);
        if (currentIndex < maxIndex) {
            currentIndex++;
            currentPosition = currentIndex * itemWidth;
            updateSlider();
        }
    }
    
    function prevSlide() {
        if (currentIndex > 0) {
            currentIndex--;
            currentPosition = currentIndex * itemWidth;
            updateSlider();
        }
    }
    
    // Event listeners
    prevBtn.addEventListener('click', prevSlide);
    nextBtn.addEventListener('click', nextSlide);
    
    // Auto slide
    let autoSlideInterval = setInterval(nextSlide, 5000);
    
    // Pause on hover
    const slider = document.querySelector('.best-sellers-slider');
    slider.addEventListener('mouseenter', () => clearInterval(autoSlideInterval));
    slider.addEventListener('mouseleave', () => {
        autoSlideInterval = setInterval(nextSlide, 5000);
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        const newItemWidth = items[0].offsetWidth + 20;
        if (itemWidth !== newItemWidth) {
            currentPosition = Math.round(currentPosition / itemWidth) * newItemWidth;
            itemWidth = newItemWidth;
            updateSlider();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') prevSlide();
        if (e.key === 'ArrowRight') nextSlide();
    });
});