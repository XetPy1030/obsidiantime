// ObsidianTime - Main Application Controller
'use strict';

/**
 * Главный объект приложения ObsidianTime
 * Координирует работу всех модулей
 */
const ObsidianTime = {
    // Конфигурация приложения
    config: {
        version: '2.0.0',
        debug: false,
        modules: ['notifications', 'gallery', 'forms', 'ui', 'chat']
    },

    // Состояние приложения
    state: {
        initialized: false,
        activeModules: new Set(),
        currentTheme: 'light'
    },

    /**
     * Инициализация приложения
     */
    init() {
        if (this.state.initialized) {
            console.warn('ObsidianTime уже инициализирован');
            return;
        }

        this.log('Инициализация ObsidianTime...');
        
        try {
            this.setupErrorHandling();
            this.detectFeatures();
            this.initializeModules();
            this.bindGlobalEvents();
            this.finalizeInit();
            
            this.state.initialized = true;
            this.log('ObsidianTime успешно инициализирован! 🚀');
        } catch (error) {
            console.error('Ошибка инициализации ObsidianTime:', error);
        }
    },

    /**
     * Настройка обработки ошибок
     */
    setupErrorHandling() {
        // Глобальная обработка ошибок JavaScript
        window.addEventListener('error', (event) => {
            this.handleError('JavaScript Error', event.error, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Обработка необработанных Promise
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError('Unhandled Promise Rejection', event.reason);
            event.preventDefault();
        });
    },

    /**
     * Обработка ошибок
     */
    handleError(type, error, details = {}) {
        const errorInfo = {
            type,
            message: error.message || error.toString(),
            stack: error.stack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            ...details
        };

        if (this.config.debug) {
            console.group(`🚨 ${type}`);
            console.error('Error:', error);
            console.table(errorInfo);
            console.groupEnd();
        }

        // Отправка ошибки на сервер (опционально)
        this.reportError(errorInfo);
    },

    /**
     * Отправка ошибки на сервер
     */
    async reportError(errorInfo) {
        try {
            const response = await fetch('/api/errors/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': Utils.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    ...errorInfo,
                    timestamp: new Date().toISOString(),
                    url: window.location.href,
                    userAgent: navigator.userAgent,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            this.log('Ошибка отправлена на сервер:', result);
            
        } catch (e) {
            // Логируем ошибку отправки, но не показываем пользователю
            this.log('Ошибка отправки отчета об ошибке:', e);
        }
    },

    /**
     * Определение возможностей браузера
     */
    detectFeatures() {
        const features = {
            // JavaScript возможности
            es6: typeof Symbol !== 'undefined',
            es2017: typeof Object.values === 'function',
            modules: 'noModule' in HTMLScriptElement.prototype,
            
            // Web APIs
            intersectionObserver: 'IntersectionObserver' in window,
            resizeObserver: 'ResizeObserver' in window,
            webp: this.supportsWebP(),
            touchDevice: 'ontouchstart' in window,
            
            // CSS возможности
            customProperties: CSS.supports('color', 'var(--test)'),
            grid: CSS.supports('display', 'grid'),
            flexbox: CSS.supports('display', 'flex'),
            objectFit: CSS.supports('object-fit', 'cover')
        };

        // Добавляем классы для CSS
        Object.entries(features).forEach(([feature, supported]) => {
            document.documentElement.classList.toggle(`has-${feature}`, supported);
            document.documentElement.classList.toggle(`no-${feature}`, !supported);
        });

        this.features = features;
        this.log('Возможности браузера определены:', features);
    },

    /**
     * Проверка поддержки WebP
     */
    supportsWebP() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    },

    /**
     * Инициализация модулей
     */
    initializeModules() {
        // Проверяем доступность модулей и инициализируем их
        const moduleChecks = {
            notifications: () => window.NotificationManager,
            gallery: () => window.GalleryManager,
            forms: () => window.FormsManager,
            ui: () => window.UIManager,
            chat: () => window.ChatManager
        };

        Object.entries(moduleChecks).forEach(([moduleName, checkFn]) => {
            try {
                const moduleInstance = checkFn();
                if (moduleInstance) {
                    this.state.activeModules.add(moduleName);
                    this.log(`✓ Модуль ${moduleName} активен`);
                } else {
                    this.log(`⚠ Модуль ${moduleName} не найден`);
                }
            } catch (error) {
                this.log(`✗ Ошибка модуля ${moduleName}:`, error);
            }
        });
    },

    /**
     * Привязка глобальных событий
     */
    bindGlobalEvents() {
        // Отслеживание изменения размера окна
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleWindowResize();
            }, 250);
        });

        // Отслеживание изменения ориентации
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        // Отслеживание видимости страницы
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });

        // Отслеживание состояния сети
        if ('navigator' in window && 'onLine' in navigator) {
            window.addEventListener('online', () => this.handleNetworkChange(true));
            window.addEventListener('offline', () => this.handleNetworkChange(false));
        }
    },

    /**
     * Обработка изменения размера окна
     */
    handleWindowResize() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // Обновляем CSS переменные
        document.documentElement.style.setProperty('--window-width', `${width}px`);
        document.documentElement.style.setProperty('--window-height', `${height}px`);
        
        // Определяем точки останова
        const breakpoints = {
            mobile: width < 768,
            tablet: width >= 768 && width < 992,
            desktop: width >= 992
        };

        Object.entries(breakpoints).forEach(([name, matches]) => {
            document.documentElement.classList.toggle(`is-${name}`, matches);
        });

        this.log('Изменение размера окна:', { width, height, breakpoints });
    },

    /**
     * Обработка изменения ориентации
     */
    handleOrientationChange() {
        const orientation = screen.orientation?.type || 
                          (window.innerHeight > window.innerWidth ? 'portrait' : 'landscape');
        
        document.documentElement.classList.toggle('is-portrait', orientation.includes('portrait'));
        document.documentElement.classList.toggle('is-landscape', orientation.includes('landscape'));
        
        this.log('Изменение ориентации:', orientation);
    },

    /**
     * Обработка изменения видимости страницы
     */
    handleVisibilityChange() {
        const isVisible = !document.hidden;
        
        if (isVisible) {
            this.log('Страница стала видимой');
            // Возобновляем активности (например, анимации, запросы)
            this.resumeActivities();
        } else {
            this.log('Страница скрыта');
            // Приостанавливаем активности для экономии ресурсов
            this.pauseActivities();
        }
    },

    /**
     * Обработка изменения состояния сети
     */
    handleNetworkChange(isOnline) {
        document.documentElement.classList.toggle('is-online', isOnline);
        document.documentElement.classList.toggle('is-offline', !isOnline);
        
        if (isOnline) {
            this.log('Соединение восстановлено');
            window.NotificationManager?.success('Соединение восстановлено');
        } else {
            this.log('Соединение потеряно');
            window.NotificationManager?.warning('Нет соединения с интернетом');
        }
    },

    /**
     * Приостановка активностей
     */
    pauseActivities() {
        // Уведомляем модули о необходимости приостановить активности
        this.state.activeModules.forEach(moduleName => {
            const moduleInstance = this.getModuleInstance(moduleName);
            if (moduleInstance && typeof moduleInstance.pause === 'function') {
                moduleInstance.pause();
            }
        });
    },

    /**
     * Возобновление активностей
     */
    resumeActivities() {
        // Уведомляем модули о необходимости возобновить активности
        this.state.activeModules.forEach(moduleName => {
            const moduleInstance = this.getModuleInstance(moduleName);
            if (moduleInstance && typeof moduleInstance.resume === 'function') {
                moduleInstance.resume();
            }
        });
    },

    /**
     * Получение экземпляра модуля
     */
    getModuleInstance(moduleName) {
        const moduleMap = {
            notifications: () => window.NotificationManager,
            gallery: () => window.GalleryManager,
            forms: () => window.FormsManager,
            ui: () => window.UIManager,
            chat: () => window.ChatManager
        };

        return moduleMap[moduleName]?.();
    },

    /**
     * Финализация инициализации
     */
    finalizeInit() {
        // Устанавливаем глобальные CSS переменные
        this.setCSSVariables();
        
        // Запускаем начальную обработку размера окна
        this.handleWindowResize();
        
        // Показываем приложение
        document.body.classList.add('app-loaded');
        
        // Скрываем прелоадер
        this.hidePreloader();
    },

    /**
     * Установка CSS переменных
     */
    setCSSVariables() {
        const root = document.documentElement;
        
        // Цвета темы
        const isDark = document.body.classList.contains('dark-mode');
        this.state.currentTheme = isDark ? 'dark' : 'light';
        
        // Размеры
        root.style.setProperty('--header-height', '60px');
        root.style.setProperty('--footer-height', '80px');
        root.style.setProperty('--sidebar-width', '250px');
        
        // Анимации
        root.style.setProperty('--animation-duration', '0.3s');
        root.style.setProperty('--animation-easing', 'cubic-bezier(0.4, 0, 0.2, 1)');
    },

    /**
     * Скрытие прелоадера
     */
    hidePreloader() {
        const preloader = document.querySelector('.preloader');
        if (preloader) {
            preloader.style.opacity = '0';
            setTimeout(() => {
                if (preloader.parentNode) {
                    preloader.parentNode.removeChild(preloader);
                }
            }, 300);
        }
    },

    /**
     * Логирование
     */
    log(...args) {
        if (this.config.debug || localStorage.getItem('obsidiantime_debug') === 'true') {
            console.log('%c[ObsidianTime]', 'color: #007bff; font-weight: bold;', ...args);
        }
    },

    /**
     * Получение информации о приложении
     */
    getInfo() {
        return {
            version: this.config.version,
            initialized: this.state.initialized,
            activeModules: Array.from(this.state.activeModules),
            currentTheme: this.state.currentTheme,
            features: this.features,
            performance: {
                loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart
            }
        };
    },

    /**
     * Включение/выключение режима отладки
     */
    setDebugMode(enabled) {
        this.config.debug = enabled;
        localStorage.setItem('obsidiantime_debug', enabled.toString());
        this.log('Режим отладки:', enabled ? 'включен' : 'выключен');
    }
};

