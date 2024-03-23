document.addEventListener('DOMContentLoaded', function() {
    const userList = document.getElementById('userList');

    fetch('/api/userlist')
        .then(response => response.json())
        .then(data => {

            data.forEach(user => {
                const listItem = document.createElement('li');
                listItem.textContent = user.name;
                listItem.addEventListener('click', function() {
                    window.location.href = '/view/' + user.id; 
                });
                userList.appendChild(listItem);
            });
        })
        .catch(error => {
            console.error('Ошибка получения данных:', error);
            alert('Произошла ошибка при получении списка пользователей.');
        });
});
