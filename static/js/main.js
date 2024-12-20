// async function loadVideos() {
//     const response = await fetch('/api/videos');
//     const videos = await response.json();

//     const feed = document.getElementById('feed');
//     videos.forEach(video => {
//         const videoElement = document.createElement('div');
//         videoElement.innerHTML = \
//             <video controls>
//                 <source src="\" type="video/mp4">
//             </video>
//             <p>\</p>
//         \;
//         feed.appendChild(videoElement);
//     });
// }

// if (document.getElementById('feed')) {
//     loadVideos();
// }
