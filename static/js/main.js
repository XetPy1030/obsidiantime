// ObsidianTime Main JavaScript - Refactored
'use strict';

/**
 * Главный объект приложения ObsidianTime
 */
const ObsidianTime = {
    // Конфигурация
    config: {
        scrollOffset: 80,
        alertTimeout: 5000,
        searchDebounceDelay: 500,
        chatRefreshInterval: 3000
    },

    // Инициализация приложения
    init() {
        this.setupCSRF();
        this.initComponents();
        this.bindEvents();
        this.initFeatures();
        console.log('ObsidianTime - Ready to rock! 🚀');
    },

    // Настройка CSRF токена
    setupCSRF() {
        const csrftoken = Utils.getCookie('csrftoken');
        $.ajaxSetup({
            beforeSend: (xhr, settings) => {
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    },

    // Инициализация компонентов
    initComponents() {
        Notifications.init();
        Gallery.init();
        Chat.init();
        Navigation.init();
        Forms.init();
    },

    // Привязка основных событий
    bindEvents() {
        Navigation.bindEvents();
        Forms.bindEvents();
        Gallery.bindEvents();
        UI.bindEvents();
    },

    // Инициализация дополнительных функций
    initFeatures() {
        UI.initTooltips();
        UI.initLazyLoading();
        UI.initDarkMode();
        UI.initScrollAnimations();
    }
};

/**
 * Утилиты общего назначения
 */
const Utils = {
    // Получение cookie
    getCookie(name) {
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
    },

    // Debounce функция
    debounce(func, delay) {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    // Throttle функция
    throttle(func, delay) {
        let inThrottle;
        return (...args) => {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, delay);
            }
        };
    },

    // Проверка на мобильное устройство
    isMobile() {
        return window.innerWidth <= 768;
    },

    // Форматирование чисел
    formatNumber(num) {
        return new Intl.NumberFormat('ru-RU').format(num);
    }
};

/**
 * Система уведомлений
 */
const Notifications = {
    container: null,

    init() {
        this.container = $('#notifications-container');
        this.autoHideAlerts();
    },

    // Показ уведомления
    show(message, type = 'info', timeout = ObsidianTime.config.alertTimeout) {
        const notification = $(`
            <div class="notification ${type}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>
                            ${this.getIcon(type)} ${message}
                        </strong>
                    </div>
                    <button type="button" class="btn-close" onclick="$(this).parent().parent().remove()"></button>
                </div>
            </div>
        `);

        this.container.append(notification);

        if (timeout > 0) {
            setTimeout(() => {
                notification.fadeOut(() => notification.remove());
            }, timeout);
        }

        return notification;
    },

    // Получение иконки по типу
    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    },

    // Автоскрытие алертов
    autoHideAlerts() {
        $('.alert, .notification').each(function() {
            const element = $(this);
            setTimeout(() => {
                element.fadeOut(() => element.remove());
            }, ObsidianTime.config.alertTimeout);
        });
    }
};

/**
 * Навигация и плавная прокрутка
 */
const Navigation = {
    init() {
        this.setupSmoothScrolling();
    },

    bindEvents() {
        // Плавная прокрутка к якорям
        $('a[href^="#"]').on('click', this.handleAnchorClick.bind(this));
    },

    setupSmoothScrolling() {
        $('html').css('scroll-behavior', 'smooth');
    },

    handleAnchorClick(event) {
        const target = $(event.currentTarget.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - ObsidianTime.config.scrollOffset
            }, 1000);
        }
    }
};

/**
 * Обработка форм
 */
