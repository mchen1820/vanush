// ============================================
// SHARED UTILITIES - Used on both pages
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  
  // ============================================
  // INPUT ANIMATIONS
  // ============================================
  
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
  
  if (document.querySelectorAll('.orb').length > 0) {
    animateOrbs();
  }
  
  // ============================================
  // BACK BUTTON ANIMATION
  // ============================================
  
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

// ============================================
// DYNAMIC STYLES
// ============================================

// Add card glow styles
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