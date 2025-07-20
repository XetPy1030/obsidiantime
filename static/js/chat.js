// ObsidianTime - Chat Module

/**
 * Namespace для модуля чата
 */
const ObsidianChat = (() => {
    'use strict';

    /**
     * Конфигурация по умолчанию
     */
    const DEFAULT_CONFIG = {
        refreshInterval: 3000,
        loadMoreBatchSize: 20,
        apiEndpoints: {
            messages: '/chat/api/messages/',
            sendMessage: '/chat/send-message/',
            createPoll: '/chat/create-poll/'
        },
        selectors: {
            chatMessages: '#chat-messages',
            loadMoreBtn: '#load-more-btn',
            loadingIndicator: '#loading-indicator',
            messageForm: '#message-form',
            pollForm: '#poll-form',
            messageItem: '.message-item',
            dateSeparator: '.date-separator'
        }
    };

    /**
     * Состояние модуля
     */
    let state = {
        initialized: false,
        config: null,
        chatManager: null
    };

    /**
     * Основной класс для управления чатом
     */
    class ChatManager {
        constructor(config) {
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.state = {
        lastMessageId: 0,
        isLoading: false,
        hasMoreMessages: true,
        currentPage: 1,
        refreshInterval: null,
        chatMessages: null
            };
            
            this.domElements = {};
            this.messageRenderer = new MessageRenderer(this.config);
            this.apiClient = new ChatApiClient(this.config);
        }

        /**
         * Инициализация чата
         */
    init() {
            if (!this.isOnChatPage()) return false;

            try {
                this.initializeDomElements();
                this.setupInitialState();
                this.bindEventListeners();
                this.startAutoRefresh();
                return true;
            } catch (error) {
                console.error('Ошибка инициализации чата:', error);
                return false;
            }
        }

        /**
         * Проверка, находимся ли мы на странице чата
         */
        isOnChatPage() {
            return window.location.pathname.includes('/chat/');
        }

        /**
         * Инициализация DOM элементов
         */
        initializeDomElements() {
            const { selectors } = this.config;
            
            this.domElements = {
                chatMessages: document.querySelector(selectors.chatMessages),
                loadMoreBtn: document.querySelector(selectors.loadMoreBtn),
                loadingIndicator: document.querySelector(selectors.loadingIndicator),
                messageForm: document.querySelector(selectors.messageForm),
                pollForm: document.querySelector(selectors.pollForm)
            };

            this.state.chatMessages = this.domElements.chatMessages;
            
            // Проверяем критически важные элементы
            if (!this.state.chatMessages) {
                throw new Error('Chat messages container not found');
            }
        }

        /**
         * Настройка начального состояния
         */
        setupInitialState() {
        this.updateLastMessageId();
        this.hideLoadingIndicator();
        this.scrollToBottom();
        this.setupScrollHandler();
        }

        /**
         * Привязка обработчиков событий
         */
        bindEventListeners() {
            this.bindFormSubmissions();
            this.bindLoadMoreButton();
        }

        /**
         * Привязка обработчиков форм
         */
        bindFormSubmissions() {
            const { messageForm, pollForm } = this.domElements;
            
            messageForm?.addEventListener('submit', (e) => {
                this.handleFormSubmission(e, 'message');
            });

            pollForm?.addEventListener('submit', (e) => {
                this.handleFormSubmission(e, 'poll');
            });
        }

        /**
         * Привязка кнопки загрузки старых сообщений
         */
        bindLoadMoreButton() {
            this.domElements.loadMoreBtn?.addEventListener('click', () => {
                this.loadOlderMessages();
            });
        }

        /**
         * Обработка отправки форм
         */
        async handleFormSubmission(event, formType) {
            event.preventDefault();
            const form = event.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            try {
                this.toggleSubmitButton(submitBtn, true);
                
                const success = await this.apiClient.submitForm(form, formType);
                
                if (success) {
                    form.reset();
                    window.NotificationManager?.success(
                        formType === 'message' ? 'Сообщение отправлено!' : 'Голосование создано!'
                    );
                }
            } catch (error) {
                console.error(`Ошибка отправки ${formType}:`, error);
                window.NotificationManager?.error(
                    `Ошибка ${formType === 'message' ? 'отправки сообщения' : 'создания голосования'}`
                );
            } finally {
                this.toggleSubmitButton(submitBtn, false);
            }
        }

        /**
         * Обновление ID последнего сообщения
         */
    updateLastMessageId() {
            const lastMessage = document.querySelector(`${this.config.selectors.messageItem}:last-child`);
        if (lastMessage) {
                this.state.lastMessageId = parseInt(lastMessage.dataset.messageId) || 0;
            }
        }

        /**
         * Скрытие индикатора загрузки
         */
    hideLoadingIndicator() {
            if (this.domElements.loadingIndicator) {
                this.domElements.loadingIndicator.style.display = 'none';
            }
        }

        /**
         * Настройка обработчика прокрутки
         */
    setupScrollHandler() {
        if (!this.state.chatMessages) return;

            this.state.chatMessages.addEventListener('scroll', this.throttle(() => {
                if (this.shouldLoadMoreMessages()) {
                this.loadOlderMessages();
            }
        }, 250));
        }

        /**
         * Проверка необходимости загрузки старых сообщений
         */
        shouldLoadMoreMessages() {
            return (
                this.state.chatMessages.scrollTop === 0 &&
                this.state.hasMoreMessages &&
                !this.state.isLoading
            );
        }

        /**
         * Начало автообновления
         */
    startAutoRefresh() {
        this.state.refreshInterval = setInterval(() => {
            this.refreshMessages();
        }, this.config.refreshInterval);
        }

        /**
         * Остановка автообновления
         */
    stopAutoRefresh() {
        if (this.state.refreshInterval) {
            clearInterval(this.state.refreshInterval);
            this.state.refreshInterval = null;
        }
        }

        /**
         * Обновление новых сообщений
         */
        async refreshMessages() {
            try {
                const data = await this.apiClient.getMessages({ last_id: this.state.lastMessageId });
                
            if (data.messages && data.messages.length > 0) {
                    this.processIncomingMessages(data.messages);
                    
                    // Проверяем, что last_id корректен
                    if (data.last_id !== undefined && data.last_id !== null) {
                this.state.lastMessageId = data.last_id;
                    } else {
                        console.warn('last_id is undefined in API response');
                        // Получаем максимальный ID из сообщений как fallback
                        const messageIds = data.messages
                            .filter(item => item.type === 'message')
                            .map(item => item.id);
                        if (messageIds.length > 0) {
                            this.state.lastMessageId = Math.max(...messageIds);
                        }
                    }
                    
                this.scrollToBottom();
                }
            } catch (error) {
                console.warn('Ошибка обновления чата:', error);
            }
        }

        /**
         * Загрузка старых сообщений
         */
        async loadOlderMessages() {
        if (this.state.isLoading || !this.state.hasMoreMessages) return;

        this.state.isLoading = true;
        this.updateLoadMoreButton('loading');

            try {
                const firstMessage = document.querySelector(`${this.config.selectors.messageItem}:first-child`);
        const beforeId = firstMessage ? firstMessage.dataset.messageId : null;

                const data = await this.apiClient.getMessages({
            page: this.state.currentPage + 1,
            before_id: beforeId
                });

            this.handleOlderMessagesResponse(data);
            } catch (error) {
                console.error('Ошибка загрузки старых сообщений:', error);
                window.NotificationManager?.error('Ошибка загрузки сообщений');
            } finally {
            this.state.isLoading = false;
            this.updateLoadMoreButton('normal');
            }
        }

        /**
         * Обработка ответа с старыми сообщениями
         */
    handleOlderMessagesResponse(data) {
        if (data.messages && data.messages.length > 0) {
            const scrollHeight = this.state.chatMessages.scrollHeight;
            
                // Добавляем элементы в обратном порядке
                data.messages.reverse().forEach(item => {
                    this.messageRenderer.prependMessage(item, this.state.chatMessages);
            });

            this.state.currentPage++;
            this.state.hasMoreMessages = data.has_more;

            // Сохраняем позицию прокрутки
            this.state.chatMessages.scrollTop = this.state.chatMessages.scrollHeight - scrollHeight;
        } else {
            this.state.hasMoreMessages = false;
        }
        }

        /**
         * Обработка входящих сообщений
         */
        processIncomingMessages(messages) {
            messages.forEach(item => {
                this.messageRenderer.appendMessage(item, this.state.chatMessages);
            });
        }

        /**
         * Переключение состояния кнопки отправки
         */
        toggleSubmitButton(button, isLoading, loadingText = 'Отправка...') {
            if (!button) return;

            if (isLoading) {
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.innerHTML = `<span class="spinner"></span> ${loadingText}`;
            } else {
                button.disabled = false;
                button.textContent = button.dataset.originalText || 'Отправить';
            }
        }

        /**
         * Обновление кнопки загрузки
         */
        updateLoadMoreButton(state) {
            const btn = this.domElements.loadMoreBtn;
            if (!btn) return;

            switch (state) {
                case 'loading':
                    btn.innerHTML = '<div class="spinner"></div> Загрузка...';
                    break;
                case 'normal':
                default:
                    btn.innerHTML = '<i class="fas fa-chevron-up"></i> Загрузить старые сообщения';
                    break;
            }
        }

        /**
         * Прокрутка к низу
         */
        scrollToBottom() {
            if (this.state.chatMessages) {
                this.state.chatMessages.scrollTop = this.state.chatMessages.scrollHeight;
            }
        }

        /**
         * Функция throttle для оптимизации производительности
         */
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }

        /**
         * Приостановка работы чата
         */
        pause() {
            this.stopAutoRefresh();
        }

        /**
         * Возобновление работы чата
         */
        resume() {
            if (this.isOnChatPage()) {
                this.startAutoRefresh();
            }
        }

        /**
         * Очистка ресурсов
         */
        cleanup() {
            this.stopAutoRefresh();
        }
    }

    /**
     * Класс для рендеринга сообщений
     */
    class MessageRenderer {
        constructor(config) {
            this.config = config;
        }

        /**
         * Добавление сообщения в конец
         */
        appendMessage(item, container) {
            if (item.type === 'date_separator') {
                this.appendDateSeparator(item, container);
            } else if (item.type === 'message') {
                this.appendMessageElement(item, container);
            }
        }

        /**
         * Добавление сообщения в начало
         */
        prependMessage(item, container) {
            if (item.type === 'date_separator') {
                this.prependDateSeparator(item, container);
            } else if (item.type === 'message') {
                this.prependMessageElement(item, container);
            }
        }

        /**
         * Добавление элемента сообщения в конец
         */
        appendMessageElement(message, container) {
        if (this.messageExists(message.id)) return;

        const messageElement = this.createMessageElement(message);
            container.appendChild(messageElement);
        messageElement.classList.add('fade-in');
        }

        /**
         * Добавление элемента сообщения в начало
         */
        prependMessageElement(message, container) {
        const messageElement = this.createMessageElement(message);
            container.insertBefore(messageElement, container.firstChild);
        }

        /**
         * Добавление разделителя даты в конец
         */
        appendDateSeparator(dateSeparator, container) {
            // Проверяем существование по дате и по читаемому тексту (для надежности)
            if (this.dateSeparatorExists(dateSeparator.date) || 
                this.dateSeparatorExistsByText(dateSeparator.date_readable)) {
                return;
            }

            const separatorElement = this.createDateSeparatorElement(dateSeparator);
            container.appendChild(separatorElement);
        }

        /**
         * Добавление разделителя даты в начало
         */
        prependDateSeparator(dateSeparator, container) {
            // Проверяем существование по дате и по читаемому тексту (для надежности)
            if (this.dateSeparatorExists(dateSeparator.date) || 
                this.dateSeparatorExistsByText(dateSeparator.date_readable)) {
                return;
            }

            const separatorElement = this.createDateSeparatorElement(dateSeparator);
            container.insertBefore(separatorElement, container.firstChild);
        }

        /**
         * Создание элемента сообщения
         */
    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = 'message-item';
        div.dataset.messageId = message.id;
        
        if (message.author === this.getCurrentUsername()) {
            div.classList.add('own');
        }

        div.innerHTML = this.createMessageHTML(message);
        return div;
        }

        /**
         * Создание элемента разделителя даты
         */
        createDateSeparatorElement(dateSeparator) {
            const div = document.createElement('div');
            div.className = 'date-separator';
            div.dataset.date = dateSeparator.date;
            
            div.innerHTML = `
                <div class="date-separator-line"></div>
                <div class="date-separator-text">${this.escapeHtml(dateSeparator.date_readable)}</div>
                <div class="date-separator-line"></div>
            `;
            
            return div;
        }

        /**
         * Создание HTML содержимого сообщения
         */
    createMessageHTML(message) {
        let html = `
            <div class="d-flex justify-content-between">
                <strong class="text-primary">${this.escapeHtml(message.author)}</strong>
                <small class="text-muted">${message.created_at}</small>
            </div>
            <div class="message-content mt-2">
        `;

        if (message.message_type === 'poll' && message.poll) {
            html += this.createPollHTML(message.poll);
        } else {
            html += this.escapeHtml(message.content).replace(/\n/g, '<br>');
        }

        html += '</div>';
        return html;
        }

        /**
         * Создание HTML для голосования
         */
    createPollHTML(poll) {
        let html = `
            <div class="poll-container">
                <h6><i class="fas fa-poll"></i> ${this.escapeHtml(poll.question)}</h6>
                <div class="poll-options">
        `;

        poll.options.forEach(option => {
            const votedClass = option.user_voted ? 'voted' : '';
            html += `
                <div class="poll-option ${votedClass}" 
                     data-option-id="${option.id}" 
                     data-poll-id="${poll.id}">
                    <div class="d-flex justify-content-between">
                        <span>${this.escapeHtml(option.text)}</span>
                        <span class="poll-votes">${option.vote_count}</span>
                    </div>
                    <div class="poll-progress">
                        <div class="poll-progress-bar" style="width: ${option.vote_percentage}%"></div>
                    </div>
                </div>
            `;
        });

        html += `
                </div>
                <div class="text-center mt-2">
                    <small class="text-muted poll-total-votes">${poll.total_votes} голосов</small>
                </div>
            </div>
        `;

        return html;
        }

        /**
         * Проверка существования сообщения
         */
        messageExists(messageId) {
            return document.querySelector(`[data-message-id="${messageId}"]`) !== null;
        }

        /**
         * Проверка существования разделителя даты
         */
        dateSeparatorExists(date) {
            return document.querySelector(`[data-date="${date}"]`) !== null;
        }

        /**
         * Проверка существования разделителя даты по тексту
         */
        dateSeparatorExistsByText(dateText) {
            const separators = document.querySelectorAll('.date-separator-text');
            for (let separator of separators) {
                if (separator.textContent.trim() === dateText) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Получение имени текущего пользователя
         */
        getCurrentUsername() {
            return window.chatConfig?.currentUser || '';
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

    /**
     * Класс для работы с API чата
     */
    class ChatApiClient {
        constructor(config) {
            this.config = config;
        }

        /**
         * Получение сообщений
         */
        async getMessages(params) {
            const url = new URL(this.config.apiEndpoints.messages, window.location.origin);
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null) {
                    url.searchParams.append(key, params[key]);
                }
            });

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        }

        /**
         * Отправка формы
         */
        async submitForm(form, formType) {
        const formData = new FormData(form);
        
            const response = await fetch(form.action, {
            method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Неизвестная ошибка');
            }

            return true;
        }
    }

    /**
     * Публичный API модуля
     */
    return {
        /**
         * Инициализация модуля чата
         */
        init(userConfig = {}) {
            if (state.initialized) {
                console.warn('Chat module already initialized');
                return state.chatManager;
            }

            try {
                // Объединяем конфигурацию
                const config = {
                    ...DEFAULT_CONFIG,
                    ...userConfig,
                    ...window.chatConfig // Данные из Django шаблона
                };

                state.config = config;
                state.chatManager = new ChatManager(config);
                
                const initialized = state.chatManager.init();
                if (initialized) {
                    state.initialized = true;
                    console.log('Chat module initialized successfully');
                }
                
                return state.chatManager;
            } catch (error) {
                console.error('Failed to initialize chat module:', error);
                return null;
            }
        },

        /**
         * Получение экземпляра менеджера чата
         */
        getInstance() {
            return state.chatManager;
        },

        /**
         * Проверка состояния инициализации
         */
        isInitialized() {
            return state.initialized;
        },

        /**
         * Приостановка работы
         */
        pause() {
            state.chatManager?.pause();
        },

        /**
         * Возобновление работы
         */
        resume() {
            state.chatManager?.resume();
        },

        /**
         * Очистка ресурсов
         */
    cleanup() {
            if (state.chatManager) {
                state.chatManager.cleanup();
                state.chatManager = null;
                state.initialized = false;
            }
        }
    };
})();

// Автоинициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    ObsidianChat.init();
});

// Очистка при выгрузке страницы
window.addEventListener('beforeunload', () => {
    ObsidianChat.cleanup();
});

// Экспорт в глобальную область для совместимости
window.ChatManager = ObsidianChat.getInstance();
window.ObsidianChat = ObsidianChat; 