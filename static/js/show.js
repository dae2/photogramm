document.addEventListener("DOMContentLoaded", function() {
    fetchAlbums();
});

function fetchAlbums() {
    const userId = getUserIdFromUrl();
    fetch(`/api/albums/${userId}`)
        .then(response => response.json())
        .then(data => {
            const albumsDiv = document.getElementById('albums');
            albumsDiv.innerHTML = '';
            data.albums.forEach(album => {
                const albumDiv = document.createElement('div');
                albumDiv.classList.add('album');
                albumDiv.innerHTML = `
                    <img src="/static/img/album.jpg" alt="Album Cover">
                    <div class="title">${album.name}</div>
                `;
                albumDiv.addEventListener('click', function() {
                    window.location.href = `/view/${userId}/album/${album.id}`;
                });
                albumsDiv.appendChild(albumDiv);
            });
        })
        .catch(error => console.error('Error fetching albums:', error));
}

function getUserIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}
function newalbum() {
    const albumName = prompt("Введите название:", "");
    var albumVision;
    var access; 

    var result = confirm("Альбом будет открытым (нажмите ОК) или закрытым (нажмите Отмена)?");
    if (result) {
        albumVision = 1;
        access = null;
    } else {
        albumVision = 0;
        access = prompt("Введите id тех, кто будет иметь доступ, через ,:", "");
    }

    if (albumName === null || albumName.trim() === "") {
        alert("Название альбома не может быть пустым!");
        return;
    }

    fetch('/create_album', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: albumName, alov: albumVision, access: access })
    })
    .then(response => {
        if (response.ok) {
            window.location.reload(true);
        } else {
            alert('Не удалось создать альбом.');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при создании альбома.');
    });
}
