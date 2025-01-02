async function searchVideos() {
    const searchTerm = document.getElementById('searchInput').value;
    const response = await fetch(`/api/videos/search?q=${searchTerm}`);
    const videos = await response.json();
    updateFeed(videos);
}

function updateFeed(videos) {
    const feedDiv = document.getElementById('feed');
    feedDiv.innerHTML = '';
    
}