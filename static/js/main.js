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

    // Poll voting
    $(document).on('click', '.poll-option-btn', function(e) {
        e.preventDefault();
        const btn = $(this);
        const url = btn.data('url');
        const pollContainer = btn.closest('.poll-container');
        
        $.post(url, function(data) {
            // Update poll results
            updatePollDisplay(pollContainer, data);
        });
    });

    function updatePollDisplay(container, data) {
        // Update total votes
        container.find('.poll-total-votes').text(data.total_votes + ' голосов');
        
        // Update each option
        data.options.forEach(function(option) {
            const optionElement = container.find(`[data-option-id="${option.id}"]`);
            optionElement.find('.poll-votes').text(option.vote_count);
            optionElement.find('.poll-percentage').text(option.vote_percentage + '%');
            
            // Update progress bar
            const progressBar = optionElement.find('.poll-progress-bar');
            progressBar.css('width', option.vote_percentage + '%');
        });
    }

    // Chat auto-refresh
    let lastMessageId = 0;
    
    function refreshChat() {
        if (window.location.pathname.includes('/chat/')) {
            $.get('/chat/api/messages/', {last_id: lastMessageId}, function(data) {
                if (data.messages.length > 0) {
                    data.messages.forEach(function(message) {
                        addMessageToChat(message);
                    });
                    lastMessageId = data.last_id;
                    scrollChatToBottom();
                }
            });
        }
    }

    function addMessageToChat(message) {
        const chatContainer = $('.chat-messages');
        if (chatContainer.length === 0) return;
        
        let messageHtml = `
            <div class="message-item mb-2 p-2 border-bottom fade-in">
                <div class="d-flex justify-content-between">
                    <strong class="text-primary">${message.author}</strong>
                    <small class="text-muted">${message.created_at}</small>
                </div>
                <div class="message-content">
        `;
        
        if (message.message_type === 'poll' && message.poll) {
            messageHtml += `
                <div class="poll-container">
                    <h6><i class="fas fa-poll"></i> ${message.poll.question}</h6>
                    <div class="poll-options">
            `;
            
            message.poll.options.forEach(function(option) {
                messageHtml += `
                    <div class="poll-option" data-option-id="${option.id}">
                        <div class="d-flex justify-content-between">
                            <span>${option.text}</span>
                            <span class="poll-votes">${option.vote_count}</span>
                        </div>
                        <div class="poll-progress">
                            <div class="poll-progress-bar" style="width: ${option.vote_percentage}%"></div>
                        </div>
                    </div>
                `;
            });
            
            messageHtml += `
                    </div>
                    <div class="text-center mt-2">
                        <small class="text-muted poll-total-votes">${message.poll.total_votes} голосов</small>
                    </div>
                </div>
            `;
        } else {
            messageHtml += message.content;
        }
        
        messageHtml += `
                </div>
            </div>
        `;
        
        chatContainer.append(messageHtml);
    }

    function scrollChatToBottom() {
        const chatContainer = $('.chat-messages');
        if (chatContainer.length > 0) {
            chatContainer.scrollTop(chatContainer[0].scrollHeight);
        }
    }

    // Auto-refresh chat every 3 seconds
    if (window.location.pathname.includes('/chat/')) {
        setInterval(refreshChat, 3000);
        
        // Get initial last message ID
        const lastMessage = $('.message-item').last();
        if (lastMessage.length > 0) {
            lastMessageId = lastMessage.data('message-id') || 0;
        }
    }

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