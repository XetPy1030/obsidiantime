// ObsidianTime - Forms Module

/**
 * Конфигурация форм
 */
const FORMS_CONFIG = {
    searchDebounceDelay: 500,
    validateDelay: 300,
    autoSaveDelay: 2000,
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedImageTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
};

/**
 * Селекторы форм
 */
const FORMS_SELECTORS = {
    fileInput: 'input[type="file"]',
    searchInput: '.search-input',
    confirmAction: '.confirm-action',
    autoSave: '[data-auto-save]',
    validateOnBlur: '[data-validate]',
    imagePreview: '.image-preview',
    characterCounter: '.character-counter',
    form: 'form'
};

/**
 * Класс для управления формами
 */
class FormsManager {
    constructor() {
        this.searchTimeouts = new Map();
        this.validationTimeouts = new Map();
        this.autoSaveTimeouts = new Map();
        this.validators = new Map();
        
        this.initValidators();
    }

    /**
     * Инициализация менеджера форм
     */
    init() {
        this.bindEvents();
        this.initExistingElements();
        this.setupCSRF();
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Обработка файлов
        document.addEventListener('change', (e) => {
            if (e.target.matches(FORMS_SELECTORS.fileInput)) {
                this.handleFileChange(e);
            }
        });

        // Поиск
        document.addEventListener('input', (e) => {
            if (e.target.matches(FORMS_SELECTORS.searchInput)) {
                this.handleSearch(e);
            }
        });

        // Подтверждение действий
        document.addEventListener('click', (e) => {
            if (e.target.matches(FORMS_SELECTORS.confirmAction)) {
                this.handleConfirmAction(e);
            }
        });

        // Автосохранение
        document.addEventListener('input', (e) => {
            if (e.target.matches(FORMS_SELECTORS.autoSave)) {
                this.handleAutoSave(e);
            }
        });

        // Валидация при потере фокуса
        document.addEventListener('blur', (e) => {
            if (e.target.matches(FORMS_SELECTORS.validateOnBlur)) {
                this.handleValidation(e);
            }
        }, true);

        // Счетчик символов
        document.addEventListener('input', (e) => {
            if (e.target.hasAttribute('maxlength')) {
                this.updateCharacterCounter(e.target);
            }
        });

        // Отправка форм
        document.addEventListener('submit', (e) => {
            if (e.target.matches(FORMS_SELECTORS.form)) {
                this.handleFormSubmit(e);
            }
        });
    }

    /**
     * Обработка загрузки файлов
     */
    handleFileChange(event) {
        const input = event.target;
        const files = Array.from(input.files);
        
        if (files.length === 0) {
            this.clearPreview(input);
            return;
        }

        // Валидация файлов
        const validation = this.validateFiles(files, input);
        if (!validation.valid) {
            window.NotificationManager?.error(validation.message);
            input.value = '';
            return;
        }

        // Создание превью
        if (input.accept && input.accept.includes('image')) {
            this.createImagePreview(input, files[0]);
        } else {
            this.createFilePreview(input, files);
        }

        // Trigger custom event
        input.dispatchEvent(new CustomEvent('fileProcessed', {
            detail: { files, valid: validation.valid }
        }));
    }

    /**
     * Валидация файлов
     */
    validateFiles(files, input) {
        const maxFiles = parseInt(input.dataset.maxFiles) || 1;
        const maxSize = parseInt(input.dataset.maxSize) || FORMS_CONFIG.maxFileSize;
        const allowedTypes = input.accept ? input.accept.split(',').map(t => t.trim()) : [];

        if (files.length > maxFiles) {
            return {
                valid: false,
                message: `Можно выбрать не более ${maxFiles} файл(ов)`
            };
        }

        for (const file of files) {
            if (file.size > maxSize) {
                return {
                    valid: false,
                    message: `Размер файла "${file.name}" превышает ${this.formatFileSize(maxSize)}`
                };
            }

            if (allowedTypes.length > 0 && !allowedTypes.some(type => 
                file.type.includes(type.replace('*', '')) || 
                file.name.toLowerCase().endsWith(type.replace('*', '')))) {
                return {
                    valid: false,
                    message: `Файл "${file.name}" имеет недопустимый тип`
                };
            }
        }

        return { valid: true };
    }

