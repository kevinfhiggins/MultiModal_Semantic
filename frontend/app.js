// MoD Semantic Search - Frontend Application

const API_BASE_URL = 'http://localhost:8000';

// State
let currentModality = 'all';
let isSearching = false;
let currentBrowseFilter = 'all';
let allDocuments = [];

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const filterBtns = document.querySelectorAll('.filter-btn');
const resultsContainer = document.getElementById('results-container');
const welcomeState = document.getElementById('welcome-state');
const loadingState = document.getElementById('loading-state');
const errorState = document.getElementById('error-state');
const errorMessage = document.getElementById('error-message');
const resultsList = document.getElementById('results-list');

// Tab elements
const tabBtns = document.querySelectorAll('.tab-btn');
const searchTab = document.getElementById('search-tab');
const browseTab = document.getElementById('browse-tab');
const uploadTab = document.getElementById('upload-tab');

// Browse elements
const browseFilterBtns = document.querySelectorAll('.browse-filter-btn');
const browseLoading = document.getElementById('browse-loading');
const browseError = document.getElementById('browse-error');
const browseErrorMessage = document.getElementById('browse-error-message');
const browseList = document.getElementById('browse-list');

// Upload form elements
const uploadForm = document.getElementById('upload-form');
const uploadFile = document.getElementById('upload-file');
const uploadModality = document.getElementById('upload-modality');
const captionGroup = document.getElementById('caption-group');
const transcriptGroup = document.getElementById('transcript-group');
const uploadStatus = document.getElementById('upload-status');
const resetBtn = document.getElementById('reset-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkBackendHealth();
});

// Event Listeners
function setupEventListeners() {
    // Search
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Filters
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentModality = btn.dataset.modality;
        });
    });

    // Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            switchTab(targetTab);
        });
    });

    // Upload form
    uploadModality.addEventListener('change', handleModalityChange);
    uploadForm.addEventListener('submit', handleUpload);
    resetBtn.addEventListener('click', resetUploadForm);

    // Browse filters
    browseFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            browseFilterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentBrowseFilter = btn.dataset.filter;
            displayBrowseDocuments();
        });
    });
}

// Tab switching
function switchTab(tabName) {
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    searchTab.classList.remove('active');
    browseTab.classList.remove('active');
    uploadTab.classList.remove('active');

    if (tabName === 'search') {
        searchTab.classList.add('active');
    } else if (tabName === 'browse') {
        browseTab.classList.add('active');
        loadAllDocuments();
    } else if (tabName === 'upload') {
        uploadTab.classList.add('active');
    }
}

// Check backend health
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('Backend health:', data);
    } catch (error) {
        console.error('Backend is not accessible:', error);
    }
}

// Search handler
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        showError('Please enter a search query');
        return;
    }

    if (isSearching) return;

    try {
        isSearching = true;
        showLoading();

        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                modality: currentModality,
                top_k: 20  // Return more results to browse
            })
        });

        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Search error:', error);
        showError(error.message || 'Failed to perform search. Please check your connection and try again.');
    } finally {
        isSearching = false;
    }
}

// Display search results
function displayResults(data) {
    hideAllStates();

    if (!data.results || data.results.length === 0) {
        showError('No results found. Try a different query or adjust your filters.');
        return;
    }

    resultsList.innerHTML = '';
    resultsList.classList.remove('hidden');

    // Add results header
    const header = document.createElement('div');
    header.style.marginBottom = '20px';
    header.innerHTML = `
        <h3>Found ${data.total} result${data.total !== 1 ? 's' : ''} for: <em>"${data.query}"</em></h3>
        ${data.modality_filter ? `<p style="color: var(--text-secondary);">Filtered by: ${data.modality_filter}</p>` : ''}
    `;
    resultsList.appendChild(header);

    // Add search trail tile if present
    if (data.search_trail && data.search_trail.length > 0) {
        const trailTile = createSearchTrail(data.search_trail);
        resultsList.appendChild(trailTile);
    }

    // Add search info tile if present
    if (data.search_info) {
        const infoTile = document.createElement('div');
        infoTile.className = 'search-info-tile';
        infoTile.innerHTML = `
            <div class="search-info-icon">ℹ️</div>
            <div class="search-info-text">${escapeHtml(data.search_info)}</div>
        `;
        resultsList.appendChild(infoTile);
    }

    // Render each result
    data.results.forEach(result => {
        const card = createResultCard(result);
        resultsList.appendChild(card);
    });
}

