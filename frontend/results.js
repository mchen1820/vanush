// ============================================
// RESULTS PAGE - LOAD AND DISPLAY ANALYSIS
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    loadAnalysisResults();
});

function loadAnalysisResults() {
    // Get results from sessionStorage
    const resultsJson = sessionStorage.getItem('analysisResult');
    
    if (!resultsJson) {
        console.error('No analysis results found');
        window.location.href = 'index.html';
        return;
    }

    try {
        const results = JSON.parse(resultsJson);
        console.log('Analysis results:', results);
        
        // Update metadata
        updateMetadata(results.metadata);
        
        // Update overall credibility
        updateOverallScore(results.overall_credibility);
        
        // Update individual scores
        updateIndividualScores(results);
        
        // Update summary and central claim
        updateSummary(results);
        
    } catch (error) {
        console.error('Error loading results:', error);
        window.location.href = 'index.html';
    }
}

function updateMetadata(metadata) {
    // Update title
    const titleElement = document.querySelector('.meta-item:nth-child(1) .meta-value');
    if (titleElement && metadata.title) {
        titleElement.textContent = metadata.title;
    }
    
    // Update author
    const authorElement = document.querySelector('.meta-item:nth-child(2) .meta-value');
    if (authorElement && metadata.author) {
        authorElement.textContent = metadata.author;
    }
    
    // Update date
    const dateElement = document.querySelector('.meta-item:nth-child(3) .meta-value');
    if (dateElement && metadata.date) {
        dateElement.textContent = metadata.date;
    }
    
    // Update preview
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
    
    // Update description based on score
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
    // Score mapping matches the order in HTML:
    // Evidence, Bias, Date, Citation, Author, Publisher, Usefulness
    const scoreMapping = [
        { key: 'evidence_check', label: 'Evidence Quality Score' },
        { key: 'bias_check', label: 'Bias & Framing Score' },
        { key: 'relevancy_check', label: 'Date & Relevancy Score' },
        { key: 'citation_check', label: 'Citation Validity Score' },
        { key: 'author_credibility', label: 'Author Credibility Score' },
        { key: 'organization_check', label: 'Publisher Credibility Score' },
        { key: 'usefulness_check', label: 'Usefulness Score' },
    ];
    
    const scoreCards = document.querySelectorAll('.score-card');
    
    scoreCards.forEach((card, index) => {
        if (index < scoreMapping.length) {
            const mapping = scoreMapping[index];
            const data = results[mapping.key];
            
            if (data && data.overall_score !== undefined) {
                const score = data.overall_score;
                
                // Update pie chart
                const pie = card.querySelector('.pie');
                const pieText = card.querySelector('.pie-text');
                if (pie && pieText) {
                    pie.style.setProperty('--p', score);
                    pie.setAttribute('data-score', score);
                    pieText.textContent = `${score}%`;
                }
                
                // Update progress bar
                const barFill = card.querySelector('.score-bar-fill');
                if (barFill) {
                    barFill.style.width = `${score}%`;
                }
                
                // Update explanation in data attribute if available
                if (data.summary) {
                    card.setAttribute('data-explanation', data.summary);
                }
            }
        }
    });
}

function updateSummary(results) {
    // Update central claim
    const centralClaimElement = document.querySelector('.central-claim p');
    if (centralClaimElement && results.metadata && results.metadata.central_claim) {
        centralClaimElement.textContent = results.metadata.central_claim;
    }
    
    // Update article summary
    const summaryContent = document.querySelector('.summary-content p');
    if (summaryContent && results.metadata && results.metadata.article_summary) {
        summaryContent.textContent = results.metadata.article_summary;
    }
    
    // Update badges based on results
    updateBadges(results);
}

function updateBadges(results) {
    const badgesContainer = document.querySelector('.badges');
    
    if (!badgesContainer) return;
    
    // Clear existing badges
    badgesContainer.innerHTML = '';
    
    // Add badges based on analysis
    const badges = [];
    
    // Bias badge
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
    
    // Evidence badge
    if (results.evidence_check) {
        const evidenceScore = results.evidence_check.overall_score;
        if (evidenceScore >= 70) {
            badges.push({ text: 'Factually Sound', type: 'success' });
        } else if (evidenceScore < 50) {
            badges.push({ text: 'Weak Evidence', type: 'warning' });
        }
    }
    
    // Relevancy badge
    if (results.relevancy_check) {
        const relevancyScore = results.relevancy_check.overall_score;
        if (relevancyScore >= 70) {
            badges.push({ text: 'Recent Publication', type: 'info' });
        } else if (relevancyScore < 50) {
            badges.push({ text: 'Outdated Content', type: 'warning' });
        }
    }
    
    // Create badge elements
    badges.forEach(badge => {
        const badgeEl = document.createElement('span');
        badgeEl.className = `badge badge-${badge.type}`;
        badgeEl.textContent = badge.text;
        badgesContainer.appendChild(badgeEl);
    });
}

// Export functionality
function exportReport() {
    const resultsJson = sessionStorage.getItem('analysisResult');
    if (!resultsJson) return;
    
    const results = JSON.parse(resultsJson);
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'credibility-analysis.json';
    a.click();
    URL.revokeObjectURL(url);
}

// Share functionality
function shareAnalysis() {
    const resultsJson = sessionStorage.getItem('analysisResult');
    if (!resultsJson) return;
    
    const results = JSON.parse(resultsJson);
    const shareText = `Article Credibility Analysis\n\nOverall Score: ${results.overall_credibility}/100\n\nAnalyzed with Article Credibility Analyzer`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Article Credibility Analysis',
            text: shareText,
        }).catch(err => console.log('Error sharing:', err));
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(shareText).then(() => {
            alert('Analysis summary copied to clipboard!');
        });
    }
}

// Attach event listeners to action buttons
document.addEventListener('DOMContentLoaded', function() {
    const exportBtn = document.querySelector('.btn-primary');
    const shareBtn = document.querySelector('.btn-secondary');
    
    if (exportBtn) {
        exportBtn.addEventListener('click', exportReport);
    }
    
    if (shareBtn) {
        shareBtn.addEventListener('click', shareAnalysis);
    }
});

// ============================================
// SCORE MODAL FUNCTIONALITY
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('score-modal');
  const modalOverlay = modal?.querySelector('.modal-overlay');
  const modalClose = modal?.querySelector('.modal-close');
  const modalTitle = document.getElementById('modal-title');
  const modalScoreValue = document.getElementById('modal-score-value');
  const modalPie = document.getElementById('modal-pie');
  const modalExplanation = document.getElementById('modal-explanation');
  const scoreCards = document.querySelectorAll('.score-card');

  // Open modal when score card is clicked
  scoreCards.forEach(card => {
    card.addEventListener('click', function() {
      const scoreType = this.getAttribute('data-score-type');
      const explanation = this.getAttribute('data-explanation');
      const scoreValue = this.querySelector('.pie').getAttribute('data-score');

      if (modal && scoreType && explanation && scoreValue) {
        // Update modal content
        modalTitle.textContent = scoreType;
        modalScoreValue.textContent = scoreValue;
        modalPie.style.setProperty('--p', scoreValue);
        modalExplanation.textContent = explanation;

        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Animate pie chart
        setTimeout(() => {
          animateModalPie(scoreValue);
        }, 100);
      }
    });
  });

  // Close modal when clicking overlay
  if (modalOverlay) {
    modalOverlay.addEventListener('click', closeModal);
  }

  // Close modal when clicking close button
  if (modalClose) {
    modalClose.addEventListener('click', closeModal);
  }

  // Close modal on Escape key
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
});