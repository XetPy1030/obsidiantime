// ObsidianTime - UI Module

/**
 * Конфигурация UI
 */
const UI_CONFIG = {
    scrollOffset: 80,
    scrollDuration: 1000,
    animationDuration: 300,
    throttleDelay: 100,
    darkModeKey: 'obsidiantime_dark_mode',
    tooltipDelay: 500
};

/**
 * Селекторы UI элементов
 */
const UI_SELECTORS = {
    darkModeToggle: '.dark-mode-toggle',
    copyToClipboard: '.copy-to-clipboard',
    smoothScrollLink: 'a[href^="#"]:not([href="#"])',
    animateOnScroll: '.animate-on-scroll',
    tooltip: '[data-bs-toggle="tooltip"]',
    dropdown: '.dropdown-toggle',
    modal: '.modal',
    accordion: '.accordion'
};

/**
 * Класс для управления UI компонентами
 */
class UIManager {
    constructor() {
        this.isScrolling = false;
        this.scrollAnimationFrame = null;
        this.observedElements = new Set();
        this.intersectionObserver = null;
        
        this.initIntersectionObserver();
    }

    /**
     * Инициализация UI менеджера
     */
    init() {
        this.bindEvents();
        this.initComponents();
        this.initDarkMode();
        this.initAnimations();
        this.setupAccessibility();
        
        // Инициализация активной навигации
        this.updateActiveNavigation();
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Переключение темной темы
        document.addEventListener('click', (e) => {
            if (e.target.matches(UI_SELECTORS.darkModeToggle) || 
                e.target.closest(UI_SELECTORS.darkModeToggle)) {
                this.toggleDarkMode(e);
            }
        });

        // Копирование в буфер обмена
        document.addEventListener('click', (e) => {
            if (e.target.matches(UI_SELECTORS.copyToClipboard) || 
                e.target.closest(UI_SELECTORS.copyToClipboard)) {
                this.handleCopyToClipboard(e);
            }
        });

        // Плавная прокрутка
        document.addEventListener('click', (e) => {
            if (e.target.matches(UI_SELECTORS.smoothScrollLink)) {
                this.handleSmoothScroll(e);
            }
        });

        // Прокрутка страницы
        window.addEventListener('scroll', this.throttle(() => {
            this.handleScroll();
        }, UI_CONFIG.throttleDelay));

        // Изменение размера окна
        window.addEventListener('resize', this.throttle(() => {
            this.handleResize();
        }, UI_CONFIG.throttleDelay));

        // Клавиатурные сочетания
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Управление фокусом
        document.addEventListener('focusin', (e) => {
            this.handleFocusIn(e);
        });

        document.addEventListener('focusout', (e) => {
            this.handleFocusOut(e);
        });

        // Обработка изменения URL (для SPA или AJAX навигации)
        window.addEventListener('popstate', () => {
            this.updateActiveNavigation();
        });

        // Обработка кликов по ссылкам навигации
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('nav a');
            if (navLink && !navLink.classList.contains('dropdown-toggle')) {
                // Небольшая задержка для обновления активного состояния после перехода
                setTimeout(() => {
                    this.updateActiveNavigation();
                }, 100);
            }
        });
    }

    /**
     * Инициализация компонентов
     */
    initComponents() {
        this.initTooltips();
        this.initDropdowns();
        this.initModals();
        this.initAccordions();
        this.initScrollToTop();
    }

    /**
     * Инициализация тултипов
     */
    initTooltips() {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipElements = document.querySelectorAll(UI_SELECTORS.tooltip);
            tooltipElements.forEach(element => {
                new bootstrap.Tooltip(element, {
                    delay: { show: UI_CONFIG.tooltipDelay, hide: 100 },
                    trigger: 'hover focus'
                });
            });
        }
    }

    /**
     * Инициализация выпадающих меню
     */
    initDropdowns() {
        const dropdownElements = document.querySelectorAll(UI_SELECTORS.dropdown);
        dropdownElements.forEach(element => {
            // Добавляем ARIA атрибуты
            element.setAttribute('aria-haspopup', 'true');
            element.setAttribute('aria-expanded', 'false');
            
            // Обработка клавиатуры
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    element.click();
                }
            });
        });
    }

    /**
     * Инициализация модальных окон
     */
    initModals() {
        const modalElements = document.querySelectorAll(UI_SELECTORS.modal);
        modalElements.forEach(modal => {
            // Обработка клавиши Escape
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const bootstrapModal = bootstrap.Modal.getInstance(modal);
                    if (bootstrapModal) {
                        bootstrapModal.hide();
                    }
                }
            });

            // Фокус на первом элементе при открытии
            modal.addEventListener('shown.bs.modal', () => {
                const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            });
        });
    }

    /**
     * Инициализация аккордеонов
     */
    initAccordions() {
        const accordionElements = document.querySelectorAll(UI_SELECTORS.accordion);
        accordionElements.forEach(accordion => {
            const buttons = accordion.querySelectorAll('.accordion-button');
            
            buttons.forEach(button => {
                button.addEventListener('keydown', (e) => {
                    this.handleAccordionKeyboard(e, buttons);
                });
            });
        });
    }

    /**
     * Инициализация кнопки "Наверх"
     */
    initScrollToTop() {
        let scrollToTopBtn = document.querySelector('.scroll-to-top');
        
        if (!scrollToTopBtn) {
            scrollToTopBtn = document.createElement('button');
            scrollToTopBtn.className = 'scroll-to-top';
            scrollToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
            scrollToTopBtn.title = 'Наверх';
            scrollToTopBtn.setAttribute('aria-label', 'Прокрутить наверх');
            document.body.appendChild(scrollToTopBtn);
        }

        scrollToTopBtn.addEventListener('click', () => {
            this.scrollToTop();
        });

        // Показ/скрытие кнопки при прокрутке
        this.toggleScrollToTopButton();
    }

    /**
     * Обработка клавиатуры для аккордеонов
     */
    handleAccordionKeyboard(event, buttons) {
        const currentIndex = Array.from(buttons).indexOf(event.target);
        let targetIndex = currentIndex;

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                targetIndex = (currentIndex + 1) % buttons.length;
                break;
            case 'ArrowUp':
                event.preventDefault();
                targetIndex = currentIndex === 0 ? buttons.length - 1 : currentIndex - 1;
                break;
            case 'Home':
                event.preventDefault();
                targetIndex = 0;
                break;
            case 'End':
                event.preventDefault();
                targetIndex = buttons.length - 1;
                break;
            default:
                return;
        }

        buttons[targetIndex].focus();
    }

    /**
     * Инициализация темной темы
     */
    initDarkMode() {
        const savedMode = localStorage.getItem(UI_CONFIG.darkModeKey);
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        const shouldUseDarkMode = savedMode === 'true' || (savedMode === null && systemPrefersDark);
        
        if (shouldUseDarkMode) {
            this.enableDarkMode();
        }

        // Отслеживание изменения системной темы
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (localStorage.getItem(UI_CONFIG.darkModeKey) === null) {
                if (e.matches) {
                    this.enableDarkMode();
                } else {
                    this.disableDarkMode();
                }
            }
        });
    }

    /**
     * Переключение темной темы
     */
    toggleDarkMode(event) {
        event?.preventDefault();
        
        const isDarkMode = document.body.classList.contains('dark-mode');
        
        if (isDarkMode) {
            this.disableDarkMode();
        } else {
            this.enableDarkMode();
        }

        // Анимация переключения
        this.animateThemeSwitch();
    }

    /**
     * Включение темной темы
     */
    enableDarkMode() {
        document.body.classList.add('dark-mode');
        localStorage.setItem(UI_CONFIG.darkModeKey, 'true');
        this.updateDarkModeToggles(true);
        
        // Обновляем мета-тег для браузера
        this.updateThemeColorMeta('#1a1a1a');
    }

    /**
     * Отключение темной темы
     */
    disableDarkMode() {
        document.body.classList.remove('dark-mode');
        localStorage.setItem(UI_CONFIG.darkModeKey, 'false');
        this.updateDarkModeToggles(false);
        
        // Обновляем мета-тег для браузера
        this.updateThemeColorMeta('#ffffff');
    }

    /**
     * Обновление переключателей темы
     */
    updateDarkModeToggles(isDark) {
        const toggles = document.querySelectorAll(UI_SELECTORS.darkModeToggle);
        toggles.forEach(toggle => {
            toggle.classList.toggle('active', isDark);
            toggle.setAttribute('aria-pressed', isDark.toString());
        });
    }

    /**
     * Обновление цвета темы в мета-теге
     */
    updateThemeColorMeta(color) {
        let metaTag = document.querySelector('meta[name="theme-color"]');
        if (!metaTag) {
            metaTag = document.createElement('meta');
            metaTag.name = 'theme-color';
            document.head.appendChild(metaTag);
        }
        metaTag.content = color;
    }

    /**
     * Анимация переключения темы
     */
    animateThemeSwitch() {
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    /**
     * Инициализация анимаций
     */
    initAnimations() {
        // Обработка элементов с анимацией при прокрутке
        this.observeAnimationElements();
        
        // Начальная проверка видимых элементов
        this.handleScroll();
    }

    /**
     * Наблюдение за элементами для анимации
     */
    observeAnimationElements() {
        const elements = document.querySelectorAll(UI_SELECTORS.animateOnScroll);
        
        elements.forEach(element => {
            this.intersectionObserver.observe(element);
            this.observedElements.add(element);
        });
    }

    /**
     * Инициализация Intersection Observer
     */
    initIntersectionObserver() {
        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    
                    // Запускаем анимацию с задержкой для последовательного появления
                    const delay = Array.from(entry.target.parentNode.children)
                        .indexOf(entry.target) * 100;
                    
                    setTimeout(() => {
                        entry.target.classList.add('animation-complete');
                    }, delay);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });
    }

    /**
     * Обработка плавной прокрутки
     */
    handleSmoothScroll(event) {
        const href = event.target.getAttribute('href');
        
        // Проверяем, что href не пустой и не равен "#"
        if (!href || href === '#' || href === '#') {
            return;
        }
        
        // Если это якорная ссылка (начинается с #)
        if (href.startsWith('#')) {
            // Дополнительная проверка - исключаем пустые якоря
            const anchorId = href.substring(1);
            if (!anchorId) {
                return;
            }
            
            const target = document.querySelector(href);
            if (target) {
                event.preventDefault();
                this.scrollToElement(target);
            } else {
                console.warn(`Target element not found for anchor: ${href}`);
            }
        }
        // Если это внешняя ссылка, не обрабатываем
        else if (href.startsWith('http') || href.startsWith('//')) {
            return;
        }
        // Для внутренних ссылок можно добавить дополнительную логику
        else {
            // Обрабатываем внутренние ссылки если нужно
            console.log('Internal link clicked:', href);
        }
    }

    /**
     * Прокрутка к элементу
     */
    scrollToElement(element) {
        const targetPosition = element.offsetTop - UI_CONFIG.scrollOffset;
        
        this.smoothScrollTo(targetPosition);
    }

    /**
     * Плавная прокрутка наверх
     */
    scrollToTop() {
        this.smoothScrollTo(0);
    }

    /**
     * Плавная прокрутка к позиции
     */
    smoothScrollTo(targetPosition) {
        if (this.isScrolling) return;
        
        this.isScrolling = true;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        const startTime = performance.now();

        const animateScroll = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / UI_CONFIG.scrollDuration, 1);
            
            // Easing function (ease-in-out)
            const easeInOut = progress < 0.5 
                ? 2 * progress * progress 
                : -1 + (4 - 2 * progress) * progress;
            
            window.scrollTo(0, startPosition + distance * easeInOut);
            
            if (progress < 1) {
                this.scrollAnimationFrame = requestAnimationFrame(animateScroll);
            } else {
                this.isScrolling = false;
                this.scrollAnimationFrame = null;
            }
        };

        this.scrollAnimationFrame = requestAnimationFrame(animateScroll);
    }

    /**
     * Обработка прокрутки
     */
    handleScroll() {
        this.toggleScrollToTopButton();
        this.updateActiveNavigation();
        this.handleParallaxEffects();
    }

    /**
     * Переключение кнопки "Наверх"
     */
    toggleScrollToTopButton() {
        const scrollToTopBtn = document.querySelector('.scroll-to-top');
        if (!scrollToTopBtn) return;

        const shouldShow = window.pageYOffset > 300;
        scrollToTopBtn.classList.toggle('show', shouldShow);
    }

    /**
     * Обновление активной навигации
     */
    updateActiveNavigation() {
        // Сначала устанавливаем активное состояние на основе URL
        this.setActiveNavigationByUrl();
        
        // Затем обновляем на основе скролла (если есть секции)
        this.updateActiveNavigationByScroll();
    }

    /**
     * Установка активной навигации на основе URL
     */
    setActiveNavigationByUrl() {
        const currentPath = window.location.pathname;
        
        // Убираем активный класс со всех ссылок (исключаем логотип)
        const allNavLinks = document.querySelectorAll('nav a:not(.dropdown-toggle):not(.navbar-brand)');
        allNavLinks.forEach(link => {
            link.classList.remove('active');
        });

        // Убираем активный класс с dropdown элементов
        const dropdownToggles = document.querySelectorAll('nav .dropdown-toggle');
        dropdownToggles.forEach(toggle => {
            toggle.classList.remove('active');
        });

        // Находим и активируем соответствующую ссылку
        const matchingLink = Array.from(allNavLinks).find(link => {
            const href = link.getAttribute('href');
            if (!href || href === '#') return false;
            
            // Нормализуем пути для сравнения
            const normalizedHref = href.endsWith('/') ? href.slice(0, -1) : href;
            const normalizedPath = currentPath.endsWith('/') ? currentPath.slice(0, -1) : currentPath;
            
            // Специальная обработка для главной страницы
            if (href === '/' || href === '/home/' || href === '/home') {
                const isHomePage = normalizedPath === '' || normalizedPath === '/' || normalizedPath === '/home';
                return isHomePage;
            }
            
            // Проверяем точное совпадение или совпадение с началом пути
            const matches = normalizedHref === normalizedPath || 
                           (normalizedHref !== '/' && normalizedPath.startsWith(normalizedHref));
            
            return matches;
        });

        if (matchingLink) {
            matchingLink.classList.add('active');
            
            // Если это dropdown элемент, активируем родительский dropdown
            const dropdownItem = matchingLink.closest('.dropdown-item');
            if (dropdownItem) {
                const dropdownToggle = dropdownItem.closest('.dropdown').querySelector('.dropdown-toggle');
                if (dropdownToggle) {
                    dropdownToggle.classList.add('active');
                }
            }
        } else {
            // Debug: выводим информацию о текущем пути
            console.log('Активная ссылка не найдена');
            console.log('Current path:', currentPath);
            console.log('Available links:', Array.from(allNavLinks).map(link => ({
                href: link.getAttribute('href'),
                text: link.textContent.trim(),
                classes: link.className
            })));
        }
    }

    /**
     * Обновление активной навигации на основе скролла
     */
    updateActiveNavigationByScroll() {
        const sections = document.querySelectorAll('section[id]');
        if (sections.length === 0) return; // Если нет секций, не обновляем по скроллу
        
        // Исключаем dropdown элементы и ссылки с href="#"
        const navLinks = document.querySelectorAll('nav a[href^="#"]:not(.dropdown-toggle):not([href="#"])');
        
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - UI_CONFIG.scrollOffset - 50;
            const sectionHeight = section.offsetHeight;
            
            if (window.pageYOffset >= sectionTop && 
                window.pageYOffset < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });

        // Убираем активный класс со всех ссылок с якорями
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        // Добавляем активный класс только к соответствующей ссылке
        if (currentSection) {
            const activeLink = document.querySelector(`nav a[href="#${currentSection}"]:not(.dropdown-toggle)`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    }

    /**
     * Обработка параллакс эффектов
     */
    handleParallaxEffects() {
        const parallaxElements = document.querySelectorAll('.parallax');
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    }

    /**
     * Обработка изменения размера окна
     */
    handleResize() {
        // Обновляем высоту для мобильных браузеров
        this.updateViewportHeight();
        
        // Переинициализируем компоненты если нужно
        this.reinitializeComponents();
    }

    /**
     * Обновление высоты viewport для мобильных
     */
    updateViewportHeight() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }

    /**
     * Переинициализация компонентов
     */
    reinitializeComponents() {
        // Переинициализируем наблюдателя для анимаций
        this.observedElements.forEach(element => {
            this.intersectionObserver.unobserve(element);
        });
        this.observedElements.clear();
        this.observeAnimationElements();
    }

    /**
     * Обработка копирования в буфер обмена
     */
    async handleCopyToClipboard(event) {
        event.preventDefault();
        
        const button = event.target.closest(UI_SELECTORS.copyToClipboard);
        const text = button.dataset.text || button.textContent.trim();
        
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
            } else {
                // Fallback для старых браузеров
                this.fallbackCopyToClipboard(text);
            }
            
            this.showCopyFeedback(button);
        } catch (error) {
            console.error('Ошибка копирования:', error);
            window.NotificationManager?.error('Ошибка копирования в буфер обмена');
        }
    }

    /**
     * Fallback для копирования в старых браузерах
     */
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
        } finally {
            document.body.removeChild(textArea);
        }
    }

    /**
     * Показ обратной связи при копировании
     */
    showCopyFeedback(button) {
        const originalText = button.textContent;
        button.textContent = 'Скопировано!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }

    /**
     * Обработка клавиатурных сочетаний
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K для поиска
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.querySelector('input[type="search"], .search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Ctrl/Cmd + D для переключения темы
        if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
            event.preventDefault();
            this.toggleDarkMode();
        }

        // Escape для закрытия модальных окон и меню
        if (event.key === 'Escape') {
            this.closeOpenOverlays();
        }
    }

    /**
     * Закрытие открытых оверлеев
     */
    closeOpenOverlays() {
        // Закрываем открытые дропдауны
        const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
        openDropdowns.forEach(dropdown => {
            const toggle = dropdown.previousElementSibling;
            if (toggle && typeof bootstrap !== 'undefined') {
                const bsDropdown = bootstrap.Dropdown.getInstance(toggle);
                if (bsDropdown) {
                    bsDropdown.hide();
                }
            }
        });
    }

    /**
     * Обработка получения фокуса
     */
    handleFocusIn(event) {
        // Добавляем класс для стилизации элементов в фокусе
        event.target.classList.add('focused');
    }

    /**
     * Обработка потери фокуса
     */
    handleFocusOut(event) {
        // Убираем класс фокуса
        event.target.classList.remove('focused');
    }

    /**
     * Настройка доступности
     */
    setupAccessibility() {
        // Добавляем skip-link для навигации с клавиатуры
        this.addSkipLink();
        
        // Улучшаем aria-labels
        this.improveAriaLabels();
        
        // Настраиваем focus trap для модальных окон
        this.setupFocusTrap();
    }

    /**
     * Добавление ссылки для пропуска навигации
     */
    addSkipLink() {
        if (document.querySelector('.skip-link')) return;
        
        const skipLink = document.createElement('a');
        skipLink.className = 'skip-link';
        skipLink.href = '#main-content';
        skipLink.textContent = 'Перейти к основному содержимому';
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }

    /**
     * Улучшение aria-labels
     */
    improveAriaLabels() {
        // Кнопки без текста
        const iconButtons = document.querySelectorAll('button:not([aria-label]):has(i:only-child)');
        iconButtons.forEach(button => {
            const icon = button.querySelector('i');
            const iconClass = icon.className;
            
            // Простая логика определения назначения по иконке
            if (iconClass.includes('search')) {
                button.setAttribute('aria-label', 'Поиск');
            } else if (iconClass.includes('menu')) {
                button.setAttribute('aria-label', 'Меню');
            } else if (iconClass.includes('close') || iconClass.includes('times')) {
                button.setAttribute('aria-label', 'Закрыть');
            }
        });
    }

    /**
     * Настройка focus trap для модальных окон
     */
    setupFocusTrap() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            modal.addEventListener('shown.bs.modal', () => {
                this.trapFocus(modal);
            });
        });
    }

    /**
     * Ограничение фокуса внутри элемента
     */
    trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        element.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }
        });
    }

    /**
     * Утилита throttle
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
     * Проверка поддержки функций браузером
     */
    checkBrowserSupport() {
        const features = {
            intersectionObserver: 'IntersectionObserver' in window,
            customProperties: CSS.supports('color', 'var(--test)'),
            objectFit: CSS.supports('object-fit', 'cover'),
            grid: CSS.supports('display', 'grid'),
            clipboard: navigator.clipboard && window.isSecureContext
        };

        // Добавляем классы для CSS fallbacks
        Object.entries(features).forEach(([feature, supported]) => {
            document.documentElement.classList.toggle(`no-${feature}`, !supported);
            document.documentElement.classList.toggle(`has-${feature}`, supported);
        });

        return features;
    }

    /**
     * Очистка ресурсов
     */
    cleanup() {
        // Отменяем анимацию прокрутки
        if (this.scrollAnimationFrame) {
            cancelAnimationFrame(this.scrollAnimationFrame);
        }

        // Отключаем наблюдателя
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }

        // Очищаем наблюдаемые элементы
        this.observedElements.clear();
    }
}

// Создание и инициализация UI менеджера
const uiManager = new UIManager();

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    uiManager.init();
});

// Очистка при выгрузке страницы
window.addEventListener('beforeunload', () => {
    uiManager.cleanup();
});

// Экспорт для использования в других модулях
window.UIManager = uiManager; 