// Create search trail visualization
function createSearchTrail(steps) {
    const trail = document.createElement('div');
    trail.className = 'search-trail';

    const iconMap = {
        query: '1',
        embedding: '2',
        search: '3',
        results: '4'
    };

    const stepsHtml = steps.map(step => `
        <div class="search-trail-step">
            <div class="trail-step-icon">${iconMap[step.icon] || '?'}</div>
            <div class="trail-step-label">${escapeHtml(step.label)}</div>
            <div class="trail-step-detail">${escapeHtml(step.detail)}</div>
        </div>
    `).join('');

    trail.innerHTML = `
        <div class="search-trail-header" onclick="toggleSearchTrail(this)">
            <div class="search-trail-title">
                <span>Search Pipeline Trail</span>
            </div>
            <span class="search-trail-toggle">&#9660;</span>
        </div>
        <div class="search-trail-steps">
            ${stepsHtml}
        </div>
    `;

    return trail;
}

function toggleSearchTrail(header) {
    const steps = header.nextElementSibling;
    const toggle = header.querySelector('.search-trail-toggle');
    steps.classList.toggle('hidden');
    toggle.classList.toggle('collapsed');
}

// Create result card
function createResultCard(result) {
    const card = document.createElement('div');
    card.className = 'result-card';

    // Debug: Log the result object for audio
    if (result.modality === 'audio') {
        console.log('Creating audio result card:', result);
        console.log('Timestamp:', result.timestamp);
        console.log('Matched text:', result.matched_text);
    }

    const modalityIcon = getModalityIcon(result.modality);
    const score = result.score ? (result.score * 100).toFixed(1) : null;

    // Build media content based on modality
    let mediaContent = '';
    if (result.file_url) {
        if (result.modality === 'image') {
            // Show the actual image
            mediaContent = `
                <div class="result-media">
                    <img src="${escapeHtml(result.file_url)}" alt="${escapeHtml(result.title)}" class="result-image">
                </div>
            `;
        } else if (result.modality === 'audio') {
            // Show audio player with timestamp support
            const audioId = 'audio-' + (result._id || result.id || Math.random().toString(36).substr(2, 9));
            const timestamp = result.timestamp || 0;
            const hasMatch = result.matched_text && result.timestamp !== null;

            mediaContent = `
                <div class="result-media">
                    ${hasMatch ? `
                        <div class="audio-match-info">
                            <strong>🎯 Match found at ${formatTimestamp(timestamp)}</strong>
                            <p class="matched-text">"${escapeHtml(result.matched_text)}"</p>
                        </div>
                    ` : ''}
                    <audio controls class="result-audio" id="${audioId}" data-timestamp="${timestamp}">
                        <source src="${escapeHtml(result.file_url)}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            `;
        } else if (result.modality === 'video') {
            // Show video player with timestamp support
            const videoId = 'video-' + (result._id || result.id || Math.random().toString(36).substr(2, 9));
            const timestamp = result.timestamp || 0;
            const hasMatch = result.matched_text && result.timestamp !== null;

            mediaContent = `
                <div class="result-media">
                    ${hasMatch ? `
                        <div class="audio-match-info">
                            <strong>🎯 Match found at ${formatTimestamp(timestamp)}</strong>
                            <p class="matched-text">"${escapeHtml(result.matched_text)}"</p>
                        </div>
                    ` : ''}
                    <video controls class="result-video" id="${videoId}" data-timestamp="${timestamp}">
                        <source src="${escapeHtml(result.file_url)}" type="video/mp4">
                        Your browser does not support the video element.
                    </video>
                </div>
            `;
        } else if (result.modality === 'pdf') {
            // Show link to PDF with page finder
            const pdfId = result._id || result.id;
            mediaContent = `
                <div class="result-media">
                    <a href="${escapeHtml(result.file_url)}" target="_blank" class="file-link">
                        📄 Open PDF
                    </a>
                    <button class="find-pages-btn" data-pdf-id="${pdfId}" data-pdf-url="${escapeHtml(result.file_url)}">
                        🔍 Find Pages
                    </button>
                    <div class="pdf-pages-container" id="pages-${pdfId}" style="display: none;"></div>
                </div>
            `;
        }
    }

    card.innerHTML = `
        <div class="result-header">
            <div class="result-title">
                <h3>${escapeHtml(result.title)}</h3>
            </div>
            <div class="result-meta">
                <span class="result-badge">${modalityIcon} ${result.modality.toUpperCase()}</span>
                ${score ? `<span class="result-score">Score: ${score}%</span>` : ''}
            </div>
        </div>
        ${mediaContent}
        <div class="result-preview">
            ${escapeHtml(result.preview)}
        </div>
        <div class="result-footer">
            <div class="result-tags">
                ${result.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
            <div class="result-source">
                ${result.file_url ?
                    `<a href="${escapeHtml(result.file_url)}" target="_blank" class="source-link" title="Open ${escapeHtml(result.source_file)}">📁 ${escapeHtml(result.source_file)}</a>` :
                    `📁 ${escapeHtml(result.source_file)}`
                }
            </div>
        </div>
    `;

    // Set up audio timestamp seeking if this is an audio result
    if (result.modality === 'audio' && result.timestamp !== null && result.timestamp !== undefined) {
        const audioId = 'audio-' + (result._id || result.id || Math.random().toString(36).substr(2, 9));
        setTimeout(() => {
            const audioElement = card.querySelector(`#${audioId}`);
            if (audioElement) {
                audioElement.addEventListener('loadedmetadata', function() {
                    const timestamp = parseFloat(this.dataset.timestamp);
                    console.log('Audio loaded - seeking to timestamp:', timestamp);
                    this.currentTime = timestamp;
                    console.log('Audio currentTime set to:', this.currentTime);
                    // Don't auto-play - let user press play
                });
            }
        }, 0);
    }

    // Set up video timestamp seeking if this is a video result
    if (result.modality === 'video' && result.timestamp !== null && result.timestamp !== undefined) {
        const videoId = 'video-' + (result._id || result.id || Math.random().toString(36).substr(2, 9));
        setTimeout(() => {
            const videoElement = card.querySelector(`#${videoId}`);
            if (videoElement) {
                videoElement.addEventListener('loadedmetadata', function() {
                    const timestamp = parseFloat(this.dataset.timestamp);
                    console.log('Video loaded - seeking to timestamp:', timestamp);
                    this.currentTime = timestamp;
                    console.log('Video currentTime set to:', this.currentTime);
                    // Don't auto-play - let user press play
                });
            }
        }, 0);
    }

    // Set up PDF page finder if this is a PDF result
    if (result.modality === 'pdf') {
        setTimeout(() => {
            const findPagesBtn = card.querySelector('.find-pages-btn');
            console.log('PDF result - setting up Find Pages button:', findPagesBtn);
            if (findPagesBtn) {
                console.log('Button found, adding click listener');
                findPagesBtn.addEventListener('click', async function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Find Pages button clicked!');
                    const pdfId = this.dataset.pdfId;
                    const pdfUrl = this.dataset.pdfUrl;
                    const container = document.getElementById(`pages-${pdfId}`);
                    const currentQuery = document.getElementById('search-input').value;

                    console.log('PDF ID:', pdfId);
                    console.log('Query:', currentQuery);

                    // Toggle visibility
                    if (container.style.display === 'block') {
                        container.style.display = 'none';
                        this.textContent = '🔍 Find Pages';
                        return;
                    }

                    // Show loading
                    this.textContent = '⏳ Finding pages...';
                    this.disabled = true;

                    try {
                        const url = `${API_BASE_URL}/pdf-pages/${pdfId}?query=${encodeURIComponent(currentQuery)}`;
                        console.log('Fetching:', url);

                        const response = await fetch(url);
                        console.log('Response status:', response.status);

                        const data = await response.json();
                        console.log('Response data:', data);

                        if (data.matching_pages && data.matching_pages.length > 0) {
                            // Build pages list
                            let pagesHTML = `
                                <div class="pdf-pages-result">
                                    <strong>📄 Found on ${data.match_count} pages (Total: ${data.total_pages} pages)</strong>
                                    <ul class="pages-list">
                            `;

                            data.matching_pages.slice(0, 10).forEach(page => {
                                // Use custom PDF viewer that supports page navigation and highlighting
                                const viewerUrl = `pdf-viewer.html?file=${encodeURIComponent(pdfUrl)}&page=${page.page}&query=${encodeURIComponent(currentQuery)}`;
                                pagesHTML += `
                                    <li class="page-match" onclick="window.open('${viewerUrl}', '_blank')" style="cursor: pointer;">
                                        <div class="page-header">
                                            <strong>📄 Page ${page.page}</strong>
                                            <span class="page-hint">Click anywhere to open</span>
                                        </div>
                                        <div class="page-excerpt">${escapeHtml(page.excerpt)}</div>
                                    </li>
                                `;
                            });

                            pagesHTML += `</ul></div>`;
                            container.innerHTML = pagesHTML;
                            container.style.display = 'block';
                            this.textContent = '🔍 Hide Pages';
                        } else {
                            container.innerHTML = '<div class="pdf-pages-result">No matching pages found</div>';
                            container.style.display = 'block';
                            this.textContent = '🔍 Hide Pages';
                        }
                    } catch (error) {
                        console.error('Error finding PDF pages:', error);
                        container.innerHTML = '<div class="pdf-pages-result error">Error finding pages</div>';
                        container.style.display = 'block';
                    } finally {
                        this.disabled = false;
                    }
                });
            }
        }, 0);
    }

    return card;
}

