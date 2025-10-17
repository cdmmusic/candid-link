/**
 * 메인 JavaScript
 * 홈페이지 전체 기능
 */

// 전역 상태
const AppState = {
    currentView: 'grid', // 'grid' or 'list'
    currentPage: 1,
    hasMore: true,
    isLoading: false,
    albums: [],
    searchQuery: '',
    carousel: null
};

/**
 * 페이지 초기화
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 캔디드뮤직 링크 시작');

    initializeCarousel();
    initializeSearch();
    loadLatestAlbums();
    loadTop100Albums();
});

/**
 * 캐러셀 초기화
 */
function initializeCarousel() {
    const carouselContainer = document.getElementById('hero-carousel');
    if (!carouselContainer) return;

    // 이번 주 신규 발매 앨범 가져오기
    fetch('/api/albums-with-links?page=1&limit=8')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.albums.length > 0) {
                renderCarousel(data.albums);

                // Carousel 인스턴스 생성
                if (typeof Carousel !== 'undefined') {
                    AppState.carousel = new Carousel('hero-carousel', {
                        autoScroll: true,
                        scrollInterval: 4000
                    });
                }
            }
        })
        .catch(err => {
            console.error('캐러셀 로드 실패:', err);
        });
}

/**
 * 캐러셀 렌더링
 */
function renderCarousel(albums) {
    const track = document.getElementById('carousel-track');
    if (!track) {
        console.error('Carousel track not found');
        return;
    }

    if (albums.length === 0) {
        track.innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.8);">앨범이 없습니다</div>';
        return;
    }

    const html = albums.map(album => {
        const albumId = encodeURIComponent(album.artist_ko + '|||' + album.album_ko);
        const coverUrl = album.album_cover_url || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22280%22 height=%22280%22%3E%3Crect fill=%22%23999%22 width=%22280%22 height=%22280%22/%3E%3C/svg%3E';
        const title = album.album_ko || '제목 없음';
        const artist = album.artist_ko || '아티스트 없음';

        return `
            <a href="/album/${albumId}" class="carousel-item">
                <img src="${coverUrl}"
                     alt="${escapeHtml(title)}"
                     class="carousel-image"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22280%22 height=%22280%22%3E%3Crect fill=%22%23999%22 width=%22280%22 height=%22280%22/%3E%3C/svg%3E'">
                <div class="carousel-info">
                    <div class="carousel-title">${escapeHtml(title)}</div>
                    <div class="carousel-artist">${escapeHtml(artist)}</div>
                </div>
            </a>
        `;
    }).join('');

    track.innerHTML = html;
    console.log(`Carousel rendered with ${albums.length} items`);
}

/**
 * 검색 초기화
 */
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    // 실시간 검색 (디바운스)
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                performSearch(query);
            } else if (query.length === 0) {
                // 검색어가 비어있으면 초기 데이터 로드
                AppState.searchQuery = '';
                loadLatestAlbums();
                loadTop100Albums();
            }
        }, 300);
    });

    // 엔터키로 검색
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (query) {
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        }
    });
}

/**
 * 검색 수행
 */
function performSearch(query) {
    AppState.searchQuery = query;
    AppState.albums = [];
    AppState.currentPage = 1;

    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                AppState.albums = data.albums;
                AppState.hasMore = false; // 검색 결과는 페이지네이션 없음
                renderAlbums(AppState.albums, false);
            }
        })
        .catch(err => {
            console.error('검색 실패:', err);
        });
}

/**
 * 뷰 토글 초기화 (그리드/리스트)
 */
function initializeViewToggle() {
    const gridButton = document.querySelector('[data-view="grid"]');
    const listButton = document.querySelector('[data-view="list"]');

    if (!gridButton || !listButton) return;

    gridButton.addEventListener('click', () => {
        AppState.currentView = 'grid';
        updateViewToggle();
        renderAlbums(AppState.albums, false);
    });

    listButton.addEventListener('click', () => {
        AppState.currentView = 'list';
        updateViewToggle();
        renderAlbums(AppState.albums, false);
    });
}

/**
 * 뷰 토글 UI 업데이트
 */
function updateViewToggle() {
    const gridButton = document.querySelector('[data-view="grid"]');
    const listButton = document.querySelector('[data-view="list"]');
    const container = document.querySelector('.album-grid') || document.querySelector('.album-list');

    if (!gridButton || !listButton || !container) return;

    if (AppState.currentView === 'grid') {
        gridButton.classList.add('active');
        listButton.classList.remove('active');
        container.className = 'album-grid';
    } else {
        gridButton.classList.remove('active');
        listButton.classList.add('active');
        container.className = 'album-list';
    }
}

/**
 * 무한 스크롤 초기화
 */
function initializeInfiniteScroll() {
    window.addEventListener('scroll', () => {
        // 검색 중이면 무한 스크롤 비활성화
        if (AppState.searchQuery) return;
        if (!AppState.hasMore || AppState.isLoading) return;

        const scrollPosition = window.innerHeight + window.scrollY;
        const threshold = document.documentElement.offsetHeight - 500;

        if (scrollPosition >= threshold) {
            loadMoreAlbums();
        }
    });
}

