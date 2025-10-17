/**
 * 캐러셀 컴포넌트
 * 히어로 섹션의 이번 주 신규 발매 앨범 캐러셀
 */

class Carousel {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.track = null;
        this.items = [];
        this.currentIndex = 0;
        this.autoScrollInterval = null;

        // 옵션
        this.options = {
            autoScroll: options.autoScroll !== false,
            scrollInterval: options.scrollInterval || 3000,
            itemWidth: options.itemWidth || 280,
            gap: options.gap || 16,
            ...options
        };

        this.init();
    }

    init() {
        if (!this.container) {
            console.error('Carousel container not found');
            return;
        }

        this.track = this.container.querySelector('.carousel-track');
        if (!this.track) {
            console.error('Carousel track not found');
            return;
        }

        this.items = Array.from(this.track.children);

        // 이벤트 리스너
        this.setupEventListeners();

        // 자동 스크롤 시작
        if (this.options.autoScroll && this.items.length > 0) {
            this.startAutoScroll();
        }
    }

    setupEventListeners() {
        // 마우스 호버 시 자동 스크롤 정지
        this.container.addEventListener('mouseenter', () => {
            this.stopAutoScroll();
        });

        this.container.addEventListener('mouseleave', () => {
            if (this.options.autoScroll) {
                this.startAutoScroll();
            }
        });

        // 터치 이벤트 (모바일)
        let startX = 0;
        let scrollLeft = 0;

        this.track.addEventListener('touchstart', (e) => {
            startX = e.touches[0].pageX;
            scrollLeft = this.track.scrollLeft;
            this.stopAutoScroll();
        });

        this.track.addEventListener('touchmove', (e) => {
            const x = e.touches[0].pageX;
            const walk = (startX - x) * 2;
            this.track.scrollLeft = scrollLeft + walk;
        });

        this.track.addEventListener('touchend', () => {
            if (this.options.autoScroll) {
                this.startAutoScroll();
            }
        });
    }

    startAutoScroll() {
        this.stopAutoScroll();

        this.autoScrollInterval = setInterval(() => {
            this.scrollToNext();
        }, this.options.scrollInterval);
    }

    stopAutoScroll() {
        if (this.autoScrollInterval) {
            clearInterval(this.autoScrollInterval);
            this.autoScrollInterval = null;
        }
    }

    scrollToNext() {
        if (this.items.length === 0) return;

        this.currentIndex = (this.currentIndex + 1) % this.items.length;
        this.scrollToIndex(this.currentIndex);
    }

    scrollToPrev() {
        if (this.items.length === 0) return;

        this.currentIndex = (this.currentIndex - 1 + this.items.length) % this.items.length;
        this.scrollToIndex(this.currentIndex);
    }

    scrollToIndex(index) {
        if (index < 0 || index >= this.items.length) return;

        const scrollAmount = index * (this.options.itemWidth + this.options.gap);

        this.track.scrollTo({
            left: scrollAmount,
            behavior: 'smooth'
        });

        this.currentIndex = index;
    }

    destroy() {
        this.stopAutoScroll();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Carousel;
}
