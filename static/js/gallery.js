// ObsidianTime - Gallery Module

/**
 * Конфигурация галереи
 */
const GALLERY_CONFIG = {
    animationDuration: 300,
    debounceDelay: 500,
    maxImageSize: 5 * 1024 * 1024, // 5MB
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
};

/**
 * Селекторы элементов галереи
 */
const GALLERY_SELECTORS = {
    likeBtn: '.like-btn',
    dislikeBtn: '.dislike-btn',
    quoteLikeBtn: '.quote-like-btn',
    reactionBtn: '.like-btn, .dislike-btn',
    rating: '.rating',
    likeCount: '.like-count',
    dislikeCount: '.dislike-count',
    imageInput: 'input[type="file"][accept*="image"]',
    imagePreview: '.image-preview'
};

/**
 * Класс для управления галереей и реакциями
 */
class GalleryManager {
    constructor() {
        this.pendingRequests = new Set();
        this.imageCache = new Map();
    }

    /**
     * Инициализация менеджера галереи
     */
    init() {
        this.bindEvents();
        this.initImageHandling();
        this.initLazyLoading();
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Реакции на мемы
        document.addEventListener('click', (e) => {
            if (e.target.matches(GALLERY_SELECTORS.reactionBtn) || 
                e.target.closest(GALLERY_SELECTORS.reactionBtn)) {
                this.handleReaction(e);
            }
        });

        // Лайки цитат
        document.addEventListener('click', (e) => {
            if (e.target.matches(GALLERY_SELECTORS.quoteLikeBtn) || 
                e.target.closest(GALLERY_SELECTORS.quoteLikeBtn)) {
                this.handleQuoteLike(e);
            }
        });

        // Обработка загрузки изображений
        document.addEventListener('change', (e) => {
            if (e.target.matches(GALLERY_SELECTORS.imageInput)) {
                this.handleImageUpload(e);
            }
        });
    }

