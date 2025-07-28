
/**
 * NSPI HEMIS - Main JavaScript File
 * Bootstrap 5.3.2 based functionality with enhanced mobile responsivity
 */

// Global state management
const AppState = {
    isMobile: window.innerWidth <= 768,
    isTablet: window.innerWidth > 768 && window.innerWidth <= 1024,
    currentBreakpoint: getCurrentBreakpoint(),
    components: {}
};

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
    initializeAnimations();
    initializeFormValidation();
    initializeSurveySystem();
    initializeResponsiveHandlers();
    initializeTouchSupport();
});

// Window resize handler for responsive updates
window.addEventListener('resize', debounce(function() {
    AppState.isMobile = window.innerWidth <= 768;
    AppState.isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
    AppState.currentBreakpoint = getCurrentBreakpoint();
    handleResponsiveChanges();
}, 250));

// Get current Bootstrap breakpoint
function getCurrentBreakpoint() {
    const width = window.innerWidth;
    if (width < 576) return 'xs';
    if (width < 768) return 'sm';
    if (width < 992) return 'md';
    if (width < 1200) return 'lg';
    if (width < 1400) return 'xl';
    return 'xxl';
}

// Initialize all Bootstrap components with mobile optimization
function initializeComponents() {
    // Initialize tooltips with mobile-friendly settings
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: AppState.isMobile ? 'click' : 'hover',
            placement: AppState.isMobile ? 'top' : 'auto'
        });
    });

    // Initialize popovers with responsive settings
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: AppState.isMobile ? 'click' : 'hover',
            placement: AppState.isMobile ? 'top' : 'auto'
        });
    });

    // Initialize modals with mobile optimization
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(function(modalElement) {
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: true
        });
        
        // Mobile modal adjustments
        if (AppState.isMobile) {
            modalElement.classList.add('modal-fullscreen-sm-down');
        }
    });

    // Initialize offcanvas for mobile navigation
    const offcanvasElements = document.querySelectorAll('.offcanvas');
    offcanvasElements.forEach(function(offcanvasElement) {
        new bootstrap.Offcanvas(offcanvasElement);
    });
}

