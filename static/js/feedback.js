// ObsidianTime - Feedback Management Module

/**
 * Конфигурация управления обращениями
 */
const FEEDBACK_CONFIG = window.FEEDBACK_CONFIG || {
    statusChangeDebounce: 300,
    commentSubmitDelay: 500,
    autoRefreshInterval: 30000, // 30 секунд
    maxCommentLength: 1000
};

/**
 * Селекторы для обратной связи
 */
const FEEDBACK_SELECTORS = window.FEEDBACK_SELECTORS || {
    statusChange: '[data-status-change]',
    commentForm: '#commentForm form, form[method="post"]',
    commentInput: '#commentForm textarea, textarea[name="comment"]',
    feedbackList: '.feedback-list',
    feedbackItem: '.feedback-item',
    commentItem: '.comment',
    statusBadge: '.status-badge',
    commentCounter: '.comment-counter',
    quickActions: '.quick-actions button',
    filterForm: '.filter-form',
    searchInput: '.search-input'
};

/**
 * Класс для управления обратной связью
 */
class FeedbackManager {
    constructor() {
        this.currentFeedbackId = null;
        this.statusChangeTimeouts = new Map();
        this.autoRefreshTimer = null;
        this.searchTimeout = null;
        this.isInitialized = false;
    }

    /**
     * Инициализация менеджера обратной связи
     */
    init() {
        if (this.isInitialized) {
            return;
        }

        console.log('Инициализация FeedbackManager...');
        
        this.bindEvents();
        this.initExistingElements();
        this.startAutoRefresh();
        
        this.isInitialized = true;
        console.log('FeedbackManager инициализирован');
        
        // Проверяем наличие элементов на странице
        this.debugPageElements();
    }

    /**
     * Отладочная информация о элементах на странице
     */
    debugPageElements() {
        console.log('=== Отладка элементов страницы ===');
        
        const statusButtons = document.querySelectorAll('[data-status-change]');
        console.log('Кнопки изменения статуса:', statusButtons.length);
        
        const statusBadges = document.querySelectorAll('.status-badge');
        console.log('Бейджи статуса:', statusBadges.length);
        
        const commentForm = document.querySelector('#commentForm form');
        console.log('Форма комментария:', commentForm ? 'найдена' : 'не найдена');
        
        const commentsList = document.querySelector('.comments-list');
        console.log('Список комментариев:', commentsList ? 'найден' : 'не найден');
        
        console.log('=== Конец отладки ===');
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        console.log('Привязка событий...');
        
        // Изменение статуса
        document.addEventListener('click', (e) => {
            if (e.target.matches(FEEDBACK_SELECTORS.statusChange)) {
                console.log('Найдена кнопка изменения статуса:', e.target);
                this.handleStatusChange(e);
            }
        });

        // Быстрые действия
        document.addEventListener('click', (e) => {
            if (e.target.matches(FEEDBACK_SELECTORS.quickActions)) {
                console.log('Найдена кнопка быстрого действия:', e.target);
                this.handleQuickAction(e);
            }
        });

        // Отправка комментариев
        document.addEventListener('submit', (e) => {
            console.log('Событие submit:', e.target);
            if (e.target.matches(FEEDBACK_SELECTORS.commentForm)) {
                console.log('Найдена форма комментария:', e.target);
                this.handleCommentSubmit(e);
            }
        });

        // Фильтрация
        document.addEventListener('submit', (e) => {
            if (e.target.matches(FEEDBACK_SELECTORS.filterForm)) {
                this.handleFilterSubmit(e);
            }
        });

        // Поиск
        document.addEventListener('input', (e) => {
            if (e.target.matches(FEEDBACK_SELECTORS.searchInput)) {
                this.handleSearch(e);
            }
        });

        // Счетчик символов для комментариев
        document.addEventListener('input', (e) => {
            if (e.target.matches(FEEDBACK_SELECTORS.commentInput)) {
                this.updateCommentCounter(e.target);
            }
        });
        
        console.log('События привязаны');
    }

