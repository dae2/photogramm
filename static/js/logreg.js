document.addEventListener('DOMContentLoaded', function() {
    const title = document.querySelector('.fadeIn');
    title.style.animation = 'fadeIn 2s';
});
document.getElementById('changeLink').addEventListener('click', function() {
    document.querySelector('form').setAttribute('action', '/register'); 
});