// Upload form handlers
function handleModalityChange() {
    const modality = uploadModality.value;

    // Hide all conditional fields
    captionGroup.style.display = 'none';
    transcriptGroup.style.display = 'none';

    // Show relevant field
    if (modality === 'image') {
        captionGroup.style.display = 'block';
        document.getElementById('upload-caption').required = true;
        document.getElementById('upload-transcript').required = false;
    } else if (modality === 'audio') {
        transcriptGroup.style.display = 'block';
        document.getElementById('upload-transcript').required = false;  // NOT required - auto-transcribes
        document.getElementById('upload-caption').required = false;
    } else {
        document.getElementById('upload-caption').required = false;
        document.getElementById('upload-transcript').required = false;
    }
}

async function handleUpload(e) {
    e.preventDefault();

    const file = uploadFile.files[0];
    if (!file) {
        showUploadStatus('Please select a file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', document.getElementById('upload-title').value);
    formData.append('modality', uploadModality.value);
    formData.append('tags', document.getElementById('upload-tags').value);

    if (uploadModality.value === 'image') {
        formData.append('caption', document.getElementById('upload-caption').value);
    } else if (uploadModality.value === 'audio') {
        formData.append('transcript', document.getElementById('upload-transcript').value);
    }

    try {
        document.getElementById('upload-btn').disabled = true;

        // Show different message for audio (transcription takes time)
        const isAudio = uploadModality.value === 'audio';
        const transcript = document.getElementById('upload-transcript').value.trim();

        if (isAudio && !transcript) {
            showUploadStatus('🎤 Uploading and auto-transcribing audio... This may take 1-2 minutes.', 'info');
        } else {
            showUploadStatus('Uploading and embedding...', 'info');
        }

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();
        showUploadStatus(`✓ ${data.message}`, 'success');
        resetUploadForm();

    } catch (error) {
        console.error('Upload error:', error);
        showUploadStatus(`✗ Upload failed: ${error.message}`, 'error');
    } finally {
        document.getElementById('upload-btn').disabled = false;
    }
}

function resetUploadForm() {
    uploadForm.reset();
    captionGroup.style.display = 'none';
    transcriptGroup.style.display = 'none';
    uploadStatus.classList.add('hidden');
}

function showUploadStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = type;
    uploadStatus.classList.remove('hidden');
}