const Forms = {
    init() {
        this.setupSearch();
    },

    bindEvents() {
        $(document).on('change', 'input[type="file"]', this.handleFileChange);
        $(document).on('input', '.search-input', this.handleSearch);
        $(document).on('click', '.confirm-action', this.handleConfirmAction);
    },

    // Предпросмотр изображений
    handleFileChange(e) {
        const file = e.target.files[0];
        const $input = $(e.target);
        let $preview = $input.siblings('.image-preview');

        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                if ($preview.length === 0) {
                    $preview = $(`
                        <div class="image-preview mt-2">
                            <img src="${e.target.result}" class="img-thumbnail" style="max-height: 200px;">
                        </div>
                    `);
                    $input.after($preview);
                } else {
                    $preview.html(`<img src="${e.target.result}" class="img-thumbnail" style="max-height: 200px;">`);
                }
            };
            reader.readAsDataURL(file);
        } else {
            $preview.remove();
        }
    },

    // Поиск с debounce
    setupSearch() {
        this.debouncedSearch = Utils.debounce((form) => {
            form.submit();
        }, ObsidianTime.config.searchDebounceDelay);
    },

    handleSearch(e) {
        const $input = $(e.target);
        const query = $input.val();
        const $form = $input.closest('form');

        if (query.length >= 3 || query.length === 0) {
            Forms.debouncedSearch($form[0]);
        }
    },

    // Подтверждение действий
    handleConfirmAction(e) {
        const $element = $(e.target);
        const message = $element.data('confirm') || 'Вы уверены?';
        if (!confirm(message)) {
            e.preventDefault();
        }
    }
};

/**
 * Функциональность галереи и реакций
 */
const Gallery = {
    init() {
        this.bindReactionEvents();
    },

    bindEvents() {
        $(document).on('click', '.like-btn, .dislike-btn', this.handleReaction);
        $(document).on('click', '.quote-like-btn', this.handleQuoteLike);
    },

    bindReactionEvents() {
        this.bindEvents();
    },

    // Обработка реакций на мемы
    handleReaction(e) {
        e.preventDefault();
        const $btn = $(e.currentTarget);
        const memeId = $btn.data('meme-id');
        const url = $btn.data('url');
        const isLike = $btn.hasClass('like-btn');

        if (!url) return;

        // Показываем индикатор загрузки
        const originalContent = $btn.html();
        $btn.html('<span class="spinner"></span>');

        $.post(url)
            .done((data) => {
                Gallery.updateReactionButtons(memeId, data, isLike);
            })
            .fail(() => {
                Notifications.show('Ошибка при обработке реакции', 'error');
            })
            .always(() => {
                $btn.html(originalContent);
            });
    },

    // Обновление кнопок реакций
    updateReactionButtons(memeId, data, wasLike) {
        const $likeBtn = $(`.like-btn[data-meme-id="${memeId}"]`);
        const $dislikeBtn = $(`.dislike-btn[data-meme-id="${memeId}"]`);
        const $rating = $(`.rating[data-meme-id="${memeId}"]`);

        // Обновляем состояние кнопок
        $likeBtn.toggleClass('liked', data.liked);
        $dislikeBtn.toggleClass('disliked', data.disliked);

        // Обновляем счетчики
        $likeBtn.find('.like-count').text(data.likes_count);
        $dislikeBtn.find('.dislike-count').text(data.dislikes_count);

        // Обновляем рейтинг
        if ($rating.length) {
            $rating.text(data.rating);
        }
    },

    // Обработка лайков цитат
    handleQuoteLike(e) {
        e.preventDefault();
        const $btn = $(e.currentTarget);
        const url = $btn.data('url');

        if (!url) return;

        $.post(url)
            .done((data) => {
                $btn.toggleClass('liked', data.liked);
                $btn.find('.like-count').text(data.likes_count);

                const $icon = $btn.find('i');
                if (data.liked) {
                    $icon.removeClass('far').addClass('fas');
                } else {
                    $icon.removeClass('fas').addClass('far');
                }
            })
            .fail(() => {
                Notifications.show('Ошибка при обработке лайка', 'error');
            });
    }
};

/**
 * Чат функциональность
 */
