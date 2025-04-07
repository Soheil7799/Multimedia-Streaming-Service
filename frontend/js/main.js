document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const videoFile = document.getElementById('video-file');
    const uploadProgress = document.getElementById('upload-progress').querySelector('.progress');
    const filterSection = document.querySelector('.filter-section');
    const saveConfigBtn = document.getElementById('save-config');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const videoPlayer = document.getElementById('video-player');
    const startStreamBtn = document.getElementById('start-stream');
    const videoPlayerSection = document.querySelector('.video-player');
    
    // Handle file upload
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!videoFile.files[0]) {
            alert('Please select a file to upload');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', videoFile.files[0]);
        
        // TODO: Replace with your actual API endpoint
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            return response.json();
        })
        .then(data => {
            console.log('Upload successful:', data);
            filterSection.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Upload failed: ' + error.message);
        });
    });
    
    // Mock implementation - will be replaced with actual API calls
    saveConfigBtn.addEventListener('click', function() {
        alert('Configuration saved');
    });
    
    applyFiltersBtn.addEventListener('click', function() {
        alert('Filters applied');
        videoPlayerSection.style.display = 'block';
    });
    
    startStreamBtn.addEventListener('click', function() {
        // TODO: Replace with your streaming endpoint
        videoPlayer.src = '/stream';
        videoPlayer.play();
    });
});