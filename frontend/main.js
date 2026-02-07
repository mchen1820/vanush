// ============================================
// INDEX PAGE - Form submission and analysis
// ============================================

// API Configuration
const API_BASE_URL = (() => {
    if (window.CLARITY_API_BASE_URL) {
        return window.CLARITY_API_BASE_URL;
    }
    if (window.location.protocol.startsWith('http')) {
        return `${window.location.origin}/api`;
    }
    return 'http://localhost:5000/api';
})();

// ============================================
// FORM SUBMISSION & ANALYSIS
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyze-btn');
    const urlInput = document.getElementById('url-input');
    const textInput = document.getElementById('text-input');
    const pdfInput = document.getElementById('pdf-input');
    const fileText = document.querySelector('.file-text');
    const purposeInput = document.getElementById('purpose-input');
    const loading = document.getElementById('loading');
    const defaultFileLabel = 'Choose PDF file';

    if (pdfInput && fileText) {
        pdfInput.addEventListener('change', function() {
            const selected = this.files && this.files[0];
            if (selected) {
                fileText.textContent = selected.name;
                fileText.title = selected.name;
                if (urlInput) urlInput.value = '';
                if (textInput) textInput.value = '';
            } else {
                fileText.textContent = defaultFileLabel;
                fileText.title = '';
            }
        });
    }

    if (urlInput) {
        urlInput.addEventListener('input', function() {
            if (this.value.trim().length > 0 && pdfInput) {
                pdfInput.value = '';
                if (fileText) {
                    fileText.textContent = defaultFileLabel;
                    fileText.title = '';
                }
            }
        });
    }

    if (textInput) {
        textInput.addEventListener('input', function() {
            if (this.value.trim().length > 0 && pdfInput) {
                pdfInput.value = '';
                if (fileText) {
                    fileText.textContent = defaultFileLabel;
                    fileText.title = '';
                }
            }
        });
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            // Determine which input method was used
            const url = urlInput?.value.trim();
            const text = textInput?.value.trim();
            const pdfFile = pdfInput?.files[0];
            const purpose = purposeInput?.value.trim();
            
            // Validate that at least one input is provided
            if (!url && !text && !pdfFile) {
                showNotification('Please provide an article URL, text, or PDF file to analyze.', 'warning');
                return;
            }

            // Show loading with animation
            showLoadingAnimation();
            analyzeBtn.disabled = true;

            try {
                let result;
                // Priority: PDF > URL > text
                if (pdfFile) {
                    result = await analyzePdf(pdfFile, purpose);
                } else if (url) {
                    result = await analyzeUrl(url, purpose);
                } else {
                    result = await analyzeText(text, purpose);
                }

                // Store results in sessionStorage
                sessionStorage.setItem('analysisResult', JSON.stringify(result));

                // Short delay so transition is visible after a real response.
                await new Promise(resolve => setTimeout(resolve, 450));

                // Redirect to results page
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

// ============================================
// MOCK DATA (Remove when backend is integrated)
// ============================================

function getMockAnalysisData(purpose = '') {
    return {
        metadata: {
            title: "The Future of Artificial Intelligence",
            author: "Jane Doe",
            date: "January 12, 2025",
            preview_text: "Artificial intelligence is rapidly transforming industries worldwide. Experts argue that while AI offers unprecedented efficiency, it also raises ethical concerns related to bias, transparency, and accountability..."
        },
        overall_credibility: 78,
        bias_check: {
            overall_score: 60,
            confidence_score: 85,
            summary: "Moderate linguistic bias detected in the article's framing and word choice. The tone shows some persuasive elements and selective emphasis favoring certain perspectives.",
            dominant_tone: "persuasive",
            bias_level: "Moderate Bias",
            key_indicators: [
                { example_text: "unprecedented efficiency", indicator_type: "emotionally loaded" },
                { example_text: "raises ethical concerns", indicator_type: "selective emphasis" }
            ],
            affected_topics: ["AI development", "Workplace automation"],
            recommendations: ["Include counterarguments", "Use more neutral language", "Present balanced perspectives"]
        },
        author_credibility: {
            overall_score: 65,
            confidence_score: 70,
            summary: "The author demonstrates relevant expertise in the field with professional credentials and a track record of quality work. However, some academic background in the subject matter would strengthen credibility further.",
            author_name: "Jane Doe",
            credentials: ["Professional journalist", "5+ years in tech writing"],
            expertise_areas: ["Technology", "AI/ML", "Innovation"],
            concerns: ["Limited academic background in the subject"]
        },
        evidence_check: {
            overall_score: 70,
            confidence_score: 75,
            summary: "The article presents several claims backed by research and data. Most major assertions are supported by credible sources, though some statements could benefit from additional citations.",
            claims_analyzed: 12,
            verified_claims: 8,
            questionable_claims: ["AI will replace all jobs by 2030", "100% efficiency improvement"],
            sources_quality: "Mix of peer-reviewed research and industry reports"
        },
        usefulness_check: {
            overall_score: purpose ? 85 : 82,
            confidence_score: 80,
            summary: purpose 
                ? `Highly relevant for your purpose: "${purpose}". The article provides practical insights and current information that directly applies to your needs.`
                : "Article provides practical insights for professionals and general readers interested in AI development.",
            target_audience: "Tech professionals, business leaders, general audience",
            practical_value: "High - provides actionable insights and current trends",
            actionability: "Moderate - concepts discussed can inform decision-making"
        },
        citation_check: {
            overall_score: 55,
            confidence_score: 65,
            summary: "The article includes citations from a mix of academic and industry sources. While key claims are referenced, some important assertions lack proper citations.",
            total_citations: 8,
            citation_quality: "Mix of academic and industry sources",
            missing_citations: ["Statistical claim about job displacement", "Expert opinion attribution"]
        },
        organization_check: {
            overall_score: 68,
            confidence_score: 85,
            summary: "The article follows a logical structure with clear introduction, body, and conclusion. Information flows well between sections, though some transitions could be smoother.",
            structure_quality: "Well-organized with clear sections",
            strengths: ["Clear introduction", "Logical progression", "Strong conclusion"],
            weaknesses: ["Some sections too brief", "Could use more subheadings"]
        },
        relevancy_check: {
            overall_score: 75,
            confidence_score: 90,
            summary: "Published recently with current information on the topic. The content addresses ongoing developments and contemporary issues in the field.",
            publication_date: "January 12, 2025",
            is_current: true,
            relevancy_notes: "Content is timely and addresses ongoing developments in the field"
        }
    };
}

// ============================================
// LOADING ANIMATION
// ============================================

function showLoadingAnimation() {
    const loading = document.getElementById('loading');
    const loadingMessage = document.getElementById('loading-message');
    
    // Inject SVG gradient definition
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
    
    // Animated messages
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
    
    // Animate steps
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
            // Loop back
            stepIndex = 0;
            steps.forEach(step => step.classList.remove('active'));
        }
    }, 2000);
    
    // Store intervals for cleanup
    loading.dataset.messageInterval = messageInterval;
    loading.dataset.stepInterval = stepInterval;
}

function hideLoadingAnimation() {
    const loading = document.getElementById('loading');
    
    // Clear intervals
    if (loading.dataset.messageInterval) {
        clearInterval(parseInt(loading.dataset.messageInterval));
    }
    if (loading.dataset.stepInterval) {
        clearInterval(parseInt(loading.dataset.stepInterval));
    }
    
    loading.style.display = 'none';
}

// ============================================
// API CALLS
// ============================================

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
    if (!file) {
        throw new Error('No PDF file selected.');
    }

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

// ============================================
// NOTIFICATION SYSTEM
// ============================================

function showNotification(message, type = 'info') {
    // Remove existing notification if any
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

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Auto remove
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Add notification styles dynamically if not already added
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
