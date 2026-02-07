
document.addEventListener('DOMContentLoaded', function() {
    loadAnalysisResults();
    initializeScoreModal();
    initializeDropdowns();
});

function loadAnalysisResults() {
    const resultsJson = sessionStorage.getItem('analysisResult');
    
    if (!resultsJson) {
        console.error('No analysis results found');
        window.location.href = 'index.html';
        return;
    }

    try {
        const results = JSON.parse(resultsJson);
        console.log('Analysis results:', results);
        
        updateMetadata(results.metadata);
        updateOverallScore(results.overall_credibility);
        updateIndividualScores(results);
        updateSummary(results);
        updateQuotes(results);
        loadRecommendedArticles(results);
        
        if (!results.hasPurpose) {
            hideUsefulnessScore();
        }
        
    } catch (error) {
        console.error('Error loading results:', error);
        window.location.href = 'index.html';
    }
}

function updateMetadata(metadata) {
    const titleElement = document.querySelector('.meta-item:nth-child(1) .meta-value');
    if (titleElement && metadata.title) {
        titleElement.textContent = metadata.title;
    }
    
    const authorElement = document.querySelector('.meta-item:nth-child(2) .meta-value');
    if (authorElement && metadata.author) {
        authorElement.textContent = metadata.author;
    }
    
    const dateElement = document.querySelector('.meta-item:nth-child(3) .meta-value');
    if (dateElement && metadata.date) {
        dateElement.textContent = metadata.date;
    }
    
    const previewElement = document.querySelector('.preview p');
    if (previewElement && metadata.preview_text) {
        previewElement.textContent = metadata.preview_text;
    }
}

function updateOverallScore(score) {
    const overallPie = document.querySelector('.overall-pie');
    const pieValue = document.querySelector('.pie-value');
    
    if (overallPie && pieValue) {
        overallPie.style.setProperty('--p', score);
        pieValue.textContent = score;
    }
    
    const scoreDescription = document.querySelector('.score-description');
    if (scoreDescription) {
        if (score >= 80) {
            scoreDescription.textContent = 'Excellent - Highly trustworthy and credible';
        } else if (score >= 65) {
            scoreDescription.textContent = 'Good - Generally trustworthy with minor concerns';
        } else if (score >= 50) {
            scoreDescription.textContent = 'Average - Use with caution and verify claims';
        } else if (score >= 35) {
            scoreDescription.textContent = 'Below Average - Significant credibility concerns';
        } else {
            scoreDescription.textContent = 'Poor - Not recommended as a reliable source';
        }
    }
}

function updateIndividualScores(results) {
    const scoreMapping = [
        { key: 'evidence_check', label: 'Evidence Quality Score' },
        { key: 'bias_check', label: 'Bias & Framing Score' },
        { key: 'relevancy_check', label: 'Date & Relevancy Score' },
        { key: 'citation_check', label: 'Citation Validity Score' },
        { key: 'author_credibility', label: 'Author & Publisher Score' },
        { key: 'usefulness_check', label: 'Usefulness Score' },
    ];
    
    const scoreCards = document.querySelectorAll('.score-card');
    
    scoreCards.forEach((card, index) => {
        if (index < scoreMapping.length) {
            const mapping = scoreMapping[index];
            const data = results[mapping.key];
            
            if (data && data.overall_score !== undefined) {
                const score = data.overall_score;
                
                const pie = card.querySelector('.pie');
                const pieText = card.querySelector('.pie-text');
                if (pie && pieText) {
                    pie.style.setProperty('--p', score);
                    pie.setAttribute('data-score', score);
                    pieText.textContent = `${score}%`;
                }
                
                const barFill = card.querySelector('.score-bar-fill');
                if (barFill) {
                    barFill.style.width = `${score}%`;
                }
                
                if (data.summary) {
                    card.setAttribute('data-explanation', data.summary);
                }
            }
        }
    });
}

