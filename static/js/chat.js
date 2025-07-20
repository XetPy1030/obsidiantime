// ObsidianTime - Chat Enhanced JavaScript

/**
 * Расширенная функциональность чата
 */
const ChatEnhanced = {
    config: {
        refreshInterval: 3000,
        loadMoreBatchSize: 20
    },

    // Состояние чата
    state: {
        lastMessageId: 0,
        isLoading: false,
        hasMoreMessages: true,
        currentPage: 1,
        refreshInterval: null,
        chatMessages: null
    },

    // Инициализация расширенного чата
    init() {
        if (!window.location.pathname.includes('/chat/')) return;

        this.state.chatMessages = document.getElementById('chat-messages');
        this.initializeChat();
        this.setupEventListeners();
    },

    // Первоначальная настройка
    initializeChat() {
        this.updateLastMessageId();
        this.hideLoadingIndicator();
        this.scrollToBottom();
        this.startAutoRefresh();
        this.setupScrollHandler();
    },

    // Настройка обработчиков событий
    setupEventListeners() {
        // Обработчики форм
        this.bindFormSubmission();
        
        // Кнопка загрузки старых сообщений
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => this.loadOlderMessages());
        }
    },

    // Обновление ID последнего сообщения
    updateLastMessageId() {
        const lastMessage = document.querySelector('.message-item:last-child');
        if (lastMessage) {
            this.state.lastMessageId = lastMessage.dataset.messageId || 0;
        }
    },

    // Скрытие индикатора загрузки
    hideLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    },

    // Настройка обработчика прокрутки
    setupScrollHandler() {
        if (!this.state.chatMessages) return;

        this.state.chatMessages.addEventListener('scroll', Utils.throttle(() => {
            if (this.state.chatMessages.scrollTop === 0 && 
                this.state.hasMoreMessages && 
                !this.state.isLoading) {
                this.loadOlderMessages();
            }
        }, 250));
    },

    // Автообновление сообщений
    startAutoRefresh() {
        this.state.refreshInterval = setInterval(() => {
            this.refreshMessages();
        }, this.config.refreshInterval);
    },

    // Остановка автообновления
    stopAutoRefresh() {
        if (this.state.refreshInterval) {
            clearInterval(this.state.refreshInterval);
            this.state.refreshInterval = null;
        }
    },

    // Обновление новых сообщений
    refreshMessages() {
        $.get('/chat/api/messages/', { 
            last_id: this.state.lastMessageId 
        })
        .done((data) => {
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(message => {
                    this.addNewMessage(message);
                });
                this.state.lastMessageId = data.last_id;
                this.scrollToBottom();
            }
        })
        .fail(() => {
            console.warn('Ошибка обновления чата');
        });
    },

    // Загрузка старых сообщений
    loadOlderMessages() {
        if (this.state.isLoading || !this.state.hasMoreMessages) return;

        this.state.isLoading = true;
        this.updateLoadMoreButton('loading');

        const firstMessage = document.querySelector('.message-item:first-child');
        const beforeId = firstMessage ? firstMessage.dataset.messageId : null;

        $.get('/chat/api/messages/', {
            page: this.state.currentPage + 1,
            before_id: beforeId
        })
        .done((data) => {
            this.handleOlderMessagesResponse(data);
        })
        .fail(() => {
            Notifications.show('Ошибка загрузки сообщений', 'error');
        })
        .always(() => {
            this.state.isLoading = false;
            this.updateLoadMoreButton('normal');
        });
    },

    // Обработка ответа с старыми сообщениями
    handleOlderMessagesResponse(data) {
        if (data.messages && data.messages.length > 0) {
            const scrollHeight = this.state.chatMessages.scrollHeight;
            
            // Добавляем сообщения в обратном порядке
            data.messages.reverse().forEach(message => {
                this.prependOldMessage(message);
            });

            this.state.currentPage++;
            this.state.hasMoreMessages = data.has_more;

            // Сохраняем позицию прокрутки
            this.state.chatMessages.scrollTop = this.state.chatMessages.scrollHeight - scrollHeight;
        } else {
            this.state.hasMoreMessages = false;
        }
    },

    // Добавление нового сообщения
    addNewMessage(message) {
        if (this.messageExists(message.id)) return;

        const messageElement = this.createMessageElement(message);
        this.state.chatMessages.appendChild(messageElement);
        
        // Добавляем анимацию появления
        messageElement.classList.add('fade-in');
    },

    // Добавление старого сообщения в начало
    prependOldMessage(message) {
        const messageElement = this.createMessageElement(message);
        this.state.chatMessages.insertBefore(
            messageElement, 
            this.state.chatMessages.firstChild
        );
    },

    // Создание элемента сообщения
    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = 'message-item';
        div.dataset.messageId = message.id;
        
        if (message.author === this.getCurrentUsername()) {
            div.classList.add('own');
        }

        div.innerHTML = this.createMessageHTML(message);
        return div;
    },

    // Создание HTML сообщения
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
    },

    // Создание HTML для голосования
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
    },

    // Привязка отправки форм
    bindFormSubmission() {
        // Отправка сообщений
        const messageForm = document.getElementById('message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => {
                this.handleMessageSubmission(e);
            });
        }

        // Создание голосований
        const pollForm = document.getElementById('poll-form');
        if (pollForm) {
            pollForm.addEventListener('submit', (e) => {
                this.handlePollSubmission(e);
            });
        }
    },

    // Обработка отправки сообщения
    handleMessageSubmission(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.toggleSubmitButton(submitBtn, true);

        $.ajax({
            url: form.action,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: (data) => {
                if (data.success) {
                    form.reset();
                    Notifications.show('Сообщение отправлено!', 'success');
                } else {
                    Notifications.show(data.error || 'Ошибка отправки', 'error');
                }
            },
            error: () => {
                Notifications.show('Ошибка отправки сообщения', 'error');
            },
            complete: () => {
                this.toggleSubmitButton(submitBtn, false);
            }
        });
    },

    // Обработка создания голосования
    handlePollSubmission(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.toggleSubmitButton(submitBtn, true, 'Создание...');

        $.ajax({
            url: form.action,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: (data) => {
                if (data.success) {
                    form.reset();
                    Notifications.show('Голосование создано!', 'success');
                } else {
                    Notifications.show(data.error || 'Ошибка создания', 'error');
                }
            },
            error: () => {
                Notifications.show('Ошибка создания голосования', 'error');
            },
            complete: () => {
                this.toggleSubmitButton(submitBtn, false);
            }
        });
    },

    // Переключение состояния кнопки отправки
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
    },

    // Обновление кнопки загрузки
    updateLoadMoreButton(state) {
        const btn = document.getElementById('load-more-btn');
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
    },

    // Прокрутка к низу
    scrollToBottom() {
        if (this.state.chatMessages) {
            this.state.chatMessages.scrollTop = this.state.chatMessages.scrollHeight;
        }
    },

    // Проверка существования сообщения
    messageExists(messageId) {
        return document.querySelector(`[data-message-id="${messageId}"]`) !== null;
    },

    // Получение имени текущего пользователя
    getCurrentUsername() {
        // Можно получить из глобальной переменной или другого источника
        return window.currentUser || '';
    },

    // Экранирование HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Очистка при уходе со страницы
    cleanup() {
        this.stopAutoRefresh();
    }
};

// Инициализация при загрузке DOM
$(document).ready(() => {
    ChatEnhanced.init();
});

// Очистка при уходе со страницы
$(window).on('beforeunload', () => {
    ChatEnhanced.cleanup();
});

// Экспорт для возможного использования
window.ChatEnhanced = ChatEnhanced; 