/**
 * 최신 발매 앨범 로드 (8개만)
 */
function loadLatestAlbums() {
    fetch('/api/albums-with-links?page=1&limit=8')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.albums.length > 0) {
                renderAlbumsToContainer(data.albums, 'latest-grid');
            }
        })
        .catch(err => {
            console.error('최신 발매 로드 실패:', err);
        });
}

/**
 * TOP 100 앨범 로드 (10개만)
 */
function loadTop100Albums() {
    // TODO: 실제 TOP 100 API가 구현되면 여기서 호출
    // 지금은 임시로 최신 앨범 9-18번째 사용
    fetch('/api/albums-with-links?page=2&limit=10')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.albums.length > 0) {
                renderTop100List(data.albums);
            }
        })
        .catch(err => {
            console.error('TOP 100 로드 실패:', err);
        });
}

/**
 * TOP 100 랭킹 리스트 렌더링
 */
function renderTop100List(albums) {
    const container = document.getElementById('top100-list');
    if (!container) return;

    // 로딩 메시지 제거
    const loadingElement = container.querySelector('.loading');
    if (loadingElement) {
        loadingElement.remove();
    }

    if (albums.length === 0) {
        container.innerHTML = '<div class="no-data">등록된 앨범이 없습니다</div>';
        return;
    }

    const html = albums.map((album, index) => createRankingItemHTML(album, index + 1)).join('');
    container.innerHTML = html;
}

/**
 * 랭킹 아이템 HTML 생성
 */
function createRankingItemHTML(album, rank) {
    const albumId = encodeURIComponent(album.artist_ko + '|||' + album.album_ko);
    const coverUrl = album.album_cover_url || '';
    const title = album.album_ko || '';
    const artist = album.artist_ko || '';

    // 임시 데이터
    const viewCount = Math.floor(Math.random() * 50000) + 10000;
    const likeCount = Math.floor(Math.random() * 5000) + 500;

    // 순위 변동 (임시)
    const changes = ['up', 'down', 'new', 'same'];
    const changeType = changes[Math.floor(Math.random() * changes.length)];
    const changeValue = Math.floor(Math.random() * 10) + 1;

    let changeHTML = '';
    if (changeType === 'up') {
        changeHTML = `<span class="ranking-change up">▲ ${changeValue}</span>`;
    } else if (changeType === 'down') {
        changeHTML = `<span class="ranking-change down">▼ ${changeValue}</span>`;
    } else if (changeType === 'new') {
        changeHTML = `<span class="ranking-change new">NEW</span>`;
    } else {
        changeHTML = `<span class="ranking-change">-</span>`;
    }

    return `
        <a href="/album/${albumId}" class="ranking-item">
            <div class="ranking-number">${rank}</div>
            <img src="${coverUrl}"
                 alt="${escapeHtml(title)}"
                 class="ranking-cover"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23e9ecef%22 width=%22100%22 height=%22100%22/%3E%3C/svg%3E'">

            <div class="ranking-info">
                <div class="ranking-title">${escapeHtml(title)}</div>
                <div class="ranking-artist">${escapeHtml(artist)}</div>
            </div>

            <div class="ranking-stats">
                ${changeHTML}
                <div class="ranking-stat">
                    <span class="ranking-stat-icon view"></span>
                    <span>${formatNumber(viewCount)}</span>
                </div>
                <div class="ranking-stat">
                    <span class="ranking-stat-icon like"></span>
                    <span>${formatNumber(likeCount)}</span>
                </div>
            </div>
        </a>
    `;
}

/**
 * 특정 컨테이너에 앨범 렌더링
 */
function renderAlbumsToContainer(albums, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // 로딩 메시지 제거
    const loadingElement = container.querySelector('.loading');
    if (loadingElement) {
        loadingElement.remove();
    }

    if (albums.length === 0) {
        container.innerHTML = '<div class="no-data">등록된 앨범이 없습니다</div>';
        return;
    }

    const html = albums.map(album => createAlbumCardHTML(album)).join('');
    container.innerHTML = html;

    // 이미지 lazy loading
    lazyLoadImages();
}

/**
 * 더 많은 앨범 로드
 */
async function loadMoreAlbums() {
    if (AppState.isLoading || !AppState.hasMore) return;

    AppState.isLoading = true;
    showLoadingIndicator();

    try {
        console.log(`Loading page ${AppState.currentPage}...`);
        const response = await fetch(`/api/albums-with-links?page=${AppState.currentPage}&limit=30`);
        const data = await response.json();

        if (data.success) {
            const newAlbums = data.albums;
            console.log(`Loaded ${newAlbums.length} new albums`);

            // 첫 페이지면 전체 렌더링, 아니면 추가만
            if (AppState.currentPage === 1) {
                AppState.albums = newAlbums;
                renderAlbums(newAlbums, false);
            } else {
                AppState.albums = [...AppState.albums, ...newAlbums];
                appendNewAlbums(newAlbums);
            }

            AppState.hasMore = data.has_more;
            AppState.currentPage++;

            console.log(`Total albums: ${AppState.albums.length}, Has more: ${AppState.hasMore}`);
        } else {
            showError(data.error || '앨범을 로드할 수 없습니다');
        }
    } catch (error) {
        console.error('앨범 로드 실패:', error);
        showError('네트워크 오류가 발생했습니다');
    } finally {
        AppState.isLoading = false;
        hideLoadingIndicator();
    }
}

