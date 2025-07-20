// ObsidianTime Main JavaScript

$(document).ready(function() {
    // CSRF token setup for AJAX
    function getCookie(name) {
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
    
    const csrftoken = getCookie('csrftoken');
    
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        var target = $(this.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 80
            }, 1000);
        }
    });

    // Auto-dismiss alerts after 5 seconds
    $('.alert').each(function() {
        const alert = $(this);
        setTimeout(function() {
            alert.fadeOut();
        }, 5000);
    });

    // Like/Dislike functionality for memes
    $(document).on('click', '.like-btn', function(e) {
        e.preventDefault();
        const btn = $(this);
        const memeId = btn.data('meme-id');
        const url = btn.data('url');
        
        $.post(url, function(data) {
            // Update like button
            btn.toggleClass('liked', data.liked);
            btn.find('.like-count').text(data.likes_count);
            
            // Update dislike button
            const dislikeBtn = $(`.dislike-btn[data-meme-id="${memeId}"]`);
            dislikeBtn.removeClass('disliked');
            dislikeBtn.find('.dislike-count').text(data.dislikes_count);
            
            // Update rating
            $(`.rating[data-meme-id="${memeId}"]`).text(data.rating);
        });
    });

    $(document).on('click', '.dislike-btn', function(e) {
        e.preventDefault();
        const btn = $(this);
        const memeId = btn.data('meme-id');
        const url = btn.data('url');
        
        $.post(url, function(data) {
            // Update dislike button
            btn.toggleClass('disliked', data.disliked);
            btn.find('.dislike-count').text(data.dislikes_count);
            
            // Update like button
            const likeBtn = $(`.like-btn[data-meme-id="${memeId}"]`);
            likeBtn.removeClass('liked');
            likeBtn.find('.like-count').text(data.likes_count);
            
            // Update rating
            $(`.rating[data-meme-id="${memeId}"]`).text(data.rating);
        });
    });

    // Like functionality for quotes
    $(document).on('click', '.quote-like-btn', function(e) {
        e.preventDefault();
        const btn = $(this);
        const url = btn.data('url');
        
        $.post(url, function(data) {
            btn.toggleClass('liked', data.liked);
            btn.find('.like-count').text(data.likes_count);
            
            if (data.liked) {
                btn.find('i').removeClass('far').addClass('fas');
            } else {
                btn.find('i').removeClass('fas').addClass('far');
            }
        });
    });

    // Image preview for file uploads
    $(document).on('change', 'input[type="file"]', function(e) {
        const file = e.target.files[0];
        const preview = $(this).siblings('.image-preview');
        
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                if (preview.length === 0) {
                    $(this).after(`
                        <div class="image-preview mt-2">
                            <img src="${e.target.result}" class="img-thumbnail" style="max-height: 200px;">
                        </div>
                    `);
                } else {
                    preview.html(`<img src="${e.target.result}" class="img-thumbnail" style="max-height: 200px;">`);
                }
            }.bind(this);
            reader.readAsDataURL(file);
        }
    });

    // Confirmation dialogs
    $(document).on('click', '.confirm-action', function(e) {
        const message = $(this).data('confirm') || 'Вы уверены?';
        if (!confirm(message)) {
            e.preventDefault();
        }
    });

    // Tooltip initialization
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Copy to clipboard functionality
    $(document).on('click', '.copy-to-clipboard', function(e) {
        e.preventDefault();
        const text = $(this).data('text') || $(this).text();
        
        navigator.clipboard.writeText(text).then(function() {
            // Show success message
            const btn = $(e.target);
            const originalText = btn.text();
            btn.text('Скопировано!');
            setTimeout(() => btn.text(originalText), 2000);
        });
    });

    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
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

    // Search functionality with debouncing
    let searchTimeout;
    $(document).on('input', '.search-input', function() {
        const input = $(this);
        const query = input.val();
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            if (query.length >= 3 || query.length === 0) {
                // Trigger search
                input.closest('form').submit();
            }
        }, 500);
    });

    // Dark mode toggle (если будет нужен)
    $(document).on('click', '.dark-mode-toggle', function() {
        $('body').toggleClass('dark-mode');
        localStorage.setItem('darkMode', $('body').hasClass('dark-mode'));
    });

    // Load dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        $('body').addClass('dark-mode');
    }

    // Animate elements on scroll
    function animateOnScroll() {
        $('.animate-on-scroll').each(function() {
            const element = $(this);
            const elementTop = element.offset().top;
            const elementBottom = elementTop + element.outerHeight();
            const viewportTop = $(window).scrollTop();
            const viewportBottom = viewportTop + $(window).height();
            
            if (elementBottom > viewportTop && elementTop < viewportBottom) {
                element.addClass('animated');
            }
        });
    }

    $(window).on('scroll', animateOnScroll);
    animateOnScroll(); // Run on page load

    console.log('ObsidianTime - Ready to rock! 🚀');
}); 