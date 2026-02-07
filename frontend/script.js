
const API_BASE_URL = (() => {
    if (window.CLARITY_API_BASE_URL) {
        return window.CLARITY_API_BASE_URL;
    }
    if (window.location.protocol.startsWith('http')) {
        return `${window.location.origin}/api`;
    }
    return 'http://localhost:5000/api';
})();

document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyze-btn');
    const urlInput = document.getElementById('url-input');
    const textInput = document.getElementById('text-input');
    const pdfInput = document.getElementById('pdf-input');
    const purposeInput = document.getElementById('purpose-input');
    const loading = document.getElementById('loading');

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const url = urlInput?.value.trim();
            const text = textInput?.value.trim();
            const pdfFile = pdfInput?.files[0];
            const purpose = purposeInput?.value.trim();

            const inputCount = [Boolean(url), Boolean(text), Boolean(pdfFile)].filter(Boolean).length;

            if (inputCount === 0) {
                showNotification('Please provide an article URL, text, or PDF file to analyze.', 'warning');
                return;
            }
            if (inputCount > 1) {
                showNotification('Use only one input method at a time (URL, text, or PDF).', 'warning');
                return;
            }

            showLoadingAnimation();
            analyzeBtn.disabled = true;

            try {
                let result;
                if (url) {
                    result = await analyzeUrl(url, purpose);
                } else if (text) {
                    result = await analyzeText(text, purpose);
                } else {
                    result = await analyzePdf(pdfFile, purpose);
                }

                result.hasPurpose = Boolean(purpose);

                sessionStorage.setItem('analysisResult', JSON.stringify(result));

                await new Promise(resolve => setTimeout(resolve, 450));

                window.location.href = 'results.html';

            } catch (error) {
                console.error('Analysis error:', error);
                showNotification('Error analyzing article: ' + error.message, 'error');
                hideLoadingAnimation();
                analyzeBtn.disabled = false;
            }
        });
    }
});

function showLoadingAnimation() {
    const loading = document.getElementById('loading');
    const loadingMessage = document.getElementById('loading-message');
    
    const svg = loading.querySelector('.progress-ring');
    if (svg && !svg.querySelector('defs')) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', 'blueGradient');
        gradient.setAttribute('x1', '0%');
        gradient.setAttribute('y1', '0%');
        gradient.setAttribute('x2', '100%');
        gradient.setAttribute('y2', '100%');
        
        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop1.setAttribute('offset', '0%');
        stop1.setAttribute('style', 'stop-color:#2563eb;stop-opacity:1');
        
        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop2.setAttribute('offset', '100%');
        stop2.setAttribute('style', 'stop-color:#60a5fa;stop-opacity:1');
        
        gradient.appendChild(stop1);
        gradient.appendChild(stop2);
        defs.appendChild(gradient);
        svg.insertBefore(defs, svg.firstChild);
    }
    
    loading.style.display = 'flex';
    
    const messages = [
        'Initializing analysis...',
        'Extracting article content...',
        'Running credibility checks...',
        'Analyzing writing style and bias...',
        'Evaluating sources and citations...',
        'Computing final scores...',
        'Almost done...'
    ];
    
    let messageIndex = 0;
    const messageInterval = setInterval(() => {
        if (messageIndex < messages.length) {
            loadingMessage.textContent = messages[messageIndex];
            loadingMessage.style.animation = 'none';
            setTimeout(() => {
                loadingMessage.style.animation = 'fadeIn 0.5s ease-out';
            }, 10);
            messageIndex++;
        }
    }, 3000);
    
    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4')
    ];
    
    let stepIndex = 0;
    const stepInterval = setInterval(() => {
        if (stepIndex < steps.length) {
            steps[stepIndex].classList.add('active');
            stepIndex++;
        } else {
            stepIndex = 0;
            steps.forEach(step => step.classList.remove('active'));
        }
    }, 2000);
    
    loading.dataset.messageInterval = messageInterval;
    loading.dataset.stepInterval = stepInterval;
}

function hideLoadingAnimation() {
    const loading = document.getElementById('loading');
    
    if (loading.dataset.messageInterval) {
        clearInterval(parseInt(loading.dataset.messageInterval));
    }
    if (loading.dataset.stepInterval) {
        clearInterval(parseInt(loading.dataset.stepInterval));
    }
    
    loading.style.display = 'none';
}