/**
 * 앨범 렌더링
 */
function renderAlbums(albums, append = false) {
    const container = document.querySelector('.album-grid') || document.querySelector('.album-list');
    if (!container) return;

    // 로딩 메시지 제거
    const loadingElement = container.querySelector('.loading');
    if (loadingElement) {
        loadingElement.remove();
    }

    if (albums.length === 0 && !append) {
        container.innerHTML = '<div class="no-data">등록된 앨범이 없습니다</div>';
        return;
    }

    const html = albums.map(album => createAlbumCardHTML(album)).join('');

    if (append) {
        container.insertAdjacentHTML('beforeend', html);
    } else {
        container.innerHTML = html;
    }

    // 이미지 lazy loading
    lazyLoadImages();
}

/**
 * 새로 로드된 앨범만 렌더링 (무한 스크롤용)
 */
function appendNewAlbums(newAlbums) {
    if (newAlbums.length === 0) return;

    const container = document.querySelector('.album-grid') || document.querySelector('.album-list');
    if (!container) return;

    const html = newAlbums.map(album => createAlbumCardHTML(album)).join('');
    container.insertAdjacentHTML('beforeend', html);

    // 이미지 lazy loading
    lazyLoadImages();
}

/**
 * 앨범 카드 HTML 생성
 */
function createAlbumCardHTML(album) {
    const albumId = encodeURIComponent(album.artist_ko + '|||' + album.album_ko);
    const coverUrl = album.album_cover_url || '';
    const title = album.album_ko || '';
    const artist = album.artist_ko || '';

    // 임시 데이터 (추후 DB에서 가져올 예정)
    const viewCount = Math.floor(Math.random() * 10000) + 100; // 임시: 100-10100
    const likeCount = Math.floor(Math.random() * 1000) + 10;   // 임시: 10-1010

    return `
        <a href="/album/${albumId}" class="album-card" data-album-id="${albumId}">
            <div class="album-thumbnail-container">
                <img src="${coverUrl}"
                     alt="${escapeHtml(title)}"
                     class="album-thumbnail"
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22%3E%3Crect fill=%22%23e9ecef%22 width=%22300%22 height=%22300%22/%3E%3C/svg%3E'">

                <div class="quick-actions">
                    <button class="quick-action-button" onclick="event.preventDefault(); event.stopPropagation(); openAlbum('${albumId}')">
                        상세보기
                    </button>
                    <button class="quick-action-button" onclick="event.preventDefault(); event.stopPropagation(); shareAlbum('${albumId}')">
                        공유
                    </button>
                </div>
            </div>

            <div class="album-info">
                <h3 class="album-title">${escapeHtml(title)}</h3>
                <div class="album-artist">${escapeHtml(artist)}</div>

                <div class="album-stats">
                    <span class="stat-item">
                        <span class="stat-icon view"></span>
                        <span class="stat-value">${formatNumber(viewCount)}</span>
                    </span>
                    <span class="stat-item">
                        <span class="stat-icon like"></span>
                        <span class="stat-value">${formatNumber(likeCount)}</span>
                    </span>
                </div>
            </div>
        </a>
    `;
}

/**
 * 숫자 포맷팅 (1000 -> 1K)
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * 앨범 열기
 */
function openAlbum(albumId) {
    window.location.href = `/album/${albumId}`;
}

/**
 * 앨범 공유
 */
function shareAlbum(albumId) {
    const url = `${window.location.origin}/album/${albumId}`;

    if (navigator.share) {
        navigator.share({
            title: '캔디드뮤직 링크',
            url: url
        }).catch(err => console.log('공유 취소:', err));
    } else {
        // 클립보드 복사
        navigator.clipboard.writeText(url).then(() => {
            alert('링크가 복사되었습니다!');
        }).catch(err => {
            console.error('복사 실패:', err);
        });
    }
}

/**
 * 이미지 Lazy Loading
 */
function lazyLoadImages() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[loading="lazy"]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

/**
 * 로딩 인디케이터
 */
function showLoadingIndicator() {
    const existing = document.querySelector('.loading-indicator');
    if (existing) return;

    const indicator = document.createElement('div');
    indicator.className = 'loading-indicator';
    indicator.innerHTML = '<div class="spinner"></div> 로딩 중...';
    document.body.appendChild(indicator);
}

function hideLoadingIndicator() {
    const indicator = document.querySelector('.loading-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * 에러 표시
 */
function showError(message) {
    const container = document.querySelector('.album-grid') || document.querySelector('.album-list');
    if (!container) return;

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.appendChild(errorDiv);

    setTimeout(() => errorDiv.remove(), 5000);
}

/**
 * HTML 이스케이프
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 정렬 변경
 */
function changeSort(sortType) {
    console.log('정렬 변경:', sortType);
    // TODO: 백엔드 API에 정렬 파라미터 추가 필요
}
