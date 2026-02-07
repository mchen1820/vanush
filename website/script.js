// Enhanced interactivity for Article Credibility Analyzer

document.addEventListener('DOMContentLoaded', function() {
  
  // ============================================
  // INPUT ANIMATIONS
  // ============================================
  
  const inputs = document.querySelectorAll('input[type="text"], textarea');
  inputs.forEach(input => {
    input.addEventListener('focus', function() {
      this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
      this.parentElement.classList.remove('focused');
    });
  });
  
  // ============================================
  // FILE UPLOAD INTERACTION
  // ============================================
  
  const fileInput = document.getElementById('pdf-input');
  if (fileInput) {
    const fileLabel = document.querySelector('.file-label');
    const fileText = document.querySelector('.file-text');
    
    fileInput.addEventListener('change', function(e) {
      if (this.files && this.files[0]) {
        const fileName = this.files[0].name;
        fileText.textContent = `Selected: ${fileName}`;
        fileLabel.style.borderColor = 'var(--blue-primary)';
        fileLabel.style.background = 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)';
      }
    });
    
    // Drag and drop
    fileLabel.addEventListener('dragover', function(e) {
      e.preventDefault();
      this.style.borderColor = 'var(--blue-primary)';
      this.style.background = 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)';
    });
    
    fileLabel.addEventListener('dragleave', function(e) {
      e.preventDefault();
      this.style.borderColor = '#d1d5db';
      this.style.background = 'linear-gradient(135deg, #fafbfc 0%, #f3f4f6 100%)';
    });
    
    fileLabel.addEventListener('drop', function(e) {
      e.preventDefault();
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
      }
    });
  }
  
  // ============================================
  // ANALYZE BUTTON VALIDATION
  // ============================================
  
  const analyzeBtn = document.querySelector('.analyze-btn');
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', function(e) {
      const urlInput = document.getElementById('url-input');
      const textInput = document.getElementById('text-input');
      const pdfInput = document.getElementById('pdf-input');
      
      // Check if any input has content
      const hasInput = (urlInput && urlInput.value.trim()) || 
                       (textInput && textInput.value.trim()) || 
                       (pdfInput && pdfInput.files.length > 0);
      
      if (!hasInput) {
        e.preventDefault();
        
        // Shake animation for cards
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
          card.style.animation = 'shake 0.5s';
          setTimeout(() => {
            card.style.animation = '';
          }, 500);
        });
        
        // Show message
        showNotification('Please provide an article URL, text, or PDF file to analyze.');
      }
    });
  }
  
  // ============================================
  // PIE CHART ANIMATIONS (Results Page)
  // ============================================
  
  const scoreCards = document.querySelectorAll('.score-card');
  if (scoreCards.length > 0) {
    const observerOptions = {
      threshold: 0.2,
      rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          animatePieChart(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);
    
    scoreCards.forEach(card => {
      observer.observe(card);
    });
  }
  
  function animatePieChart(card) {
    const pie = card.querySelector('.pie');
    const scoreBar = card.querySelector('.score-bar-fill');
    
    if (pie) {
      const targetScore = parseInt(pie.getAttribute('data-score') || pie.style.getPropertyValue('--p'));
      let currentScore = 0;
      const duration = 1500;
      const increment = targetScore / (duration / 16);
      
      const animate = () => {
        currentScore += increment;
        if (currentScore < targetScore) {
          pie.style.setProperty('--p', Math.round(currentScore));
          requestAnimationFrame(animate);
        } else {
          pie.style.setProperty('--p', targetScore);
        }
      };
      
      setTimeout(animate, parseInt(card.style.getPropertyValue('--delay')) * 1000 || 0);
    }
  }
  
  // ============================================
  // NOTIFICATION SYSTEM
  // ============================================
  
  function showNotification(message) {
    // Remove existing notification if any
    const existingNotif = document.querySelector('.notification');
    if (existingNotif) {
      existingNotif.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>
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
    }, 4000);
  }
  
  // Add notification styles dynamically
  if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
      .notification {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        color: #92400e;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: var(--shadow-xl);
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 1000;
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid #fbbf24;
        max-width: 400px;
      }
      
      .notification.show {
        transform: translateY(0);
        opacity: 1;
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
      
      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
      }
    `;
    document.head.appendChild(style);
  }
  
  // ============================================
  // SMOOTH SCROLL FOR BACK BUTTON
  // ============================================
  
  const backBtn = document.querySelector('.back-btn');
  if (backBtn) {
    backBtn.addEventListener('click', function(e) {
      // Add exit animation
      const panels = document.querySelectorAll('.left-panel, .right-panel');
      panels.forEach((panel, index) => {
        panel.style.animation = index === 0 ? 'slideOutLeft 0.4s ease-in' : 'slideOutRight 0.4s ease-in';
      });
    });
  }
  
  // Add exit animations
  const exitStyle = document.createElement('style');
  exitStyle.textContent = `
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
  document.head.appendChild(exitStyle);
  
  // ============================================
  // CARD HOVER EFFECTS
  // ============================================
  
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
  
  // Add card glow styles
  const cardGlowStyle = document.createElement('style');
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
  `;
  document.head.appendChild(cardGlowStyle);
  
  // ============================================
  // PARALLAX EFFECT FOR ORBS
  // ============================================
  
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
  
  animateOrbs();
  
  console.log('✨ Article Credibility Analyzer initialized');
});