// ObsidianTime - Notifications Module

/**
 * Конфигурация уведомлений
 */
const NOTIFICATION_CONFIG = {
    timeout: 5000,
    maxNotifications: 5,
    animationDuration: 300,
    containerSelector: '#notifications-container'
};

/**
 * Типы уведомлений
 */
const NOTIFICATION_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error', 
    WARNING: 'warning',
    INFO: 'info'
};

/**
 * Иконки для типов уведомлений
 */
const NOTIFICATION_ICONS = {
    [NOTIFICATION_TYPES.SUCCESS]: '✓',
    [NOTIFICATION_TYPES.ERROR]: '✗',
    [NOTIFICATION_TYPES.WARNING]: '⚠',
    [NOTIFICATION_TYPES.INFO]: 'ℹ'
};

/**
 * Класс для управления уведомлениями
 */
class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.notificationId = 0;
    }

    /**
     * Инициализация менеджера уведомлений
     */
    init() {
        this.createContainer();
        this.autoHideExistingAlerts();
    }

    /**
     * Создание контейнера для уведомлений
     */
    createContainer() {
        let container = document.querySelector(NOTIFICATION_CONFIG.containerSelector);
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
        
        this.container = container;
    }

    /**
     * Показ уведомления
     */
    show(message, type = NOTIFICATION_TYPES.INFO, options = {}) {
        const config = {
            timeout: options.timeout ?? NOTIFICATION_CONFIG.timeout,
            persistent: options.persistent ?? false,
            html: options.html ?? false,
            action: options.action ?? null
        };

        // Проверяем лимит уведомлений
        this.enforceMaxNotifications();

        const notification = this.createNotificationElement(message, type, config);
        this.container.appendChild(notification);
        
        // Анимация появления
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Автоскрытие
        if (config.timeout > 0 && !config.persistent) {
            setTimeout(() => {
                this.hide(notification.dataset.id);
            }, config.timeout);
        }

        return notification.dataset.id;
    }

    /**
     * Создание элемента уведомления
     */
    createNotificationElement(message, type, config) {
        const id = `notification-${++this.notificationId}`;
        const notification = document.createElement('div');
        
        notification.className = `notification ${type}`;
        notification.dataset.id = id;
        notification.dataset.type = type;

        const content = config.html ? message : this.escapeHtml(message);
        const icon = NOTIFICATION_ICONS[type] || NOTIFICATION_ICONS[NOTIFICATION_TYPES.INFO];

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <span class="notification-icon">${icon}</span>
                    <div class="notification-message">${content}</div>
                    <button type="button" class="notification-close" data-id="${id}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                ${config.action ? `
                    <div class="notification-actions">
                        <button type="button" class="btn btn-sm btn-outline-primary notification-action" data-id="${id}">
                            ${config.action.text}
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        // Привязка событий
        this.bindNotificationEvents(notification, config);
        
        // Сохранение в карте
        this.notifications.set(id, {
            element: notification,
            type,
            config
        });

        return notification;
    }

    /**
     * Привязка событий уведомления
     */
    bindNotificationEvents(notification, config) {
        // Закрытие уведомления
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                this.hide(e.target.dataset.id);
            });
        }

        // Действие уведомления
        const actionBtn = notification.querySelector('.notification-action');
        if (actionBtn && config.action) {
            actionBtn.addEventListener('click', (e) => {
                const result = config.action.callback();
                if (result !== false) {
                    this.hide(e.target.dataset.id);
                }
            });
        }

        // Закрытие по клику
        notification.addEventListener('click', (e) => {
            if (e.target === notification) {
                this.hide(notification.dataset.id);
            }
        });
    }

    /**
     * Скрытие уведомления
     */
    hide(id) {
        const notificationData = this.notifications.get(id);
        if (!notificationData) return;

        const notification = notificationData.element;
        notification.classList.add('hide');

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications.delete(id);
        }, NOTIFICATION_CONFIG.animationDuration);
    }

    /**
     * Очистка всех уведомлений
     */
    clear() {
        this.notifications.forEach((_, id) => {
            this.hide(id);
        });
    }

    /**
     * Ограничение количества уведомлений
     */
    enforceMaxNotifications() {
        const notificationElements = this.container.querySelectorAll('.notification');
        
        if (notificationElements.length >= NOTIFICATION_CONFIG.maxNotifications) {
            const oldestNotification = notificationElements[0];
            if (oldestNotification) {
                this.hide(oldestNotification.dataset.id);
            }
        }
    }

    /**
     * Автоскрытие существующих алертов Bootstrap
     */
    autoHideExistingAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.style.transition = `opacity ${NOTIFICATION_CONFIG.animationDuration}ms`;
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        if (alert.parentNode) {
                            alert.parentNode.removeChild(alert);
                        }
                    }, NOTIFICATION_CONFIG.animationDuration);
                }
            }, NOTIFICATION_CONFIG.timeout);
        });
    }

    /**
     * Вспомогательные методы для разных типов уведомлений
     */
    success(message, options = {}) {
        return this.show(message, NOTIFICATION_TYPES.SUCCESS, options);
    }

    error(message, options = {}) {
        return this.show(message, NOTIFICATION_TYPES.ERROR, options);
    }

    warning(message, options = {}) {
        return this.show(message, NOTIFICATION_TYPES.WARNING, options);
    }

    info(message, options = {}) {
        return this.show(message, NOTIFICATION_TYPES.INFO, options);
    }

    /**
     * Экранирование HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
}

// Создание и инициализация менеджера уведомлений
const notificationManager = new NotificationManager();

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    notificationManager.init();
});

// Экспорт для использования в других модулях
window.NotificationManager = notificationManager;
window.NOTIFICATION_TYPES = NOTIFICATION_TYPES; 