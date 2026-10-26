// ObsidianTime - Согласие на сбор данных и аналитика посещений
'use strict';

/**
 * Сбор данных о посещениях.
 *
 * Пока посетитель не нажал «Разрешить» в баннере, ничего не отправляется.
 * Всё, что собирается здесь, перечислено на странице /privacy/ —
 * при добавлении новых данных обновите её и TRACKING["POLICY_VERSION"]
 * в settings.py, чтобы баннер снова спросил согласие.
 */
const Tracking = {
    FLUSH_DELAY: 5000,
    MAX_EVENTS_PER_REQUEST: 50,
    MAX_CLICKS_PER_PAGE: 100,

    config: null,
    banner: null,
    started: false,
    pageId: null,
    pageStart: 0,
    activeMs: 0,
    visibleSince: null,
    leaveSent: false,
    maxScroll: 0,
    clickCount: 0,
    scrollScheduled: false,
    queue: [],
    flushTimer: null,

    init() {
        const configElement = document.getElementById('tracking-config');
        if (!configElement) return;

        this.config = JSON.parse(configElement.textContent);
        this.banner = document.getElementById('consent-banner');
        this.bindBanner();
        this.initPrivacyPanel();

        document.querySelectorAll('[data-consent-open]').forEach((element) => {
            element.addEventListener('click', (event) => {
                event.preventDefault();
                this.showBanner(true);
            });
        });

        const consent = this.config.consent;
        if (!consent) {
            this.showBanner(false);
        } else if (consent.analytics) {
            this.start();
        }
    },

    // ---------- Баннер согласия ----------

    bindBanner() {
        if (!this.banner) return;

        this.banner.addEventListener('click', (event) => {
            const button = event.target.closest('[data-consent-action]');
            if (!button) return;

            switch (button.dataset.consentAction) {
                case 'accept':
                    this.saveConsent(true);
                    break;
                case 'decline':
                    this.saveConsent(false);
                    break;
                case 'save':
                    this.saveConsent(document.getElementById('consent-analytics').checked);
                    break;
                case 'customize':
                    this.toggleDetails(true);
                    break;
            }
        });
    },

    showBanner(withDetails) {
        if (!this.banner) return;
        document.getElementById('consent-analytics').checked = this.hasAnalyticsConsent();
        this.toggleDetails(withDetails);
        this.banner.hidden = false;
    },

    hideBanner() {
        if (this.banner) this.banner.hidden = true;
    },

    toggleDetails(show) {
        this.banner.querySelector('.consent-banner__details').hidden = !show;
        this.banner.querySelector('[data-consent-action="customize"]').hidden = show;
        this.banner.querySelector('[data-consent-action="save"]').hidden = !show;
    },

    hasAnalyticsConsent() {
        return Boolean(this.config.consent && this.config.consent.analytics);
    },

    async saveConsent(analytics) {
        try {
            const response = await this.post(this.config.urls.consent, { analytics });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
        } catch (error) {
            window.NotificationManager?.error('Не удалось сохранить выбор, попробуйте ещё раз');
            return;
        }

        const hadAnalytics = this.hasAnalyticsConsent();
        this.config.consent = { analytics };
        this.hideBanner();
        document.dispatchEvent(new CustomEvent('tracking:consent-changed', { detail: { analytics } }));

        if (analytics && !hadAnalytics) {
            this.start();
            this.activateDeferredScripts();
        } else if (!analytics && hadAnalytics) {
            // Сторонние счётчики уже загружены — остановить их можно только перезагрузкой
            this.stop();
            window.location.reload();
        }
    },

    /**
     * Сторонние счётчики без согласия лежат в <template> и не выполняются
     */
    activateDeferredScripts() {
        const template = document.getElementById('deferred-analytics');
        if (!template) return;

        template.content.querySelectorAll('script').forEach((original) => {
            const script = document.createElement('script');
            Array.from(original.attributes).forEach((attr) => script.setAttribute(attr.name, attr.value));
            script.text = original.text;
            document.body.appendChild(script);
        });
        template.remove();
    },

    // ---------- Сбор событий ----------

    start() {
        if (this.started) return;
        this.started = true;

        this.onClick = (event) => this.trackClick(event);
        this.onScroll = () => this.scheduleScrollUpdate();
        this.onVisibilityChange = () => {
            if (document.visibilityState === 'hidden') {
                this.pauseTimer();
                this.sendLeave();
            } else {
                this.resumeTimer();
            }
        };
        this.onPageHide = () => {
            this.pauseTimer();
            this.sendLeave();
        };
        this.onPageShow = (event) => {
            // Страница восстановлена из кеша «назад/вперёд» — это новый просмотр
            if (event.persisted) this.beginPageView();
        };

        document.addEventListener('click', this.onClick, true);
        window.addEventListener('scroll', this.onScroll, { passive: true });
        document.addEventListener('visibilitychange', this.onVisibilityChange);
        window.addEventListener('pagehide', this.onPageHide);
        window.addEventListener('pageshow', this.onPageShow);

        this.beginPageView();
    },

    stop() {
        if (!this.started) return;
        this.started = false;

        document.removeEventListener('click', this.onClick, true);
        window.removeEventListener('scroll', this.onScroll);
        document.removeEventListener('visibilitychange', this.onVisibilityChange);
        window.removeEventListener('pagehide', this.onPageHide);
        window.removeEventListener('pageshow', this.onPageShow);

        clearTimeout(this.flushTimer);
        this.flushTimer = null;
        this.queue = [];
    },

    async beginPageView() {
        this.pageId = this.generateId();
        this.pageStart = performance.now();
        this.activeMs = 0;
        this.visibleSince = document.visibilityState === 'visible' ? this.pageStart : null;
        this.leaveSent = false;
        this.maxScroll = 0;
        this.clickCount = 0;
        this.updateScroll();

        const pageFields = this.pageFields();
        const client = await this.collectClientInfo();
        this.send([{
            ...pageFields,
            type: 'pageview',
            data: {
                utm: this.getUtm(),
                navigation_type: performance.getEntriesByType?.('navigation')?.[0]?.type,
                history_length: window.history.length,
            },
        }], client);
    },

    sendLeave() {
        if (!this.started || this.leaveSent) return;
        this.leaveSent = true;

        this.queue.push({
            ...this.pageFields(),
            type: 'page_leave',
            data: {
                active_ms: Math.round(this.activeMs),
                total_ms: Math.round(performance.now() - this.pageStart),
                max_scroll_percent: this.maxScroll,
                clicks: this.clickCount,
                timing: this.getTiming(),
            },
        });
        this.flush();
    },

    trackClick(event) {
        const target = event.target.closest(
            'a, button, [role="button"], input[type="submit"], input[type="button"]'
        );
        if (!target || this.clickCount >= this.MAX_CLICKS_PER_PAGE) return;
        this.clickCount += 1;

        // Содержимое полей ввода не собирается: value берётся только у кнопок
        const text = target.innerText || target.value || target.getAttribute('aria-label') || '';
        this.queue.push({
            ...this.pageFields(),
            type: 'click',
            data: {
                element: target.tagName.toLowerCase(),
                text: text.trim().slice(0, 100),
                href: target.tagName === 'A' ? target.href : null,
                element_id: target.id || null,
                x: event.clientX,
                y: event.clientY,
            },
        });
        this.scheduleFlush();
    },

    pauseTimer() {
        if (this.visibleSince === null) return;
        this.activeMs += performance.now() - this.visibleSince;
        this.visibleSince = null;
    },

    resumeTimer() {
        if (this.visibleSince === null) this.visibleSince = performance.now();
        // Вернулись на вкладку — при следующем уходе отправим обновлённые итоги
        this.leaveSent = false;
    },

    scheduleScrollUpdate() {
        if (this.scrollScheduled) return;
        this.scrollScheduled = true;
        requestAnimationFrame(() => {
            this.scrollScheduled = false;
            this.updateScroll();
        });
    },

    updateScroll() {
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        const percent = scrollable > 0 ? Math.round((window.scrollY / scrollable) * 100) : 100;
        this.maxScroll = Math.max(this.maxScroll, Math.min(100, percent));
    },

    // ---------- Данные страницы и устройства ----------

    pageFields() {
        return {
            page_id: this.pageId,
            url: window.location.href,
            path: window.location.pathname,
            referrer: document.referrer,
            title: document.title,
        };
    },

    getUtm() {
        const params = new URLSearchParams(window.location.search);
        const utm = {};
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach((key) => {
            if (params.has(key)) utm[key] = params.get(key);
        });
        return Object.keys(utm).length ? utm : null;
    },

    getTiming() {
        const navigation = performance.getEntriesByType?.('navigation')?.[0];
        if (!navigation) return null;
        return {
            ttfb_ms: Math.round(navigation.responseStart),
            dom_content_loaded_ms: Math.round(navigation.domContentLoadedEventEnd),
            load_ms: Math.round(navigation.loadEventEnd),
            transfer_size: navigation.transferSize,
        };
    },

    async collectClientInfo() {
        const nav = window.navigator;
        const screen = window.screen || {};
        const connection = nav.connection || {};
        const media = (query) => window.matchMedia?.(query).matches;

        return {
            screen: {
                width: screen.width,
                height: screen.height,
                avail_width: screen.availWidth,
                avail_height: screen.availHeight,
                color_depth: screen.colorDepth,
                pixel_ratio: window.devicePixelRatio,
                orientation: screen.orientation?.type,
            },
            viewport: { width: window.innerWidth, height: window.innerHeight },
            language: nav.language,
            languages: Array.from(nav.languages || []),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezone_offset: new Date().getTimezoneOffset(),
            platform: nav.platform,
            vendor: nav.vendor,
            hardware_concurrency: nav.hardwareConcurrency,
            device_memory_gb: nav.deviceMemory,
            max_touch_points: nav.maxTouchPoints,
            cookies_enabled: nav.cookieEnabled,
            pdf_viewer: nav.pdfViewerEnabled,
            do_not_track: nav.doNotTrack,
            global_privacy_control: nav.globalPrivacyControl,
            connection: {
                type: connection.type,
                effective_type: connection.effectiveType,
                downlink_mbps: connection.downlink,
                rtt_ms: connection.rtt,
                save_data: connection.saveData,
            },
            preferences: {
                color_scheme: media('(prefers-color-scheme: dark)') ? 'dark' : 'light',
                reduced_motion: media('(prefers-reduced-motion: reduce)'),
            },
            gpu: this.getGpuInfo(),
            user_agent_data: await this.getUserAgentData(),
        };
    },

    getGpuInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return null;

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const gpu = {
                vendor: gl.getParameter(debugInfo ? debugInfo.UNMASKED_VENDOR_WEBGL : gl.VENDOR),
                renderer: gl.getParameter(debugInfo ? debugInfo.UNMASKED_RENDERER_WEBGL : gl.RENDERER),
            };
            gl.getExtension('WEBGL_lose_context')?.loseContext();
            return gpu;
        } catch (error) {
            return null;
        }
    },

    /**
     * Client Hints: модель устройства, версия ОС, архитектура (Chromium-браузеры)
     */
    async getUserAgentData() {
        const uaData = window.navigator.userAgentData;
        if (!uaData) return null;

        const data = { brands: uaData.brands, mobile: uaData.mobile, platform: uaData.platform };
        try {
            Object.assign(data, await uaData.getHighEntropyValues([
                'architecture', 'bitness', 'model', 'platformVersion', 'fullVersionList',
            ]));
        } catch (error) {
            // Браузер вправе отказать в расширенных данных
        }
        return data;
    },

    // ---------- Отправка ----------

    scheduleFlush() {
        if (this.flushTimer) return;
        this.flushTimer = setTimeout(() => this.flush(), this.FLUSH_DELAY);
    },

    flush() {
        clearTimeout(this.flushTimer);
        this.flushTimer = null;
        while (this.queue.length) {
            this.send(this.queue.splice(0, this.MAX_EVENTS_PER_REQUEST));
        }
    },

    async send(events, client = null) {
        if (!this.started) return;

        const body = { events };
        if (client) body.client = client;

        try {
            const response = await this.post(this.config.urls.collect, body);
            if (response.status === 403) {
                const result = await response.json().catch(() => ({}));
                if (result.error === 'consent_required') {
                    // На сервере согласия нет (например, данные удалены) — спрашиваем заново
                    this.stop();
                    this.config.consent = null;
                    this.showBanner(false);
                }
            }
        } catch (error) {
            // Сеть недоступна — событие теряется, для статистики это некритично
        }
    },

    post(url, data) {
        return fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            // keepalive позволяет запросу завершиться, даже если страницу закрыли
            keepalive: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
            body: JSON.stringify(data),
        });
    },

    getCsrfToken() {
        // Cookie актуальнее meta-тега: токен меняется при входе в аккаунт в другой вкладке
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        if (match) return decodeURIComponent(match[1]);
        return document.querySelector('meta[name="csrf-token"]')?.content || '';
    },

    generateId() {
        if (window.crypto?.randomUUID) return window.crypto.randomUUID();
        return `${Date.now().toString(16)}-${Math.random().toString(16).slice(2)}`;
    },

    // ---------- Страница «Конфиденциальность» ----------

    initPrivacyPanel() {
        const panel = document.getElementById('privacy-panel');
        if (!panel) return;

        const status = panel.querySelector('[data-privacy-status]');
        const output = panel.querySelector('[data-privacy-output]');

        const renderStatus = () => {
            const consent = this.config.consent;
            if (!consent) {
                status.textContent = 'Вы ещё не сделали выбор — данные для аналитики не собираются.';
            } else if (consent.analytics) {
                status.textContent = 'Вы разрешили сбор данных для аналитики.';
            } else {
                status.textContent = 'Вы отказались от сбора данных для аналитики — собираются только необходимые cookie.';
            }
        };
        renderStatus();
        document.addEventListener('tracking:consent-changed', renderStatus);

        panel.addEventListener('click', async (event) => {
            const button = event.target.closest('[data-privacy-action]');
            if (!button) return;

            switch (button.dataset.privacyAction) {
                case 'change':
                    this.showBanner(true);
                    break;
                case 'show': {
                    try {
                        const response = await fetch(this.config.urls.myData, { credentials: 'same-origin' });
                        const data = await response.json();
                        output.textContent = data.visitor
                            ? JSON.stringify(data, null, 2)
                            : 'О вас ничего не сохранено.';
                        output.hidden = false;
                    } catch (error) {
                        window.NotificationManager?.error('Не удалось загрузить данные, попробуйте ещё раз');
                    }
                    break;
                }
                case 'delete': {
                    if (!window.confirm('Удалить все собранные о вас данные? Сбор данных будет отключён.')) return;
                    const response = await this.post(this.config.urls.forget, {});
                    if (response.ok) {
                        this.stop();
                        window.location.reload();
                    } else {
                        window.NotificationManager?.error('Не удалось удалить данные, попробуйте ещё раз');
                    }
                    break;
                }
            }
        });
    },
};

document.addEventListener('DOMContentLoaded', () => Tracking.init());