// Enhanced animation system with mobile considerations
function initializeAnimations() {
    // Reduce animations on mobile for better performance
    const shouldAnimate = !AppState.isMobile || !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (!shouldAnimate) return;

    // Fade in elements
    const observerOptions = {
        threshold: AppState.isMobile ? 0.05 : 0.1,
        rootMargin: AppState.isMobile ? '0px 0px -30px 0px' : '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all fade-in elements
    document.querySelectorAll('.fade-in-on-scroll').forEach(function(el) {
        observer.observe(el);
    });

    // Card hover effects
    document.querySelectorAll('.card-custom').forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Survey System
function initializeSurveySystem() {
    const surveyContainer = document.getElementById('survey-form-root');
    if (surveyContainer && typeof surveyData !== 'undefined') {
        renderSurveyForm(surveyData, surveyContainer);
    }
}

// Survey Form Renderer
function renderSurveyForm(data, container) {
    let currentQuestionIndex = 0;
    const answers = {};
    
    // Create form structure
    const formHTML = `
        <div class="survey-container mx-auto">
            <!-- Progress Bar -->
            <div class="mb-4">
                <div class="progress progress-custom">
                    <div class="progress-bar progress-bar-custom" role="progressbar" style="width: 0%" id="surveyProgress"></div>
                </div>
                <div class="text-center mt-2">
                    <small class="text-muted">Savol <span id="currentQuestion">1</span> / <span id="totalQuestions">${data.questions.length}</span></small>
                </div>
            </div>
            
            <!-- Questions Container -->
            <div id="questionsContainer"></div>
            
            <!-- Navigation Buttons -->
            <div class="d-flex justify-content-between mt-4">
                <button type="button" class="btn btn-outline-secondary" id="prevBtn" onclick="previousQuestion()" disabled>
                    <i class="fas fa-arrow-left me-2"></i>Oldingi
                </button>
                <button type="button" class="btn btn-primary" id="nextBtn" onclick="nextQuestion()">
                    Keyingi<i class="fas fa-arrow-right ms-2"></i>
                </button>
                <button type="button" class="btn btn-success d-none" id="submitBtn" onclick="submitSurvey()">
                    <i class="fas fa-check me-2"></i>Yuborish
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = formHTML;
    
    // Render first question
    renderQuestion(data.questions[currentQuestionIndex]);
    updateProgress();
    
    // Global functions for navigation
    window.nextQuestion = function() {
        if (validateCurrentQuestion()) {
            currentQuestionIndex++;
            if (currentQuestionIndex < data.questions.length) {
                renderQuestion(data.questions[currentQuestionIndex]);
                updateProgress();
            }
        }
    };
    
    window.previousQuestion = function() {
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            renderQuestion(data.questions[currentQuestionIndex]);
            updateProgress();
        }
    };
    
    window.submitSurvey = function() {
        console.log('Submit survey called');
        console.log('Current answers:', answers);
        console.log('Questions data:', data.questions);
        
        if (validateAllAnswers()) {
            console.log('Validation passed, sending data...');
            showLoadingSpinner();
            sendSurveyData(answers);
        } else {
            console.log('Validation failed');
        }
    };
    
    function renderQuestion(question) {
        const questionsContainer = document.getElementById('questionsContainer');
        let questionHTML = `
            <div class="question-card fade-in">
                <div class="question-header">
                    <h5 class="question-title mb-0">
                        ${question.text}
                        ${question.is_required ? '<span class="question-required">*</span>' : ''}
                    </h5>
                </div>
                <div class="question-body">
        `;
        
        switch (question.question_type) {
            case 'text':
                questionHTML += `
                    <textarea class="form-control" rows="4" placeholder="Javobingizni yozing..." 
                              id="answer_${question.id}" ${question.is_required ? 'required' : ''}></textarea>
                `;
                break;
                
            case 'single_choice':
                question.choices.forEach(function(choice) {
                    questionHTML += `
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="radio" name="answer_${question.id}" 
                                   id="choice_${choice.id}" value="${choice.id}" ${question.is_required ? 'required' : ''}>
                            <label class="form-check-label" for="choice_${choice.id}">
                                ${choice.text}
                            </label>
                        </div>
                    `;
                });
                break;
                
            case 'multiple_choice':
                question.choices.forEach(function(choice) {
                    questionHTML += `
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="answer_${question.id}[]" 
                                   id="choice_${choice.id}" value="${choice.id}">
                            <label class="form-check-label" for="choice_${choice.id}">
                                ${choice.text}
                            </label>
                        </div>
                    `;
                });
                break;
        }
        
        questionHTML += `
                </div>
            </div>
        `;
        
        questionsContainer.innerHTML = questionHTML;
        
        // Restore previous answer if exists
        restoreAnswer(question);
    }
    
    function updateProgress() {
        const progress = ((currentQuestionIndex + 1) / data.questions.length) * 100;
        document.getElementById('surveyProgress').style.width = progress + '%';
        document.getElementById('currentQuestion').textContent = currentQuestionIndex + 1;
        
        // Update navigation buttons
        document.getElementById('prevBtn').disabled = currentQuestionIndex === 0;
        
        if (currentQuestionIndex === data.questions.length - 1) {
            document.getElementById('nextBtn').classList.add('d-none');
            document.getElementById('submitBtn').classList.remove('d-none');
        } else {
            document.getElementById('nextBtn').classList.remove('d-none');
            document.getElementById('submitBtn').classList.add('d-none');
        }
    }
    
    function validateCurrentQuestion() {
        const question = data.questions[currentQuestionIndex];
        
        switch (question.question_type) {
            case 'text':
                const textAnswer = document.getElementById(`answer_${question.id}`).value.trim();
                if (question.is_required && !textAnswer) {
                    showError('Bu savolga javob berish majburiy!');
                    return false;
                }
                // Majburiy bo'lmagan savollar uchun ham javobni saqlash
                if (textAnswer) {
                    answers[question.id] = textAnswer;
                } else {
                    delete answers[question.id]; // Bo'sh javobni o'chirish
                }
                break;
                
            case 'single_choice':
                const selectedRadio = document.querySelector(`input[name="answer_${question.id}"]:checked`);
                if (question.is_required && !selectedRadio) {
                    showError('Iltimos, variantlardan birini tanlang!');
                    return false;
                }
                // Javobni saqlash
                if (selectedRadio) {
                    answers[question.id] = selectedRadio.value;
                } else {
                    delete answers[question.id];
                }
                break;
                
            case 'multiple_choice':
                const checkedBoxes = document.querySelectorAll(`input[name="answer_${question.id}[]"]:checked`);
                if (question.is_required && checkedBoxes.length === 0) {
                    showError('Kamida bitta variantni tanlang!');
                    return false;
                }
                // Javobni saqlash
                if (checkedBoxes.length > 0) {
                    answers[question.id] = Array.from(checkedBoxes).map(cb => cb.value);
                } else {
                    delete answers[question.id];
                }
                break;
        }
        
        return true;
    }
    
    function restoreAnswer(question) {
        if (!answers[question.id]) return;
        
        switch (question.question_type) {
            case 'text':
                document.getElementById(`answer_${question.id}`).value = answers[question.id];
                break;
                
            case 'single_choice':
                const radio = document.querySelector(`input[name="answer_${question.id}"][value="${answers[question.id]}"]`);
                if (radio) radio.checked = true;
                break;
                
            case 'multiple_choice':
                answers[question.id].forEach(function(value) {
                    const checkbox = document.querySelector(`input[name="answer_${question.id}[]"][value="${value}"]`);
                    if (checkbox) checkbox.checked = true;
                });
                break;
        }
    }
    
    function validateAllAnswers() {
        // Oxirgi savolni ham validate qilish
        if (!validateCurrentQuestion()) {
            return false;
        }
        
        // Barcha majburiy savollar uchun javob borligini tekshirish
        for (let i = 0; i < data.questions.length; i++) {
            const question = data.questions[i];
            if (question.is_required) {
                const answer = answers[question.id];
                if (!answer || 
                    (typeof answer === 'string' && !answer.trim()) || 
                    (Array.isArray(answer) && answer.length === 0)) {
                    showError(`${i + 1}-savolga javob berilmagan!`);
                    // Savolga o'tish
                    currentQuestionIndex = i;
                    renderQuestion(data.questions[currentQuestionIndex]);
                    updateProgress();
                    return false;
                }
            }
        }
        return true;
    }
    
    function sendSurveyData(surveyAnswers) {
        // URL'ni to'g'rilash - API endpoint ishlatamiz
        const currentPath = window.location.pathname; // /surveys/1/
        const surveyId = currentPath.split('/').filter(x => x)[1]; // "1"
        const url = `/api/surveys/${surveyId}/submit/`;
        
        const formData = {
            answers: surveyAnswers
        };
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof csrfToken !== 'undefined' ? csrfToken : getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            hideLoadingSpinner();
            if (data.status === 'success') {
                showSuccess('So\'rovnoma muvaffaqiyatli yuborildi!');
                setTimeout(() => {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.href = '/surveys/';
                    }
                }, 2000);
            } else {
                showError(data.message || 'Xatolik yuz berdi!');
            }
        })
        .catch(error => {
            hideLoadingSpinner();
            showError('Server bilan bog\'lanishda xatolik!');
            console.error('Error:', error);
        });
    }
}

// Utility functions
function showError(message) {
    showAlert(message, 'danger');
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function showAlert(message, type) {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertAdjacentHTML('afterbegin', alertHTML);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }
    }, 5000);
}

function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.id = 'loadingSpinner';
    spinner.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
    spinner.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    spinner.style.zIndex = '9999';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Yuklanmoqda...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

function hideLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

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

// Enhanced responsive handlers
function initializeResponsiveHandlers() {
    // Mobile-specific navbar behavior
    const navbar = document.querySelector('.navbar');
    if (navbar && AppState.isMobile) {
        // Auto-collapse navbar on mobile after clicking a link
        const navLinks = navbar.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                    bootstrap.Collapse.getInstance(navbarCollapse).hide();
                }
            });
        });
    }

    // Responsive table handling
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (AppState.isMobile) {
            table.style.overflowX = 'auto';
            table.style.WebkitOverflowScrolling = 'touch';
        }
    });

    // Mobile form optimizations
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        if (AppState.isMobile) {
            // Scroll to first error on mobile
            form.addEventListener('submit', function(e) {
                setTimeout(() => {
                    const firstError = form.querySelector('.is-invalid');
                    if (firstError) {
                        firstError.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                    }
                }, 100);
            });
        }
    });
}

// Touch support for better mobile experience
function initializeTouchSupport() {
    if (!('ontouchstart' in window)) return;

    // Add touch-friendly hover effects
    const hoverElements = document.querySelectorAll('.card, .btn, .nav-link');
    hoverElements.forEach(element => {
        element.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        
        element.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('touch-active');
            }, 150);
        });
    });

    // Prevent double-tap zoom on buttons
    const buttons = document.querySelectorAll('button, .btn');
    buttons.forEach(button => {
        button.addEventListener('touchend', function(e) {
            e.preventDefault();
            this.click();
        });
    });
}

// Handle responsive changes on window resize
function handleResponsiveChanges() {
    // Update tooltip/popover settings
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(element => {
        const tooltip = bootstrap.Tooltip.getInstance(element);
        if (tooltip) {
            tooltip.dispose();
            new bootstrap.Tooltip(element, {
                trigger: AppState.isMobile ? 'click' : 'hover',
                placement: AppState.isMobile ? 'top' : 'auto'
            });
        }
    });

    // Update card layouts for mobile
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        if (AppState.isMobile) {
            card.classList.add('mobile-optimized');
        } else {
            card.classList.remove('mobile-optimized');
        }
    });

    // Trigger custom responsive event
    window.dispatchEvent(new CustomEvent('responsiveChange', {
        detail: { breakpoint: AppState.currentBreakpoint, isMobile: AppState.isMobile }
    }));
}

// Utility function for debouncing
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Performance optimization for mobile
if (AppState.isMobile) {
    // Reduce animation duration
    document.documentElement.style.setProperty('--bs-transition-duration', '0.2s');
    
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
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
        images.forEach(img => imageObserver.observe(img));
    }
}

// Tab System for Dashboard
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.nav-tabs-custom .nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('show', 'active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Show corresponding tab pane
            const targetId = this.getAttribute('data-bs-target');
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
            }
        });
    });
}

// Floating icons animation
function createFloatingIcons() {
    const container = document.querySelector('.floating-elements');
    if (!container) return;
    
    const icons = ['fas fa-book', 'fas fa-graduation-cap', 'fas fa-trophy', 'fas fa-chart-line', 'fas fa-lightbulb'];
    
    for (let i = 0; i < 15; i++) {
        const icon = document.createElement('div');
        icon.className = 'floating-icon';
        icon.innerHTML = `<i class="${icons[Math.floor(Math.random() * icons.length)]}"></i>`;
        
        // Random position
        icon.style.left = Math.random() * 100 + 'vw';
        icon.style.animationDelay = Math.random() * 20 + 's';
        icon.style.animationDuration = (15 + Math.random() * 10) + 's';
        
        container.appendChild(icon);
    }
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    createFloatingIcons();
});
