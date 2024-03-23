document.addEventListener("DOMContentLoaded", function() {
    fetchPhotos();
});

function fetchPhotos() {
    const userId = getUserIdFromUrl();
    const albumId = getAlbumIdFromUrl();
    fetch(`/api/photos/${userId}/${albumId}`)
        .then(response => response.json())
        .then(data => {
            const photosDiv = document.getElementById('photos');
            photosDiv.innerHTML = '';
            data.photos.forEach(photo => {
                const photoDiv = document.createElement('div');
                photoDiv.classList.add('photo');

                const img = document.createElement('img');
                img.src = photo.url;

                const infoOverlay = document.createElement('div');
                infoOverlay.classList.add('info-overlay');

                const photoInfo = document.createElement('div');
                photoInfo.classList.add('photo-info');

                const nameAndTagsDiv = document.createElement('div');
                nameAndTagsDiv.classList.add('photo-name-tags');
                nameAndTagsDiv.textContent = `${photo.name}${photo.tags ? ': ' + photo.tags.join(', ') : ''}`;

                photoInfo.appendChild(nameAndTagsDiv);

                const isAuthor = document.getElementById('is-author').textContent.trim() === 'true';

                if (isAuthor) {
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = 'Delete';
                    deleteButton.classList.add('delete-button');
                    deleteButton.addEventListener('click', () => deletePhoto(userId, albumId, photo.id));
                    photoInfo.appendChild(deleteButton);
                }

                infoOverlay.appendChild(photoInfo);
                photoDiv.appendChild(img);
                photoDiv.appendChild(infoOverlay);

                photosDiv.appendChild(photoDiv);
            });
        })
        .catch(error => console.error('Error fetching photos:', error));
}




function deletePhoto(userId, albumId, photoId) {
    const confirmDelete = confirm("Вы уверены, что хотите удалить эту фотографию?");
    if (confirmDelete) {
        fetch(`/api/photos/${userId}/${albumId}/${photoId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete photo');
            }
            fetchPhotos(); 
        })
        .catch(error => console.error('Error deleting photo:', error));
    }
}







function getUserIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 3];
}

function getAlbumIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}
function renameAlbum() {
    const newName = prompt("Введите новое имя для альбома:");
    if (newName !== null && newName !== "") {
        const userId = getUserIdFromUrl();
        const albumId = getAlbumIdFromUrl();
        console.log(userId)
        fetch(`/api/albums/${userId}/${albumId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: newName })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to rename album');
            }
            window.location.reload();
        })
        .catch(error => console.error('Error renaming album:', error));
    }
}

function deleteAlbum() {
    const confirmDelete = confirm("Вы уверены, что хотите удалить этот альбом?");
    if (confirmDelete) {
        const userId = getUserIdFromUrl();
        const albumId = getAlbumIdFromUrl();
        fetch(`/api/albums/${userId}/${albumId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete album');
            }
            window.location.href = "/myalbum";
        })
        .catch(error => console.error('Error deleting album:', error));
    }
}


document.getElementById('upload-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const albumId = getAlbumIdFromUrl();
    const userId = getUserIdFromUrl();
    const imageInput = document.getElementById('image-input').files[0];
    const imageName = prompt("Please enter the image name:", "");
    const imageTags = prompt("Please enter image tags (comma separated):", "");
    
    const formData = new FormData();
    formData.append('image', imageInput);
    formData.append('name', imageName);
    formData.append('tags', imageTags);

    const response = await fetch(`/api/upload/${userId}/${albumId}`, {
        method: 'POST',
        body: formData
    });
    window.location.reload(true);

});