    /**
     * Создание превью изображения
     */
    createImagePreview(input, file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            let preview = this.getOrCreatePreview(input);
            
            preview.innerHTML = `
                <div class="preview-container">
                    <img src="${e.target.result}" class="preview-image" alt="Превью">
                    <div class="preview-overlay">
                        <div class="preview-info">
                            <span class="file-name">${file.name}</span>
                            <span class="file-size">${this.formatFileSize(file.size)}</span>
                        </div>
                        <button type="button" class="btn-remove-preview" title="Удалить">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;

            this.bindPreviewEvents(preview, input);
            this.animatePreview(preview);
        };

        reader.onerror = () => {
            window.NotificationManager?.error('Ошибка при чтении файла');
        };

        reader.readAsDataURL(file);
    }

    /**
     * Создание превью файла
     */
    createFilePreview(input, files) {
        let preview = this.getOrCreatePreview(input);
        
        const filesHtml = files.map(file => `
            <div class="file-item">
                <i class="fas fa-file"></i>
                <div class="file-info">
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${this.formatFileSize(file.size)}</span>
                </div>
            </div>
        `).join('');

        preview.innerHTML = `
            <div class="files-preview">
                ${filesHtml}
                <button type="button" class="btn-remove-preview" title="Удалить все">
                    <i class="fas fa-times"></i> Удалить
                </button>
            </div>
        `;

        this.bindPreviewEvents(preview, input);
        this.animatePreview(preview);
    }

    /**
     * Получение или создание превью контейнера
     */
    getOrCreatePreview(input) {
        let preview = input.parentNode.querySelector(FORMS_SELECTORS.imagePreview);
        
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'image-preview mt-2';
            input.parentNode.appendChild(preview);
        }

        return preview;
    }

    /**
     * Привязка событий превью
     */
    bindPreviewEvents(preview, input) {
        const removeBtn = preview.querySelector('.btn-remove-preview');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                input.value = '';
                this.clearPreview(input);
            });
        }
    }

    /**
     * Анимация появления превью
     */
    animatePreview(preview) {
        preview.style.opacity = '0';
        preview.style.transform = 'translateY(-10px)';
        
        requestAnimationFrame(() => {
            preview.style.transition = 'opacity 300ms, transform 300ms';
            preview.style.opacity = '1';
            preview.style.transform = 'translateY(0)';
        });
    }

    /**
     * Очистка превью
     */
    clearPreview(input) {
        const preview = input.parentNode.querySelector(FORMS_SELECTORS.imagePreview);
        if (preview) {
            preview.style.transition = 'opacity 300ms';
            preview.style.opacity = '0';
            setTimeout(() => {
                if (preview.parentNode) {
                    preview.parentNode.removeChild(preview);
                }
            }, 300);
        }
    }

    /**
     * Обработка поиска с debounce
     */
    handleSearch(event) {
        const input = event.target;
        const query = input.value.trim();
        const form = input.closest('form');
        const minLength = parseInt(input.dataset.minLength) || 3;

        // Очищаем предыдущий таймер
        if (this.searchTimeouts.has(input)) {
            clearTimeout(this.searchTimeouts.get(input));
        }

        // Устанавливаем новый таймер
        const timeout = setTimeout(() => {
            if (query.length >= minLength || query.length === 0) {
                if (form && input.dataset.autoSubmit !== 'false') {
                    this.submitForm(form);
                }
                
                // Trigger custom event
                input.dispatchEvent(new CustomEvent('searchChanged', {
                    detail: { query, minLength }
                }));
            }
        }, FORMS_CONFIG.searchDebounceDelay);

        this.searchTimeouts.set(input, timeout);
    }

    /**
     * Обработка подтверждения действий
     */
    handleConfirmAction(event) {
        const element = event.target;
        const message = element.dataset.confirm || 'Вы уверены?';
        const title = element.dataset.confirmTitle || 'Подтверждение';
        
        event.preventDefault();
        
        this.showConfirmDialog(title, message).then(confirmed => {
            if (confirmed) {
                // Если это ссылка
                if (element.tagName === 'A') {
                    window.location.href = element.href;
                }
                // Если это кнопка в форме
                else if (element.type === 'submit') {
                    element.closest('form')?.submit();
                }
                // Если есть data-action
                else if (element.dataset.action) {
                    this.executeAction(element.dataset.action, element);
                }
            }
        });
    }

    /**
     * Показ диалога подтверждения
     */
    showConfirmDialog(title, message) {
        return new Promise(resolve => {
            // Простая реализация через confirm
            // В будущем можно заменить на красивый модальный диалог
            const result = confirm(`${title}\n\n${message}`);
            resolve(result);
        });
    }

    /**
     * Выполнение действия
     */
    async executeAction(action, element) {
        const url = element.dataset.url;
        if (!url) return;

        try {
            element.disabled = true;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    window.NotificationManager?.success(data.message || 'Действие выполнено');
                    
                    // Перезагрузка страницы если требуется
                    if (data.reload) {
                        window.location.reload();
                    }
                } else {
                    window.NotificationManager?.error(data.message || 'Ошибка выполнения');
                }
            }
        } catch (error) {
            window.NotificationManager?.error('Ошибка при выполнении действия');
        } finally {
            element.disabled = false;
        }
    }

    /**
     * Обработка автосохранения
     */
    handleAutoSave(event) {
        const input = event.target;
        const form = input.closest('form');
        const saveUrl = input.dataset.autoSave || form?.dataset.autoSave;

        if (!saveUrl) return;

        // Очищаем предыдущий таймер
        if (this.autoSaveTimeouts.has(input)) {
            clearTimeout(this.autoSaveTimeouts.get(input));
        }

        // Устанавливаем новый таймер
        const timeout = setTimeout(() => {
            this.performAutoSave(input, saveUrl);
        }, FORMS_CONFIG.autoSaveDelay);

        this.autoSaveTimeouts.set(input, timeout);
    }

    /**
     * Выполнение автосохранения
     */
    async performAutoSave(input, url) {
        const form = input.closest('form');
        const formData = new FormData(form);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                this.showAutoSaveIndicator(input, true);
            } else {
                this.showAutoSaveIndicator(input, false);
            }
        } catch (error) {
            this.showAutoSaveIndicator(input, false);
        }
    }

    /**
     * Показ индикатора автосохранения
     */
    showAutoSaveIndicator(input, success) {
        let indicator = input.parentNode.querySelector('.auto-save-indicator');
        
        if (!indicator) {
            indicator = document.createElement('span');
            indicator.className = 'auto-save-indicator';
            input.parentNode.appendChild(indicator);
        }

        indicator.className = `auto-save-indicator ${success ? 'success' : 'error'}`;
        indicator.textContent = success ? 'Сохранено' : 'Ошибка сохранения';
        
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }

    /**
     * Обновление счетчика символов
     */
    updateCharacterCounter(input) {
        const maxLength = parseInt(input.getAttribute('maxlength'));
        const currentLength = input.value.length;
        
        let counter = input.parentNode.querySelector(FORMS_SELECTORS.characterCounter);
        
        if (!counter) {
            counter = document.createElement('div');
            counter.className = 'character-counter';
            input.parentNode.appendChild(counter);
        }

        counter.textContent = `${currentLength}/${maxLength}`;
        counter.classList.toggle('warning', currentLength > maxLength * 0.8);
        counter.classList.toggle('error', currentLength >= maxLength);
    }

    /**
     * Инициализация валидаторов
     */
    initValidators() {
        this.validators.set('email', (value) => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(value);
        });

        this.validators.set('phone', (value) => {
            const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            return phoneRegex.test(value.replace(/\s+/g, ''));
        });

        this.validators.set('url', (value) => {
            try {
                new URL(value);
                return true;
            } catch {
                return false;
            }
        });
    }

    /**
     * Обработка валидации
     */
    handleValidation(event) {
        const input = event.target;
        const validator = input.dataset.validate;
        
        if (!validator || !this.validators.has(validator)) return;

        // Очищаем предыдущий таймер
        if (this.validationTimeouts.has(input)) {
            clearTimeout(this.validationTimeouts.get(input));
        }

        // Устанавливаем новый таймер
        const timeout = setTimeout(() => {
            this.performValidation(input, validator);
        }, FORMS_CONFIG.validateDelay);

        this.validationTimeouts.set(input, timeout);
    }

    /**
     * Выполнение валидации
     */
    performValidation(input, validator) {
        const value = input.value.trim();
        if (!value) return;

        const isValid = this.validators.get(validator)(value);
        this.showValidationResult(input, isValid);
    }

    /**
     * Показ результата валидации
     */
    showValidationResult(input, isValid) {
        input.classList.toggle('is-valid', isValid);
        input.classList.toggle('is-invalid', !isValid);

        let feedback = input.parentNode.querySelector('.validation-feedback');
        
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'validation-feedback';
            input.parentNode.appendChild(feedback);
        }

        feedback.className = `validation-feedback ${isValid ? 'valid' : 'invalid'}`;
        feedback.textContent = isValid ? 
            'Корректно' : 
            input.dataset.errorMessage || 'Некорректное значение';
    }

    /**
     * Обработка отправки формы
     */
    handleFormSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');

        // Проверяем валидность формы
        if (!this.validateForm(form)) {
            event.preventDefault();
            return;
        }

        // Показываем индикатор загрузки
        if (submitBtn) {
            this.setSubmitButtonLoading(submitBtn, true);
        }

        // Если форма отправляется через AJAX
        if (form.dataset.ajax === 'true') {
            event.preventDefault();
            this.submitFormAjax(form);
        }
    }

    /**
     * Валидация формы
     */
    validateForm(form) {
        const requiredInputs = form.querySelectorAll('[required]');
        let isValid = true;

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                this.showValidationResult(input, false);
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * AJAX отправка формы
     */
    async submitFormAjax(form) {
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');

        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    window.NotificationManager?.success(data.message || 'Форма отправлена успешно');
                    
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (form.dataset.resetOnSuccess !== 'false') {
                        form.reset();
                        this.clearAllPreviews(form);
                    }
                } else {
                    window.NotificationManager?.error(data.message || 'Ошибка отправки формы');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            window.NotificationManager?.error('Ошибка при отправке формы');
        } finally {
            if (submitBtn) {
                this.setSubmitButtonLoading(submitBtn, false);
            }
        }
    }

    /**
     * Утилиты
     */

    /**
     * Инициализация существующих элементов
     */
    initExistingElements() {
        // Счетчики символов
        document.querySelectorAll('input[maxlength], textarea[maxlength]').forEach(input => {
            this.updateCharacterCounter(input);
        });

        // Превью файлов
        document.querySelectorAll(FORMS_SELECTORS.fileInput).forEach(input => {
            if (input.files.length > 0) {
                this.handleFileChange({ target: input });
            }
        });
    }

    /**
     * Настройка CSRF
     */
    setupCSRF() {
        // Автоматическое добавление CSRF токена к AJAX запросам
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            // Устанавливаем мета-тег для удобства
            let metaTag = document.querySelector('meta[name="csrf-token"]');
            if (!metaTag) {
                metaTag = document.createElement('meta');
                metaTag.name = 'csrf-token';
                metaTag.content = csrfToken;
                document.head.appendChild(metaTag);
            }
        }
    }

    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
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
     * Установка состояния загрузки кнопки отправки
     */
    setSubmitButtonLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = '<span class="spinner"></span> Отправка...';
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'Отправить';
        }
    }

    /**
     * Очистка всех превью в форме
     */
    clearAllPreviews(form) {
        const previews = form.querySelectorAll(FORMS_SELECTORS.imagePreview);
        previews.forEach(preview => {
            if (preview.parentNode) {
                preview.parentNode.removeChild(preview);
            }
        });
    }

    /**
     * Отправка формы программно
     */
    submitForm(form) {
        if (form.requestSubmit) {
            form.requestSubmit();
        } else {
            form.submit();
        }
    }
}

// Создание и инициализация менеджера форм
const formsManager = new FormsManager();

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    formsManager.init();
});

// Экспорт для использования в других модулях
window.FormsManager = formsManager; 