    /**
     * Обработка реакций на мемы
     */
    async handleReaction(event) {
        event.preventDefault();
        
        const button = event.target.closest(GALLERY_SELECTORS.reactionBtn);
        if (!button) return;

        const memeId = button.dataset.memeId;
        const url = button.dataset.url;
        const isLike = button.classList.contains('like-btn');

        if (!url || !memeId) {
            console.warn('Missing URL or meme ID for reaction');
            return;
        }

        // Предотвращаем множественные запросы
        const requestKey = `${memeId}-${isLike ? 'like' : 'dislike'}`;
        if (this.pendingRequests.has(requestKey)) return;

        try {
            this.pendingRequests.add(requestKey);
            // Показываем спиннер только на время запроса
            this.setButtonLoading(button, true);

            const response = await this.makeApiRequest(url, 'POST');
            
            if (response.ok) {
                const data = await response.json();
                // Сначала восстанавливаем содержимое кнопки
                this.setButtonLoading(button, false);
                // Затем обновляем счетчики
                this.updateReactionButtons(memeId, data, isLike);
                
                // Показываем уведомление о действии
                this.showReactionFeedback(isLike, data);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Ошибка при обработке реакции:', error);
            window.NotificationManager?.error('Ошибка при обработке реакции');
            // Восстанавливаем кнопку в случае ошибки
            this.setButtonLoading(button, false);
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }

    /**
     * Обновление кнопок реакций
     */
    updateReactionButtons(memeId, data, wasLike) {
        const likeBtn = document.querySelector(`${GALLERY_SELECTORS.likeBtn}[data-meme-id="${memeId}"]`);
        const dislikeBtn = document.querySelector(`${GALLERY_SELECTORS.dislikeBtn}[data-meme-id="${memeId}"]`);
        const rating = document.querySelector(`${GALLERY_SELECTORS.rating}[data-meme-id="${memeId}"]`);

        if (likeBtn) {
            likeBtn.classList.toggle('liked', data.liked);
            const likeCount = likeBtn.querySelector(GALLERY_SELECTORS.likeCount);
            if (likeCount) {
                this.animateCounterChange(likeCount, data.likes_count);
            }
        }

        if (dislikeBtn) {
            dislikeBtn.classList.toggle('disliked', data.disliked);
            const dislikeCount = dislikeBtn.querySelector(GALLERY_SELECTORS.dislikeCount);
            if (dislikeCount) {
                this.animateCounterChange(dislikeCount, data.dislikes_count);
            }
        }

        if (rating) {
            this.animateCounterChange(rating, data.rating);
        }
    }

    /**
     * Обработка лайков цитат
     */
    async handleQuoteLike(event) {
        event.preventDefault();
        
        const button = event.target.closest(GALLERY_SELECTORS.quoteLikeBtn);
        if (!button) return;

        const url = button.dataset.url;
        if (!url) {
            console.warn('Missing URL for quote like');
            return;
        }

        // Предотвращаем множественные запросы
        const requestKey = `quote-${url}`;
        if (this.pendingRequests.has(requestKey)) return;

        try {
            this.pendingRequests.add(requestKey);
            // Показываем спиннер только на время запроса
            this.setButtonLoading(button, true);

            const response = await this.makeApiRequest(url, 'POST');
            
            if (response.ok) {
                const data = await response.json();
                // Сначала восстанавливаем содержимое кнопки
                this.setButtonLoading(button, false);
                // Затем обновляем счетчики
                this.updateQuoteLikeButton(button, data);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Ошибка при обработке лайка цитаты:', error);
            window.NotificationManager?.error('Ошибка при обработке лайка');
            // Восстанавливаем кнопку в случае ошибки
            this.setButtonLoading(button, false);
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }

    /**
     * Обновление кнопки лайка цитаты
     */
    updateQuoteLikeButton(button, data) {
        button.classList.toggle('liked', data.liked);
        
        const likeCount = button.querySelector(GALLERY_SELECTORS.likeCount);
        if (likeCount) {
            this.animateCounterChange(likeCount, data.likes_count);
        }

        const icon = button.querySelector('i');
        if (icon) {
            if (data.liked) {
                icon.classList.remove('far');
                icon.classList.add('fas');
            } else {
                icon.classList.remove('fas');
                icon.classList.add('far');
            }
        }
    }

    /**
     * Обработка загрузки изображений
     */
    handleImageUpload(event) {
        const input = event.target;
        const file = input.files[0];

        if (!file) {
            this.clearImagePreview(input);
            return;
        }

        // Валидация файла
        const validation = this.validateImageFile(file);
        if (!validation.valid) {
            window.NotificationManager?.error(validation.message);
            input.value = '';
            return;
        }

        this.createImagePreview(input, file);
    }

    /**
     * Валидация загружаемого изображения
     */
    validateImageFile(file) {
        if (!GALLERY_CONFIG.allowedTypes.includes(file.type)) {
            return {
                valid: false,
                message: 'Разрешены только изображения форматов: JPEG, PNG, GIF, WebP'
            };
        }

        if (file.size > GALLERY_CONFIG.maxImageSize) {
            return {
                valid: false,
                message: `Размер файла не должен превышать ${GALLERY_CONFIG.maxImageSize / (1024 * 1024)}MB`
            };
        }

        return { valid: true };
    }

    /**
     * Создание превью изображения
     */
    createImagePreview(input, file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            let preview = input.parentNode.querySelector(GALLERY_SELECTORS.imagePreview);
            
            if (!preview) {
                preview = document.createElement('div');
                preview.className = 'image-preview mt-2';
                input.parentNode.appendChild(preview);
            }

            preview.innerHTML = `
                <div class="preview-container">
                    <img src="${e.target.result}" class="preview-image img-thumbnail" alt="Превью изображения">
                    <div class="preview-info">
                        <small class="text-muted">
                            ${file.name} (${this.formatFileSize(file.size)})
                        </small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger preview-remove">
                        <i class="fas fa-times"></i> Удалить
                    </button>
                </div>
            `;

            // Привязка события удаления
            const removeBtn = preview.querySelector('.preview-remove');
            removeBtn.addEventListener('click', () => {
                input.value = '';
                this.clearImagePreview(input);
            });

            // Анимация появления
            preview.style.opacity = '0';
            requestAnimationFrame(() => {
                preview.style.transition = `opacity ${GALLERY_CONFIG.animationDuration}ms`;
                preview.style.opacity = '1';
            });
        };

        reader.onerror = () => {
            window.NotificationManager?.error('Ошибка при чтении файла');
        };

        reader.readAsDataURL(file);
    }

    /**
     * Очистка превью изображения
     */
    clearImagePreview(input) {
        const preview = input.parentNode.querySelector(GALLERY_SELECTORS.imagePreview);
        if (preview) {
            preview.style.transition = `opacity ${GALLERY_CONFIG.animationDuration}ms`;
            preview.style.opacity = '0';
            setTimeout(() => {
                if (preview.parentNode) {
                    preview.parentNode.removeChild(preview);
                }
            }, GALLERY_CONFIG.animationDuration);
        }
    }

    /**
     * Инициализация ленивой загрузки изображений
     */
    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        imageObserver.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px'
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // Fallback для старых браузеров
            document.querySelectorAll('img[data-src]').forEach(img => {
                this.loadImage(img);
            });
        }
    }

    /**
     * Загрузка изображения
     */
    loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        // Проверяем кеш
        if (this.imageCache.has(src)) {
            img.src = src;
            img.classList.remove('lazy');
            return;
        }

        // Создаем новое изображение для предзагрузки
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
            this.imageCache.set(src, true);
        };
        tempImg.onerror = () => {
            img.classList.add('error');
            console.warn(`Failed to load image: ${src}`);
        };
        tempImg.src = src;
    }

    /**
     * Инициализация обработки изображений
     */
    initImageHandling() {
        // Обработка ошибок загрузки изображений
        document.addEventListener('error', (e) => {
            if (e.target.tagName === 'IMG') {
                this.handleImageError(e.target);
            }
        }, true);
    }

    /**
     * Обработка ошибок загрузки изображений
     */
    handleImageError(img) {
        img.classList.add('error');
        
        // Добавляем placeholder
        if (!img.dataset.errorHandled) {
            img.dataset.errorHandled = 'true';
            img.alt = 'Изображение не загружено';
            
            // Можно добавить placeholder изображение
            const placeholder = '/static/images/placeholder.svg';
            if (img.src !== placeholder) {
                img.src = placeholder;
            }
        }
    }

    /**
     * Утилиты
     */
    
    /**
     * Анимация изменения счетчика
     */
    animateCounterChange(element, newValue) {
        element.style.transform = 'scale(1.2)';
        element.style.transition = `transform ${GALLERY_CONFIG.animationDuration}ms`;
        
        setTimeout(() => {
            element.textContent = newValue;
            element.style.transform = 'scale(1)';
        }, GALLERY_CONFIG.animationDuration / 2);
    }

    /**
     * Установка состояния загрузки кнопки
     */
    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.dataset.originalContent = button.innerHTML;
            button.innerHTML = '<span class="spinner"></span>';
        } else {
            button.disabled = false;
            // Восстанавливаем оригинальное содержимое
            if (button.dataset.originalContent) {
                button.innerHTML = button.dataset.originalContent;
                delete button.dataset.originalContent;
            }
        }
    }

    /**
     * Показ обратной связи по реакции
     */
    showReactionFeedback(isLike, data) {
        const action = isLike ? 'лайк' : 'дизлайк';
        const message = data.liked || data.disliked ? 
            `Ваш ${action} учтен!` : 
            `${action.charAt(0).toUpperCase() + action.slice(1)} отменен`;
        
        // Показываем кратковременное уведомление
        window.NotificationManager?.success(message, { timeout: 2000 });
    }

    /**
     * Форматирование размера файла
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Выполнение API запроса
     */
    async makeApiRequest(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCSRFToken()
            }
        };

        if (data) {
            if (data instanceof FormData) {
                options.body = data;
            } else {
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(data);
            }
        }

        return fetch(url, options);
    }

    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
        // Сначала пытаемся получить из meta тега
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken && metaToken.getAttribute('content')) {
            return metaToken.getAttribute('content');
        }
        
        // Если нет в meta теге, ищем в cookies
        const name = 'csrftoken';
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
}

// Создание и инициализация менеджера галереи
const galleryManager = new GalleryManager();

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    galleryManager.init();
});

// Экспорт для использования в других модулях
window.GalleryManager = galleryManager; 