let currentSlide = 0;
const slides = document.querySelectorAll('.slide');

function showSlide(n) {
  slides.forEach(slide => {
    slide.style.animation = '';
    slide.classList.remove('active');
  });
  slides[n].style.animation = 'fadeIn 1s forwards';
  slides[n].classList.add('active');
}

function nextSlide() {
  currentSlide = (currentSlide + 1) % slides.length;
  showSlide(currentSlide);
}

function autoSlide() {
  nextSlide();
}

setInterval(autoSlide, 7000); 

showSlide(currentSlide);