    /**
     * Обработка изменения статуса
     */
    async handleStatusChange(event) {
        event.preventDefault();
        
        const button = event.target;
        const feedbackId = button.dataset.feedbackId;
        const newStatus = button.dataset.status;
        
        console.log('Обработка изменения статуса:', { feedbackId, newStatus });
        
        if (!feedbackId || !newStatus) {
            console.error('Отсутствуют данные для изменения статуса');
            return;
        }

        // Подтверждение действия
        const confirmMessage = `Изменить статус обращения на "${this.getStatusDisplayName(newStatus)}"?`;
        if (!confirm(confirmMessage)) {
            return;
        }

        // Показываем индикатор загрузки
        this.setButtonLoading(button, true);

        try {
            const response = await this.changeFeedbackStatus(feedbackId, newStatus);
            
            if (response.success) {
                // Обновляем UI
                this.updateStatusBadge(feedbackId, newStatus);
                this.updateFeedbackRow(feedbackId, newStatus);
                
                // Показываем уведомление
                window.NotificationManager?.success('Статус успешно изменен');
                
                // Обновляем статистику если на странице админки
                this.updateStatistics();
                
                // Обновляем страницу через 1 секунду, чтобы показать автоматический комментарий
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                window.NotificationManager?.error(response.message || 'Ошибка изменения статуса');
            }
        } catch (error) {
            console.error('Ошибка изменения статуса:', error);
            window.NotificationManager?.error('Ошибка при изменении статуса');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    /**
     * AJAX запрос для изменения статуса
     */
    async changeFeedbackStatus(feedbackId, newStatus) {
        const url = `/management/feedback/${feedbackId}/change-status/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                status: newStatus
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Обработка быстрых действий
     */
    async handleQuickAction(event) {
        event.preventDefault();
        
        const button = event.target;
        const action = button.dataset.action;
        const feedbackId = button.dataset.feedbackId;
        
        if (!action || !feedbackId) {
            return;
        }

        // Показываем индикатор загрузки
        this.setButtonLoading(button, true);

        try {
            let newStatus;
            switch (action) {
                case 'in_progress':
                    newStatus = 'in_progress';
                    break;
                case 'resolved':
                    newStatus = 'resolved';
                    break;
                case 'closed':
                    newStatus = 'closed';
                    break;
                default:
                    throw new Error('Неизвестное действие');
            }

            const response = await this.changeFeedbackStatus(feedbackId, newStatus);
            
            if (response.success) {
                // Обновляем UI
                this.updateStatusBadge(feedbackId, newStatus);
                this.updateFeedbackRow(feedbackId, newStatus);
                
                // Показываем уведомление
                window.NotificationManager?.success('Статус успешно изменен');
                
                // Обновляем статистику
                this.updateStatistics();
            } else {
                window.NotificationManager?.error(response.message || 'Ошибка изменения статуса');
            }
        } catch (error) {
            console.error('Ошибка быстрого действия:', error);
            window.NotificationManager?.error('Ошибка при выполнении действия');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    /**
     * Обработка отправки комментария
     */
    async handleCommentSubmit(event) {
        event.preventDefault();
        
        console.log('Обработка отправки комментария');
        
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const commentInput = form.querySelector('textarea[name="comment"]');
        
        console.log('Форма:', form);
        console.log('Кнопка отправки:', submitBtn);
        console.log('Поле комментария:', commentInput);
        console.log('Значение комментария:', commentInput?.value);
        
        if (!commentInput || !commentInput.value.trim()) {
            window.NotificationManager?.error('Введите текст комментария');
            return;
        }

        // Показываем индикатор загрузки
        this.setButtonLoading(submitBtn, true);

        try {
            const formData = new FormData(form);
            console.log('Отправка формы на:', form.action);
            
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            console.log('Ответ сервера:', response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();
                console.log('Данные ответа:', data);
                
                if (data.success) {
                    // Очищаем форму
                    form.reset();
                    
                    // Добавляем новый комментарий в список
                    this.addCommentToList(data.comment);
                    
                    // Обновляем счетчик комментариев
                    this.updateCommentCounter();
                    
                    // Показываем уведомление
                    window.NotificationManager?.success('Комментарий добавлен');
                } else {
                    window.NotificationManager?.error(data.message || 'Ошибка добавления комментария');
                }
            } else {
                const errorText = await response.text();
                console.error('Ошибка HTTP:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
        } catch (error) {
            console.error('Ошибка отправки комментария:', error);
            window.NotificationManager?.error('Ошибка при отправке комментария');
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }

    /**
     * Обработка отправки фильтров
     */
    handleFilterSubmit(event) {
        // Фильтры отправляются обычной формой
        // Никаких дополнительных действий не требуется
        return true;
    }

    /**
     * Обработка поиска
     */
    handleSearch(event) {
        const input = event.target;
        const searchValue = input.value.trim();
        
        // Можно добавить debounce для поиска
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            // Автоматическая отправка формы поиска
            const form = input.closest('form');
            if (form) {
                form.submit();
            }
        }, 500);
    }

    /**
     * Добавление комментария в список
     */
    addCommentToList(commentData) {
        const commentsContainer = document.querySelector('.comments-list');
        if (!commentsContainer) {
            console.error('Контейнер комментариев не найден');
            return;
        }

        const commentHtml = this.createCommentHtml(commentData);
        commentsContainer.insertAdjacentHTML('beforeend', commentHtml);
        
        // Анимация появления
        const newComment = commentsContainer.lastElementChild;
        if (newComment) {
            newComment.style.opacity = '0';
            newComment.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                newComment.style.transition = 'all 0.3s ease';
                newComment.style.opacity = '1';
                newComment.style.transform = 'translateY(0)';
            }, 10);
        }
        
        // Обновляем счетчик комментариев в заголовке
        const commentsHeader = document.querySelector('.card-header h4');
        if (commentsHeader) {
            // Получаем текущий счетчик и увеличиваем на 1
            const currentText = commentsHeader.textContent;
            const match = currentText.match(/\((\d+)\)/);
            if (match) {
                const currentCount = parseInt(match[1]) + 1;
                commentsHeader.innerHTML = `<i class="fas fa-comments"></i> Комментарии (${currentCount})`;
            }
        }
        
        // Если есть пагинация, перезагружаем страницу для корректного отображения
        const pagination = document.querySelector('.pagination');
        if (pagination) {
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        }
        
        console.log('Комментарий добавлен в список');
    }

    /**
     * Создание HTML для комментария
     */
    createCommentHtml(commentData) {
        const isAdmin = commentData.is_admin_comment;
        const isInternal = commentData.is_internal;
        
        let bgClass = 'bg-light';
        if (isInternal) {
            bgClass = 'bg-warning bg-opacity-10';
        } else if (isAdmin) {
            bgClass = 'bg-info bg-opacity-10';
        }

        return `
            <div class="comment mb-3 p-3 border rounded ${bgClass}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="d-flex align-items-center">
                        <div class="me-2">
                            <i class="fas fa-${isAdmin ? 'user-shield text-primary' : 'user text-success'}"></i>
                        </div>
                        <div>
                            <strong>${commentData.author_name}</strong>
                            <span class="badge bg-${isAdmin ? 'primary' : 'success'} ms-2">
                                ${isAdmin ? 'Администратор' : 'Пользователь'}
                            </span>
                            ${isInternal ? '<span class="badge bg-warning text-dark ms-2"><i class="fas fa-eye-slash"></i> Внутренний</span>' : ''}
                        </div>
                    </div>
                    <small class="text-muted">${commentData.created_at}</small>
                </div>
                <div class="comment-text">
                    ${commentData.comment}
                </div>
            </div>
        `;
    }

    /**
     * Обновление бейджа статуса
     */
    updateStatusBadge(feedbackId, newStatus) {
        // Обновляем все бейджи статуса на странице
        const badges = document.querySelectorAll(`.status-badge[data-feedback-id="${feedbackId}"]`);
        const statusColor = this.getStatusColor(newStatus);
        const statusDisplay = this.getStatusDisplayName(newStatus);
        
        badges.forEach(badge => {
            badge.textContent = statusDisplay;
            // Обновляем классы в зависимости от цвета
            if (statusColor === 'info') {
                badge.className = `badge bg-info status-badge`;
            } else if (statusColor === 'warning') {
                badge.className = `badge bg-warning text-dark status-badge`;
            } else if (statusColor === 'success') {
                badge.className = `badge bg-success status-badge`;
            } else if (statusColor === 'secondary') {
                badge.className = `badge bg-secondary status-badge`;
            } else {
                badge.className = `badge bg-${statusColor} status-badge`;
            }
            badge.setAttribute('data-feedback-id', feedbackId);
        });
        
        console.log(`Обновлен статус для обращения ${feedbackId} на ${newStatus} (цвет: ${statusColor})`);
    }

    /**
     * Обновление строки в таблице
     */
    updateFeedbackRow(feedbackId, newStatus) {
        const row = document.querySelector(`tr[data-feedback-id="${feedbackId}"]`);
        if (row) {
            // Обновляем класс строки
            row.className = `table-${this.getStatusTableClass(newStatus)}`;
            
            // Обновляем бейдж статуса в таблице
            const statusCell = row.querySelector('.status-cell');
            if (statusCell) {
                statusCell.innerHTML = `
                    <span class="badge bg-${this.getStatusColor(newStatus)}">
                        ${this.getStatusDisplayName(newStatus)}
                    </span>
                `;
            }
        }
        
        // На детальной странице обновляем только бейджи статуса
        // (updateStatusBadge уже вызван выше)
    }

    /**
     * Обновление статистики
     */
    updateStatistics() {
        // Если на странице админки, обновляем статистику
        const statsContainer = document.querySelector('.statistics-container');
        if (statsContainer) {
            this.refreshStatistics();
        }
    }

    /**
     * Обновление счетчика комментариев
     */
    updateCommentCounter() {
        const input = document.querySelector(FEEDBACK_SELECTORS.commentInput);
        if (!input) return;

        const counter = input.parentNode.querySelector('.character-counter');
        if (counter) {
            const currentLength = input.value.length;
            const maxLength = FEEDBACK_CONFIG.maxCommentLength;
            
            counter.textContent = `${currentLength}/${maxLength}`;
            counter.className = `character-counter ${currentLength > maxLength ? 'text-danger' : 'text-muted'}`;
        }
    }

    /**
     * Утилиты
     */

    /**
     * Получение отображаемого имени статуса
     */
    getStatusDisplayName(status) {
        const statusNames = {
            'new': 'Новое',
            'in_progress': 'В обработке',
            'resolved': 'Решено',
            'closed': 'Закрыто'
        };
        return statusNames[status] || status;
    }

    /**
     * Получение цвета для статуса
     */
    getStatusColor(status) {
        const statusColors = {
            'new': 'info',
            'in_progress': 'warning',
            'resolved': 'success',
            'closed': 'secondary'
        };
        return statusColors[status] || 'secondary';
    }

    /**
     * Получение класса таблицы для статуса
     */
    getStatusTableClass(status) {
        const tableClasses = {
            'new': 'info',
            'in_progress': 'warning',
            'resolved': 'success',
            'closed': 'secondary'
        };
        return tableClasses[status] || '';
    }

    /**
     * Установка состояния загрузки для кнопки
     */
    setButtonLoading(button, isLoading) {
        if (!button) return;

        if (isLoading) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
        } else {
            button.disabled = false;
            // Восстанавливаем оригинальный текст
            const originalText = button.dataset.originalText;
            if (originalText) {
                button.innerHTML = originalText;
            }
        }
    }

    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
        // Сначала пробуем получить из meta тега
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            return csrfToken;
        }

        // Затем пробуем получить из cookie
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

        // Если не нашли в cookie, пробуем получить из формы
        if (!cookieValue) {
            const form = document.querySelector('form');
            if (form) {
                const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
                if (csrfInput) {
                    cookieValue = csrfInput.value;
                }
            }
        }

        return cookieValue;
    }

    /**
     * Инициализация существующих элементов
     */
    initExistingElements() {
        // Сохраняем оригинальный текст кнопок
        document.querySelectorAll('button[data-status-change], button[data-action]').forEach(button => {
            if (!button.dataset.originalText) {
                button.dataset.originalText = button.innerHTML;
            }
        });

        // Инициализируем счетчики комментариев
        document.querySelectorAll(FEEDBACK_SELECTORS.commentInput).forEach(input => {
            this.updateCommentCounter(input);
        });
    }

    /**
     * Автообновление
     */
    startAutoRefresh() {
        // Автообновление только на страницах с обращениями
        if (document.querySelector(FEEDBACK_SELECTORS.feedbackList)) {
            this.autoRefreshTimer = setInterval(() => {
                this.refreshFeedbackList();
            }, FEEDBACK_CONFIG.autoRefreshInterval);
        }
    }

    /**
     * Обновление списка обращений
     */
    async refreshFeedbackList() {
        // Реализация автообновления списка
        // Можно добавить позже при необходимости
    }

    /**
     * Обновление статистики
     */
    async refreshStatistics() {
        // Реализация обновления статистики
        // Можно добавить позже при необходимости
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    if (!window.FeedbackManager) {
        window.FeedbackManager = new FeedbackManager();
        window.FeedbackManager.init();
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackManager;
} 