async function analyzeUrl(url, purpose = '') {
    const response = await fetch(`${API_BASE_URL}/analyze/url`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, purpose }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to analyze URL');
    }

    return await response.json();
}

async function analyzeText(text, purpose = '') {
    const response = await fetch(`${API_BASE_URL}/analyze/text`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, purpose }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to analyze text');
    }

    return await response.json();
}

async function analyzePdf(file, purpose = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (purpose) {
        formData.append('purpose', purpose);
    }

    const response = await fetch(`${API_BASE_URL}/analyze/pdf`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to analyze PDF');
    }

    return await response.json();
}

function showNotification(message, type = 'info') {
    const existingNotif = document.querySelector('.notification');
    if (existingNotif) {
        existingNotif.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = type === 'error' ? 
        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>` :
        type === 'warning' ?
        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>` :
        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>`;

    notification.innerHTML = `
        ${icon}
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        .notification {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 1000;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 400px;
        }
        
        .notification.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        .notification-info {
            background: linear-gradient(135deg, #dbeafe, #bfdbfe);
            color: #1e40af;
            border: 2px solid #60a5fa;
        }
        
        .notification-warning {
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            color: #92400e;
            border: 2px solid #fbbf24;
        }
        
        .notification-error {
            background: linear-gradient(135deg, #fee2e2, #fecaca);
            color: #991b1b;
            border: 2px solid #f87171;
        }
        
        .notification svg {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }
        
        .notification span {
            font-weight: 600;
            font-size: 14px;
        }
    `;
    document.head.appendChild(style);
}

document.addEventListener('DOMContentLoaded', function() {
    
    const inputs = document.querySelectorAll('input[type="text"], textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            if (this.parentElement.classList.contains('input-wrapper')) {
                this.parentElement.classList.add('focused');
            }
        });
        
        input.addEventListener('blur', function() {
            if (this.parentElement.classList.contains('input-wrapper')) {
                this.parentElement.classList.remove('focused');
            }
        });
    });
    
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const glow = document.createElement('div');
            glow.className = 'card-glow';
            glow.style.left = x + 'px';
            glow.style.top = y + 'px';
            this.appendChild(glow);
            
            setTimeout(() => {
                glow.remove();
            }, 600);
        });
    });
    
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', function(e) {
        mouseX = e.clientX / window.innerWidth;
        mouseY = e.clientY / window.innerHeight;
    });
    
    function animateOrbs() {
        const orbs = document.querySelectorAll('.orb');
        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 0.5;
            const x = (mouseX - 0.5) * speed * 20;
            const y = (mouseY - 0.5) * speed * 20;
            orb.style.transform = `translate(${x}px, ${y}px)`;
        });
        requestAnimationFrame(animateOrbs);
    }
    
    if (document.querySelectorAll('.orb').length > 0) {
        animateOrbs();
    }
    
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function(e) {
            const panels = document.querySelectorAll('.left-panel, .right-panel');
            panels.forEach((panel, index) => {
                panel.style.animation = index === 0 ? 'slideOutLeft 0.4s ease-in' : 'slideOutRight 0.4s ease-in';
            });
        });
    }
    
    console.log('✨ Shared utilities initialized');
});

if (!document.querySelector('#card-glow-styles')) {
    const cardGlowStyle = document.createElement('style');
    cardGlowStyle.id = 'card-glow-styles';
    cardGlowStyle.textContent = `
        .card-glow {
            position: absolute;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(31, 111, 235, 0.3), transparent);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            animation: glowExpand 0.6s ease-out;
            z-index: 0;
        }
        
        @keyframes glowExpand {
            from {
                width: 0;
                height: 0;
                opacity: 1;
            }
            to {
                width: 200px;
                height: 200px;
                opacity: 0;
            }
        }
        
        @keyframes slideOutLeft {
            to {
                opacity: 0;
                transform: translateX(-50px);
            }
        }
        
        @keyframes slideOutRight {
            to {
                opacity: 0;
                transform: translateX(50px);
            }
        }
    `;
    document.head.appendChild(cardGlowStyle);
}