/**
 * Утилиты общего назначения
 */
const Utils = {
    /**
     * Получение cookie
     */
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

    /**
     * Debounce функция
     */
    debounce(func, delay) {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * Throttle функция
     */
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

    /**
     * Проверка на мобильное устройство
     */
    isMobile() {
        return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },

    /**
     * Форматирование чисел
     */
    formatNumber(num) {
        return new Intl.NumberFormat('ru-RU').format(num);
    },

    /**
     * Форматирование дат
     */
    formatDate(date, options = {}) {
        const defaultOptions = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        return new Intl.DateTimeFormat('ru-RU', { ...defaultOptions, ...options }).format(date);
    },

    /**
     * Генерация уникального ID
     */
    generateId(prefix = 'id') {
        return `${prefix}-${Math.random().toString(36).substr(2, 9)}-${Date.now().toString(36)}`;
    },

    /**
     * Глубокое клонирование объекта
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            Object.keys(obj).forEach(key => {
                cloned[key] = this.deepClone(obj[key]);
            });
            return cloned;
        }
    },

    /**
     * Проверка поддержки localStorage
     */
    hasLocalStorage() {
        try {
            const test = '__test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * Безопасное получение значения из localStorage
     */
    getLocalStorage(key, defaultValue = null) {
        if (!this.hasLocalStorage()) return defaultValue;
        
        try {
            const value = localStorage.getItem(key);
            return value !== null ? JSON.parse(value) : defaultValue;
        } catch {
            return defaultValue;
        }
    },

    /**
     * Безопасное сохранение в localStorage
     */
    setLocalStorage(key, value) {
        if (!this.hasLocalStorage()) return false;
        
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch {
            return false;
        }
    }
};

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    ObsidianTime.init();
});

// Экспорт для глобального использования
window.ObsidianTime = ObsidianTime;
window.Utils = Utils;

// Для отладки в консоли
if (typeof window !== 'undefined') {
    window.debug = {
        app: () => ObsidianTime.getInfo(),
        enableDebug: () => ObsidianTime.setDebugMode(true),
        disableDebug: () => ObsidianTime.setDebugMode(false),
        modules: () => Array.from(ObsidianTime.state.activeModules),
        features: () => ObsidianTime.features
    };
} 