const Chat = {
    lastMessageId: 0,
    refreshInterval: null,

    init() {
        if (window.location.pathname.includes('/chat/')) {
            this.setupChat();
        }
    },

    setupChat() {
        this.startAutoRefresh();
        this.bindPollEvents();
    },

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.refreshMessages();
        }, ObsidianTime.config.chatRefreshInterval);
    },

    refreshMessages() {
        $.get('/chat/api/messages/', { last_id: this.lastMessageId })
            .done((data) => {
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(message => {
                        this.addMessage(message);
                    });
                    this.lastMessageId = data.last_id;
                    this.scrollToBottom();
                }
            })
            .fail(() => {
                console.warn('Ошибка обновления чата');
            });
    },

    addMessage(message) {
        // Проверяем, нет ли уже такого сообщения
        if ($(`[data-message-id="${message.id}"]`).length > 0) return;

        const $container = $('.chat-messages');
        const messageHtml = this.createMessageHtml(message);
        $container.append(messageHtml);
    },

    createMessageHtml(message) {
        // Упрощенная версия создания HTML сообщения
        return `
            <div class="message-item" data-message-id="${message.id}">
                <div class="d-flex justify-content-between">
                    <strong class="text-primary">${message.author}</strong>
                    <small class="text-muted">${message.created_at}</small>
                </div>
                <div class="message-content mt-2">${message.content}</div>
            </div>
        `;
    },

    scrollToBottom() {
        const $container = $('.chat-messages');
        if ($container.length > 0) {
            $container.scrollTop($container[0].scrollHeight);
        }
    },

    bindPollEvents() {
        $(document).on('click', '.poll-option', this.handlePollVote);
    },

    handlePollVote(e) {
        e.preventDefault();
        const $option = $(e.currentTarget);
        const optionId = $option.data('option-id');
        const pollId = $option.data('poll-id');

        if (!optionId || !pollId) return;

        $.post(`/chat/poll/${pollId}/vote/${optionId}/`)
            .done((data) => {
                Chat.updatePollDisplay($option.closest('.poll-container'), data);
            })
            .fail(() => {
                Notifications.show('Ошибка голосования', 'error');
            });
    },

    updatePollDisplay(container, data) {
        // Обновляем отображение голосования
        container.find('.poll-total-votes').text(`${data.total_votes} голосов`);

        data.options.forEach(option => {
            const $optionElement = container.find(`[data-option-id="${option.id}"]`);
            $optionElement.find('.poll-votes').text(option.vote_count);
            $optionElement.find('.poll-progress-bar').css('width', `${option.vote_percentage}%`);
            $optionElement.toggleClass('voted', option.user_voted);
        });
    }
};

/**
 * UI компоненты и эффекты
 */
const UI = {
    bindEvents() {
        $(document).on('click', '.copy-to-clipboard', this.handleCopyToClipboard);
        $(document).on('click', '.dark-mode-toggle', this.toggleDarkMode);
        $(window).on('scroll', Utils.throttle(this.handleScroll.bind(this), 100));
    },

    // Инициализация тултипов
    initTooltips() {
        if (typeof bootstrap !== 'undefined') {
            $('[data-bs-toggle="tooltip"]').tooltip();
        }
    },

    // Ленивая загрузка изображений
    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    },

    // Темный режим
    initDarkMode() {
        if (localStorage.getItem('darkMode') === 'true') {
            $('body').addClass('dark-mode');
        }
    },

    toggleDarkMode() {
        $('body').toggleClass('dark-mode');
        localStorage.setItem('darkMode', $('body').hasClass('dark-mode'));
    },

    // Копирование в буфер обмена
    handleCopyToClipboard(e) {
        e.preventDefault();
        const $btn = $(e.currentTarget);
        const text = $btn.data('text') || $btn.text();

        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = $btn.text();
                $btn.text('Скопировано!');
                setTimeout(() => $btn.text(originalText), 2000);
            });
        }
    },

    // Анимации при прокрутке
    initScrollAnimations() {
        this.handleScroll();
    },

    handleScroll() {
        $('.animate-on-scroll').each(function() {
            const $element = $(this);
            const elementTop = $element.offset().top;
            const elementBottom = elementTop + $element.outerHeight();
            const viewportTop = $(window).scrollTop();
            const viewportBottom = viewportTop + $(window).height();

            if (elementBottom > viewportTop && elementTop < viewportBottom) {
                $element.addClass('animated');
            }
        });
    }
};

// Инициализация при загрузке DOM
$(document).ready(() => {
    ObsidianTime.init();
});

// Экспорт для возможного использования в других скриптах
window.ObsidianTime = ObsidianTime;
window.Utils = Utils;
window.Notifications = Notifications; 