function updateSummary(results) {
    const centralClaimElement = document.querySelector('.central-claim p');
    if (centralClaimElement && results.metadata && results.metadata.central_claim) {
        centralClaimElement.textContent = results.metadata.central_claim;
    }
    
    const summaryContent = document.querySelector('.summary-content p');
    if (summaryContent && results.metadata && results.metadata.article_summary) {
        summaryContent.textContent = results.metadata.article_summary;
    }
    
    updateBadges(results);
}

function updateBadges(results) {
    const badgesContainer = document.querySelector('.badges');
    
    if (!badgesContainer) return;
    
    badgesContainer.innerHTML = '';
    
    const badges = [];
    
    if (results.bias_check) {
        const biasScore = results.bias_check.overall_score;
        if (biasScore >= 70) {
            badges.push({ text: 'Minimal Bias', type: 'success' });
        } else if (biasScore < 50) {
            badges.push({ text: 'Potential Bias Detected', type: 'warning' });
        } else {
            badges.push({ text: 'Moderate Bias', type: 'info' });
        }
    }
    
    if (results.evidence_check) {
        const evidenceScore = results.evidence_check.overall_score;
        if (evidenceScore >= 70) {
            badges.push({ text: 'Factually Sound', type: 'success' });
        } else if (evidenceScore < 50) {
            badges.push({ text: 'Weak Evidence', type: 'warning' });
        }
    }
    
    if (results.relevancy_check) {
        const relevancyScore = results.relevancy_check.overall_score;
        if (relevancyScore >= 70) {
            badges.push({ text: 'Recent Publication', type: 'info' });
        } else if (relevancyScore < 50) {
            badges.push({ text: 'Outdated Content', type: 'warning' });
        }
    }
    
    badges.forEach(badge => {
        const badgeEl = document.createElement('span');
        badgeEl.className = `badge badge-${badge.type}`;
        badgeEl.textContent = badge.text;
        badgesContainer.appendChild(badgeEl);
    });
}

function updateQuotes(results) {
    const quotesContainer = document.getElementById('quotes-container');
    
    if (!quotesContainer) return;
    
    quotesContainer.innerHTML = '';
    
    // Get quotes from evidence_check.evidence_items
    const quotes = results.evidence_check?.evidence_items || [];
    
    // If no quotes found, show a message
    if (quotes.length === 0) {
        quotesContainer.innerHTML = '<p style="color: var(--text-light); font-style: italic;">No key quotes extracted from this article.</p>';
        return;
    }
    
    // Render quotes (they're just strings, not objects)
    quotes.slice(0, 5).forEach(quote => { // Limit to 5 quotes
        const quoteItem = document.createElement('div');
        quoteItem.className = 'quote-item';
        quoteItem.innerHTML = `
            <p class="quote-text">${quote}</p>
        `;
        quotesContainer.appendChild(quoteItem);
    });
}

