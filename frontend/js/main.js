document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const videoFileInput = document.getElementById('video-file');
    const uploadProgress = document.querySelector('#upload-progress .progress');
    const analysisSection = document.querySelector('.analysis-section');
    const fileInfoSection = document.getElementById('file-info');
    const filenameElement = document.getElementById('filename');
    const durationElement = document.getElementById('duration');
    const formatElement = document.getElementById('format');
    const streamsElement = document.getElementById('streams');
    const filterSection = document.querySelector('.filter-section');
    const audioFiltersContainer = document.getElementById('audio-filters');
    const videoFiltersContainer = document.getElementById('video-filters');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const playerSection = document.querySelector('.player-section');
    const videoPlayer = document.getElementById('video-player');
    
    // State
    let currentVideoId = null;
    let fileMetadata = null;
    let selectedFilters = {
        audio_filters: [],
        video_filters: []
    };
    
    // Base API URL
    const API_BASE_URL = 'http://localhost:8000/api';
    
    // Handle file upload
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!videoFileInput.files.length) {
            alert('Please select a file to upload');
            return;
        }
        
        const file = videoFileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        // Reset UI
        uploadProgress.style.width = '0%';
        uploadForm.classList.add('uploading');
        
        // Upload file
        fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            uploadProgress.style.width = '100%';
            return response.json();
        })
        .then(data => {
            currentVideoId = data.id;
            console.log('Upload successful:', data);
            
            // Analyze the file
            return fetch(`${API_BASE_URL}/analyze/${currentVideoId}`);
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Analysis failed');
            }
            return response.json();
        })
        .then(metadata => {
            fileMetadata = metadata;
            displayFileMetadata(metadata);
            createFilterOptions(metadata);
            
            // Show analysis and filter sections
            analysisSection.style.display = 'block';
            filterSection.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error: ${error.message}`);
            uploadForm.classList.remove('uploading');
        });
    });
    
    // Display file metadata
    function displayFileMetadata(metadata) {
        filenameElement.textContent = metadata.filename;
        durationElement.textContent = metadata.duration.toFixed(2);
        formatElement.textContent = metadata.format;
        
        // Display stream info
        streamsElement.innerHTML = '';
        metadata.streams.forEach((stream, index) => {
            const streamDiv = document.createElement('div');
            streamDiv.classList.add('stream-info');
            
            if (stream.type === 'video') {
                streamDiv.innerHTML = `
                    <p><strong>Video Stream ${index + 1}:</strong></p>
                    <ul>
                        <li>Codec: ${stream.codec}</li>
                        <li>Resolution: ${stream.width}x${stream.height}</li>
                        <li>Frame Rate: ${typeof stream.frame_rate === 'number' ? stream.frame_rate.toFixed(2) : stream.frame_rate} fps</li>
                    </ul>
                `;
            } else if (stream.type === 'audio') {
                streamDiv.innerHTML = `
                    <p><strong>Audio Stream ${index + 1}:</strong></p>
                    <ul>
                        <li>Codec: ${stream.codec}</li>
                        <li>Channels: ${stream.channels}</li>
                        <li>Sample Rate: ${stream.sample_rate} Hz</li>
                    </ul>
                `;
            }
            
            streamsElement.appendChild(streamDiv);
        });
    }
    
    // Create filter options UI
    function createFilterOptions(metadata) {
        // Clear existing options
        audioFiltersContainer.innerHTML = '';
        videoFiltersContainer.innerHTML = '';
        
        // Reset selected filters
        selectedFilters = {
            audio_filters: [],
            video_filters: []
        };
        
        // Function to create filter UI elements
        function createFilterElements(filters, container, filterType) {
            filters.forEach(filter => {
                const filterItem = document.createElement('div');
                filterItem.classList.add('filter-item');
                
                const filterHeader = document.createElement('div');
                filterHeader.classList.add('filter-header');
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `filter-${filter.name}`;
                checkbox.dataset.filterType = filterType;
                checkbox.dataset.filterName = filter.name;
                
                const label = document.createElement('label');
                label.htmlFor = `filter-${filter.name}`;
                label.textContent = filter.display_name;
                
                filterHeader.appendChild(checkbox);
                filterHeader.appendChild(label);
                filterItem.appendChild(filterHeader);
                
                // Add filter parameters
                if (filter.params && filter.params.length > 0) {
                    const paramsContainer = document.createElement('div');
                    paramsContainer.classList.add('filter-params');
                    paramsContainer.style.display = 'none'; // Initially hidden
                    
                    filter.params.forEach(param => {
                        const paramItem = document.createElement('div');
                        paramItem.classList.add('param-item');
                        
                        const paramLabel = document.createElement('label');
                        paramLabel.htmlFor = `param-${filter.name}-${param.name}`;
                        paramLabel.textContent = param.name.replace(/_/g, ' ');
                        
                        const paramInput = document.createElement('input');
                        paramInput.type = param.type || 'range';
                        paramInput.id = `param-${filter.name}-${param.name}`;
                        paramInput.name = param.name;
                        paramInput.min = param.min || 0;
                        paramInput.max = param.max || 100;
                        paramInput.step = param.step || 1;
                        paramInput.value = param.default || ((param.min + param.max) / 2);
                        
                        const paramValue = document.createElement('span');
                        paramValue.classList.add('param-value');
                        paramValue.textContent = paramInput.value;
                        
                        // Update value display on input change
                        paramInput.addEventListener('input', function() {
                            paramValue.textContent = this.value;
                            updateFilterParams(filter.name, param.name, this.value, filterType);
                        });
                        
                        paramItem.appendChild(paramLabel);
                        paramItem.appendChild(paramInput);
                        paramItem.appendChild(paramValue);
                        paramsContainer.appendChild(paramItem);
                    });
                    
                    filterItem.appendChild(paramsContainer);
                    
                    // Toggle parameters display when checkbox is clicked
                    checkbox.addEventListener('change', function() {
                        paramsContainer.style.display = this.checked ? 'block' : 'none';
                        updateSelectedFilters(this, filter);
                    });
                } else {
                    // Simple toggle for filters without parameters
                    checkbox.addEventListener('change', function() {
                        updateSelectedFilters(this, filter);
                    });
                }
                
                container.appendChild(filterItem);
            });
        }
        
        // Add audio filters
        if (metadata.available_filters && metadata.available_filters.audio) {
            createFilterElements(metadata.available_filters.audio, audioFiltersContainer, 'audio');
        }
        
        // Add video filters
        if (metadata.available_filters && metadata.available_filters.video) {
            createFilterElements(metadata.available_filters.video, videoFiltersContainer, 'video');
        }
    }
    
    // Update filter parameters when changed
    function updateFilterParams(filterName, paramName, value, filterType) {
        // Find the filter in selected filters
        const filterTypeKey = `${filterType}_filters`;
        const filterIndex = selectedFilters[filterTypeKey].findIndex(f => f.name === filterName);
        
        if (filterIndex !== -1) {
            // Update parameter value
            selectedFilters[filterTypeKey][filterIndex].params[paramName] = parseFloat(value);
        }
    }
    
    // Update selected filters when checkboxes change
    function updateSelectedFilters(checkbox, filter) {
        const filterType = `${checkbox.dataset.filterType}_filters`;
        const filterName = checkbox.dataset.filterName;
        
        if (checkbox.checked) {
            // Add filter to selected filters
            const filterParams = {};
            
            // Initialize parameters with default values
            if (filter.params) {
                filter.params.forEach(param => {
                    const inputElement = document.getElementById(`param-${filterName}-${param.name}`);
                    filterParams[param.name] = parseFloat(inputElement.value);
                });
            }
            
            selectedFilters[filterType].push({
                name: filterName,
                params: filterParams
            });
        } else {
            // Remove filter from selected filters
            const filterIndex = selectedFilters[filterType].findIndex(f => f.name === filterName);
            if (filterIndex !== -1) {
                selectedFilters[filterType].splice(filterIndex, 1);
            }
        }
        
        console.log('Selected filters:', selectedFilters);
    }
    
    // Apply filters
    applyFiltersBtn.addEventListener('click', function() {
        if (!currentVideoId) {
            alert('Please upload a file first');
            return;
        }
        
        // Show loading indicator
        applyFiltersBtn.textContent = 'Processing...';
        applyFiltersBtn.disabled = true;
        
        // Add a processing message to the UI
        const processingMessage = document.createElement('div');
        processingMessage.id = 'processing-message';
        processingMessage.className = 'processing-message';
        processingMessage.innerHTML = '<p>Processing your video...</p><p>This may take a while depending on the filters selected.</p>';
        filterSection.appendChild(processingMessage);
        
        // Create a timeout to check for long-running processes
        const processingTimeout = setTimeout(() => {
            const timeoutMessage = document.createElement('p');
            timeoutMessage.textContent = 'Still processing... This might take longer for complex filters or large files.';
            processingMessage.appendChild(timeoutMessage);
        }, 10000); // Show additional message after 10 seconds
        
        // First, save the configuration
        fetch(`${API_BASE_URL}/filters/${currentVideoId}/configure`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(selectedFilters)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.detail || 'Failed to save configuration');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Configuration saved:', data);
            
            // Apply the filters
            return fetch(`${API_BASE_URL}/filters/${currentVideoId}/apply`, {
                method: 'POST'
            });
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.detail || 'Failed to apply filters');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Filters applied:', data);
            
            // Clear the timeout
            clearTimeout(processingTimeout);
            
            // Reset button state
            applyFiltersBtn.textContent = 'Apply Filters';
            applyFiltersBtn.disabled = false;
            
            // Remove processing message
            const existingMessage = document.getElementById('processing-message');
            if (existingMessage) {
                existingMessage.remove();
            }
            
            // Show video player
            playerSection.style.display = 'block';
            
            // Set video source
            videoPlayer.src = `${API_BASE_URL}/stream/${currentVideoId}`;
            videoPlayer.load();
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Clear the timeout
            clearTimeout(processingTimeout);
            
            // Reset button state
            applyFiltersBtn.textContent = 'Apply Filters';
            applyFiltersBtn.disabled = false;
            
            // Change processing message to error message
            const existingMessage = document.getElementById('processing-message');
            if (existingMessage) {
                existingMessage.innerHTML = `<p class="error">Error: ${error.message}</p>
                <p>There was a problem applying the filters. You can:</p>
                <ul>
                    <li>Try again with fewer or different filters</li>
                    <li>Check if your video format is supported</li>
                    <li>Try a shorter or smaller video file</li>
                </ul>`;
                existingMessage.className = 'error-message';
            } else {
                alert(`Error: ${error.message}`);
            }
        });
    });
    // Update selected filters when checkboxes change
    function updateSelectedFilters(checkbox, filter) {
        const filterType = `${checkbox.dataset.filterType}_filters`;
        const filterName = checkbox.dataset.filterName;
        
        if (checkbox.checked) {
            // Check for potentially resource-intensive combinations
            if (filterName === 'frame_interpolation' && isFilterSelected('upscaling', 'video')) {
                if (!confirm('Combining Frame Interpolation with Upscaling might require significant processing time. Do you want to continue?')) {
                    checkbox.checked = false;
                    return;
                }
            }
            
            // Add filter to selected filters
            const filterParams = {};
            
            // Initialize parameters with default values
            if (filter.params) {
                filter.params.forEach(param => {
                    const inputElement = document.getElementById(`param-${filterName}-${param.name}`);
                    filterParams[param.name] = parseFloat(inputElement.value);
                });
            }
            
            selectedFilters[filterType].push({
                name: filterName,
                params: filterParams
            });
            
            // Update UI to reflect active filters
            updateActiveFilterStyles();
        } else {
            // Remove filter from selected filters
            const filterIndex = selectedFilters[filterType].findIndex(f => f.name === filterName);
            if (filterIndex !== -1) {
                selectedFilters[filterType].splice(filterIndex, 1);
            }
            
            // Update UI to reflect active filters
            updateActiveFilterStyles();
        }
        
        console.log('Selected filters:', selectedFilters);
        
        // Update Apply Filters button state
        updateApplyButtonState();
    }
    
    // Check if a specific filter is selected
    function isFilterSelected(filterName, filterType) {
        const filterTypeKey = `${filterType}_filters`;
        return selectedFilters[filterTypeKey].some(f => f.name === filterName);
    }
    
    // Update UI to reflect active filters
    function updateActiveFilterStyles() {
        // Reset all filter items
        document.querySelectorAll('.filter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected filters
        document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
            const filterItem = checkbox.closest('.filter-item');
            if (filterItem) {
                filterItem.classList.add('active');
            }
        });
    }
    
    // Update Apply button state based on selected filters
    function updateApplyButtonState() {
        const hasFilters = selectedFilters.audio_filters.length > 0 || selectedFilters.video_filters.length > 0;
        applyFiltersBtn.disabled = !hasFilters;
        
        if (hasFilters) {
            applyFiltersBtn.classList.add('ready');
        } else {
            applyFiltersBtn.classList.remove('ready');
        }
    }
});