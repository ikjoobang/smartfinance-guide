// Smart Finance Guide - Main JS
// Optimized for Core Web Vitals

// Reading progress bar (improves dwell time / engagement)
document.addEventListener('DOMContentLoaded', () => {
  const article = document.querySelector('article');
  if (!article) return;
  
  // Create progress bar
  const progress = document.createElement('div');
  progress.id = 'reading-progress';
  progress.style.cssText = 'position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,#1d4ed8,#6366f1);z-index:100;transition:width 0.1s;width:0';
  document.body.appendChild(progress);
  
  window.addEventListener('scroll', () => {
    const rect = article.getBoundingClientRect();
    const total = article.scrollHeight - window.innerHeight;
    const scrolled = Math.max(0, -rect.top);
    const pct = Math.min(100, (scrolled / total) * 100);
    progress.style.width = pct + '%';
  }, { passive: true });
});

// Copy link on heading click (useful for sharing specific sections)
document.querySelectorAll('.prose h2[id], .prose h3[id]').forEach(h => {
  h.style.cursor = 'pointer';
  h.title = 'Click to copy link';
  h.addEventListener('click', () => {
    const url = window.location.origin + window.location.pathname + '#' + h.id;
    navigator.clipboard?.writeText(url);
  });
});

// Lazy load images that aren't already lazy
document.querySelectorAll('img:not([loading])').forEach(img => {
  img.setAttribute('loading', 'lazy');
});

// External links open in new tab + noopener
document.querySelectorAll('a[href^="http"]').forEach(a => {
  if (!a.href.includes(window.location.hostname)) {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  }
});
