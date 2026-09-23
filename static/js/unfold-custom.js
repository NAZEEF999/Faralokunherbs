document.addEventListener('DOMContentLoaded', function () {
  // Fade in content
  const main = document.querySelector('main') || document.querySelector('#content');
  if (main) {
    main.style.opacity = '0';
    main.style.transform = 'translateY(10px)';
    requestAnimationFrame(() => {
      main.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      main.style.opacity = '1';
      main.style.transform = 'translateY(0)';
    });
  }

  console.log('Faralokun Vital Herbs admin loaded');
});