function loadRecommendedArticles(results) {
    const section = document.getElementById('recommended-section');
    const grid = document.getElementById('recommended-grid');

    if (!section || !grid) return;

    const recommendations = Array.isArray(results.recommended_articles)
        ? results.recommended_articles
        : [];

    if (recommendations.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    grid.innerHTML = '';

    recommendations.slice(0, 3).forEach((item, i) => {
        const url = item.url || '#';
        const title = item.title || `Recommended Article ${i + 1}`;
        const source = item.source || 'Recommended';
        const tag = item.tag || 'Related';
        const description = item.description || 'Suggested from analysis output.';

        let domain = 'External Link';
        try {
            domain = new URL(url).hostname.replace('www.', '');
        } catch (_e) {
            domain = 'External Link';
        }

        const card = document.createElement('a');
        card.href = url;
        card.className = 'article-card';
        card.target = '_blank';
        card.rel = 'noopener noreferrer';
        
        card.innerHTML = `
            <div class="article-card-header">
                <div class="article-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                </div>
                <span class="article-source">${source}</span>
            </div>
            <h3 class="article-title">${title}</h3>
            <p class="article-meta">
                <span class="article-author">${domain}</span>
                <span class="article-date">External Link</span>
            </p>
            <p class="article-description">${description}</p>
            <div class="article-footer">
                <span class="article-tag">${tag}</span>
                <svg class="article-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 5l7 7-7 7"/>
                </svg>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

function hideUsefulnessScore() {
    const usefulnessCard = document.querySelector('[data-score-type="Usefulness Check"]');
    if (usefulnessCard) {
        usefulnessCard.style.display = 'none';
    }
}

function initializeDropdowns() {
    const exportBtn = document.getElementById('export-btn');
    const exportMenu = document.getElementById('export-menu');
    const shareBtn = document.getElementById('share-btn');
    const shareMenu = document.getElementById('share-menu');

    exportBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle('active');
        shareMenu.classList.remove('active');
    });

    shareBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        shareMenu.classList.toggle('active');
        exportMenu.classList.remove('active');
    });

    document.querySelectorAll('#export-menu .dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const format = e.currentTarget.dataset.format;
            exportMenu.classList.remove('active');
            
            if (format === 'pdf') {
                exportAsPDF();
            } else if (format === 'json') {
                exportAsJSON();
            } else if (format === 'txt') {
                exportAsText();
            }
        });
    });

    document.querySelectorAll('#share-menu .dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const shareType = e.currentTarget.dataset.share;
            shareMenu.classList.remove('active');
            
            if (shareType === 'link') {
                copyLinkToClipboard();
            } else if (shareType === 'email') {
                shareViaEmail();
            } else if (shareType === 'twitter') {
                shareOnTwitter();
            } else if (shareType === 'clipboard') {
                copySummaryToClipboard();
            }
        });
    });

    document.addEventListener('click', () => {
        exportMenu?.classList.remove('active');
        shareMenu?.classList.remove('active');
    });

    [exportMenu, shareMenu].forEach(menu => {
        menu?.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    });
}

function exportAsJSON() {
    const data = sessionStorage.getItem('analysisResult');
    if (!data) {
        showNotification('No analysis data found', 'error');
        return;
    }
    
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clarity-analysis-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('JSON report downloaded successfully', 'info');
}

function exportAsText() {
    const data = JSON.parse(sessionStorage.getItem('analysisResult'));
    if (!data) {
        showNotification('No analysis data found', 'error');
        return;
    }
    
    let textContent = `CLARITY ANALYSIS REPORT\n`;
    textContent += `Generated: ${new Date().toLocaleString()}\n`;
    textContent += `${'='.repeat(50)}\n\n`;
    
    textContent += `ARTICLE METADATA\n`;
    textContent += `Title: ${data.metadata?.title || 'N/A'}\n`;
    textContent += `Author: ${data.metadata?.author || 'N/A'}\n`;
    textContent += `Date: ${data.metadata?.date || 'N/A'}\n\n`;
    
    textContent += `OVERALL CREDIBILITY SCORE: ${data.overall_credibility}%\n`;
    textContent += `${'='.repeat(50)}\n\n`;
    
    textContent += `BIAS CHECK (${data.bias_check?.overall_score}%)\n`;
    textContent += `${data.bias_check?.summary}\n\n`;
    
    textContent += `EVIDENCE CHECK (${data.evidence_check?.overall_score}%)\n`;
    textContent += `${data.evidence_check?.summary}\n\n`;
    
    textContent += `AUTHOR CREDIBILITY (${data.author_credibility?.overall_score}%)\n`;
    textContent += `${data.author_credibility?.summary}\n\n`;
    
    textContent += `CITATION CHECK (${data.citation_check?.overall_score}%)\n`;
    textContent += `${data.citation_check?.summary}\n\n`;
    
    textContent += `RELEVANCY CHECK (${data.relevancy_check?.overall_score}%)\n`;
    textContent += `${data.relevancy_check?.summary}\n\n`;
    
    if (data.hasPurpose) {
        textContent += `USEFULNESS CHECK (${data.usefulness_check?.overall_score}%)\n`;
        textContent += `${data.usefulness_check?.summary}\n`;
    }
    
    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clarity-analysis-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Text report downloaded successfully', 'info');
}

function exportAsPDF() {
    const data = JSON.parse(sessionStorage.getItem('analysisResult'));
    if (!data) {
        showNotification('No analysis data found', 'error');
        return;
    }
    
    showNotification('Generating PDF...', 'info');
    
    if (typeof jsPDF === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
        script.onload = () => generatePDF(data);
        document.head.appendChild(script);
    } else {
        generatePDF(data);
    }
}

function generatePDF(data) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    let y = 20;
    const lineHeight = 7;
    const pageHeight = doc.internal.pageSize.height;
    const margin = 20;
    
    const addText = (text, fontSize = 12, isBold = false) => {
        if (y > pageHeight - margin) {
            doc.addPage();
            y = 20;
        }
        doc.setFontSize(fontSize);
        doc.setFont('helvetica', isBold ? 'bold' : 'normal');
        const lines = doc.splitTextToSize(text, 170);
        doc.text(lines, 20, y);
        y += lines.length * lineHeight;
    };
    
    addText('CLARITY ANALYSIS REPORT', 18, true);
    y += 5;
    addText(`Generated: ${new Date().toLocaleString()}`, 10);
    y += 10;
    
    addText('ARTICLE METADATA', 14, true);
    y += 3;
    addText(`Title: ${data.metadata?.title || 'N/A'}`, 11);
    addText(`Author: ${data.metadata?.author || 'N/A'}`, 11);
    addText(`Date: ${data.metadata?.date || 'N/A'}`, 11);
    y += 10;
    
    addText(`OVERALL CREDIBILITY SCORE: ${data.overall_credibility}%`, 16, true);
    y += 10;
    
    addText(`Bias Check (${data.bias_check?.overall_score}%)`, 14, true);
    y += 3;
    addText(data.bias_check?.summary || 'N/A', 11);
    y += 10;
    
    addText(`Evidence Check (${data.evidence_check?.overall_score}%)`, 14, true);
    y += 3;
    addText(data.evidence_check?.summary || 'N/A', 11);
    y += 10;
    
    addText(`Author Credibility (${data.author_credibility?.overall_score}%)`, 14, true);
    y += 3;
    addText(data.author_credibility?.summary || 'N/A', 11);
    y += 10;
    
    addText(`Citation Check (${data.citation_check?.overall_score}%)`, 14, true);
    y += 3;
    addText(data.citation_check?.summary || 'N/A', 11);
    y += 10;
    
    addText(`Relevancy Check (${data.relevancy_check?.overall_score}%)`, 14, true);
    y += 3;
    addText(data.relevancy_check?.summary || 'N/A', 11);
    y += 10;
    
    if (data.hasPurpose) {
        addText(`Usefulness Check (${data.usefulness_check?.overall_score}%)`, 14, true);
        y += 3;
        addText(data.usefulness_check?.summary || 'N/A', 11);
    }
    
    doc.save(`clarity-analysis-${Date.now()}.pdf`);
    showNotification('PDF report downloaded successfully', 'info');
}

function copyLinkToClipboard() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        showNotification('Link copied to clipboard!', 'info');
    }).catch(() => {
        showNotification('Failed to copy link', 'error');
    });
}

function shareViaEmail() {
    const data = JSON.parse(sessionStorage.getItem('analysisResult'));
    const subject = encodeURIComponent('Article Credibility Analysis');
    const body = encodeURIComponent(
        `I analyzed "${data.metadata?.title || 'an article'}" and got an overall credibility score of ${data.overall_credibility}%.\n\nCheck out the full analysis here: ${window.location.href}`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
}

function shareOnTwitter() {
    const data = JSON.parse(sessionStorage.getItem('analysisResult'));
    const text = encodeURIComponent(
        `I just analyzed "${data.metadata?.title || 'an article'}" with Clarity and got a credibility score of ${data.overall_credibility}%!`
    );
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(window.location.href)}`, '_blank');
}

function copySummaryToClipboard() {
    const data = JSON.parse(sessionStorage.getItem('analysisResult'));
    const summary = `Article Credibility Analysis\n\nTitle: ${data.metadata?.title || 'N/A'}\nOverall Score: ${data.overall_credibility}%\n\nBias: ${data.bias_check?.overall_score}%\nEvidence: ${data.evidence_check?.overall_score}%\nAuthor: ${data.author_credibility?.overall_score}%`;
    
    navigator.clipboard.writeText(summary).then(() => {
        showNotification('Summary copied to clipboard!', 'info');
    }).catch(() => {
        showNotification('Failed to copy summary', 'error');
    });
}

function initializeScoreModal() {
    const modal = document.getElementById('score-modal');
    const modalOverlay = modal?.querySelector('.modal-overlay');
    const modalClose = modal?.querySelector('.modal-close');
    const modalTitle = document.getElementById('modal-title');
    const modalScoreValue = document.getElementById('modal-score-value');
    const modalPie = document.getElementById('modal-pie');
    const modalExplanation = document.getElementById('modal-explanation');
    const scoreCards = document.querySelectorAll('.score-card');

    scoreCards.forEach(card => {
        card.addEventListener('click', function() {
            const scoreType = this.getAttribute('data-score-type');
            const explanation = this.getAttribute('data-explanation');
            const scoreValue = this.querySelector('.pie').getAttribute('data-score');

            if (modal && scoreType && explanation && scoreValue) {
                modalTitle.textContent = scoreType;
                modalScoreValue.textContent = scoreValue;
                modalPie.style.setProperty('--p', scoreValue);
                
                // Clear previous content
                modalExplanation.innerHTML = `<p>${explanation}</p>`;
                
                // Add topic-specific quotes for Usefulness Check
                if (scoreType === 'Usefulness Check') {
                    const results = JSON.parse(sessionStorage.getItem('analysisResult'));
                    if (results.hasPurpose && results.usefulness_check?.useful_quotes && results.usefulness_check.useful_quotes.length > 0) {
                        const quotesSection = document.createElement('div');
                        quotesSection.className = 'modal-quotes-section';
                        quotesSection.innerHTML = `
                            <h4 style="margin-top: 24px; margin-bottom: 16px; color: var(--blue-600); font-size: 16px; font-weight: 600;">
                                Relevant Quotes for Your Topic
                            </h4>
                        `;
                        
                        results.usefulness_check.useful_quotes.forEach(quoteObj => {
                            const quoteEl = document.createElement('div');
                            quoteEl.className = 'modal-quote-item';
                            quoteEl.innerHTML = `
                                <div class="modal-quote-text">"${quoteObj.quote}"</div>
                                <div class="modal-quote-meta">
                                    <div class="modal-quote-use"><strong>Suggested Use:</strong> ${quoteObj.suggested_use}</div>
                                </div>
                            `;
                            quotesSection.appendChild(quoteEl);
                        });
                        
                        modalExplanation.appendChild(quotesSection);
                    }
                }

                modal.classList.add('active');
                document.body.style.overflow = 'hidden';

                setTimeout(() => {
                    animateModalPie(scoreValue);
                }, 100);
            }
        });
    });

    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeModal);
    }

    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal?.classList.contains('active')) {
            closeModal();
        }
    });

    function closeModal() {
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    function animateModalPie(targetScore) {
        let currentScore = 0;
        const duration = 800;
        const increment = targetScore / (duration / 16);

        const animate = () => {
            currentScore += increment;
            if (currentScore < targetScore) {
                modalPie.style.setProperty('--p', Math.round(currentScore));
                requestAnimationFrame(animate);
            } else {
                modalPie.style.setProperty('--p', targetScore);
            }
        };

        animate();
    }
}