// UI state management
function showLoading() {
    hideAllStates();
    loadingState.classList.remove('hidden');
}

function showError(message) {
    hideAllStates();
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
}

function hideAllStates() {
    welcomeState.classList.add('hidden');
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultsList.classList.add('hidden');
}

// Utilities
function getModalityIcon(modality) {
    const icons = {
        'pdf': '📄',
        'audio': '🎵',
        'video': '🎬',
        'image': '🖼️'
    };
    return icons[modality] || '📎';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimestamp(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Browse functionality
async function loadAllDocuments() {
    try {
        showBrowseLoading();

        const response = await fetch(`${API_BASE_URL}/documents`);

        if (!response.ok) {
            throw new Error(`Failed to load documents: ${response.statusText}`);
        }

        const data = await response.json();
        allDocuments = data.documents;
        displayBrowseDocuments();

    } catch (error) {
        console.error('Browse error:', error);
        showBrowseError(error.message || 'Failed to load documents. Please check your connection.');
    }
}

function displayBrowseDocuments() {
    hideBrowseStates();

    let filteredDocs = allDocuments;
    if (currentBrowseFilter !== 'all') {
        filteredDocs = allDocuments.filter(doc => doc.modality === currentBrowseFilter);
    }

    if (filteredDocs.length === 0) {
        browseList.innerHTML = '<div class="browse-empty"><h3>No documents found</h3><p>No documents match the current filter.</p></div>';
        browseList.classList.remove('hidden');
        return;
    }

    browseList.innerHTML = '';
    browseList.classList.remove('hidden');

    filteredDocs.forEach(doc => {
        const card = createBrowseCard(doc);
        browseList.appendChild(card);
    });
}

function createBrowseCard(doc) {
    const card = document.createElement('div');
    card.className = 'browse-card';

    const modalityIcon = getModalityIcon(doc.modality);
    const preview = doc.preview || 'No preview available';
    const tags = doc.tags || [];

    // Build media content
    let mediaContent = '';
    if (doc.file_url) {
        if (doc.modality === 'image') {
            mediaContent = `
                <div class="result-media">
                    <img src="${escapeHtml(doc.file_url)}" alt="${escapeHtml(doc.title)}" class="result-image">
                </div>
            `;
        } else if (doc.modality === 'audio') {
            mediaContent = `
                <div class="result-media">
                    <audio controls class="result-audio">
                        <source src="${escapeHtml(doc.file_url)}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            `;
        } else if (doc.modality === 'video') {
            mediaContent = `
                <div class="result-media">
                    <video controls class="result-video">
                        <source src="${escapeHtml(doc.file_url)}" type="video/mp4">
                        Your browser does not support the video element.
                    </video>
                </div>
            `;
        } else if (doc.modality === 'pdf') {
            mediaContent = `
                <div class="result-media">
                    <a href="${escapeHtml(doc.file_url)}" target="_blank" class="file-link">
                        📄 Open PDF
                    </a>
                </div>
            `;
        }
    }

    card.innerHTML = `
        <div class="browse-card-header">
            <div class="browse-card-title">
                <h3>${escapeHtml(doc.title)}</h3>
            </div>
            <div class="browse-card-actions">
                <span class="browse-card-badge result-badge">${modalityIcon} ${doc.modality.toUpperCase()}</span>
                <button class="delete-btn" data-id="${escapeHtml(doc._id)}" data-title="${escapeHtml(doc.title)}" title="Delete document">
                    🗑️
                </button>
            </div>
        </div>
        ${mediaContent}
        <div class="browse-card-content">
            <p class="browse-card-preview">${escapeHtml(preview)}</p>
        </div>
        <div class="browse-card-footer">
            <div class="browse-card-tags">
                ${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
            <div class="browse-card-source">
                📁 ${escapeHtml(doc.source_file)}
            </div>
        </div>
    `;

    // Add delete handler
    const deleteBtn = card.querySelector('.delete-btn');
    deleteBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const docId = deleteBtn.dataset.id;
        const docTitle = deleteBtn.dataset.title;

        if (confirm(`Are you sure you want to delete "${docTitle}"?\n\nThis action cannot be undone.`)) {
            await deleteDocument(docId, card);
        }
    });

    return card;
}

async function deleteDocument(docId, cardElement) {
    try {
        const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`Delete failed: ${response.statusText}`);
        }

        const data = await response.json();

        // Remove card from UI with animation
        cardElement.style.opacity = '0';
        cardElement.style.transform = 'scale(0.9)';
        setTimeout(() => {
            cardElement.remove();

            // Update the document list
            allDocuments = allDocuments.filter(doc => doc._id !== docId);

            // Show empty message if no documents left
            if (allDocuments.length === 0) {
                displayBrowseDocuments();
            }
        }, 300);

        console.log(data.message);

    } catch (error) {
        console.error('Delete error:', error);
        alert(`Failed to delete document: ${error.message}`);
    }
}

function showBrowseLoading() {
    hideBrowseStates();
    browseLoading.classList.remove('hidden');
}

function showBrowseError(message) {
    hideBrowseStates();
    browseErrorMessage.textContent = message;
    browseError.classList.remove('hidden');
}

function hideBrowseStates() {
    browseLoading.classList.add('hidden');
    browseError.classList.add('hidden');
    browseList.classList.add('hidden');
}

// Timestamp seeking is now handled in createResultCard() function above
// No auto-play - user must press play button manually
