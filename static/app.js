/**
 * OmniExtract — Universal Any Video Downloader
 * Frontend Client Controller v2.0
 * Supports 1080p to 144p Video Downloads & Studio Audio (up to 320 kbps MP3)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mode Elements
  const btnModeSingle = document.getElementById('btn-mode-single');
  const btnModeBatch = document.getElementById('btn-mode-batch');
  const singleForm = document.getElementById('extract-form');
  const batchForm = document.getElementById('batch-extract-form');
  const singleSamplesBar = document.getElementById('single-samples-bar');

  // Single Form Elements
  const inputUrl = document.getElementById('fb-url-input');
  const btnPaste = document.getElementById('btn-paste-clipboard');
  const btnClear = document.getElementById('btn-clear-input');
  const btnSubmit = document.getElementById('btn-extract-submit');
  const spinner = document.getElementById('submit-spinner');
  const btnText = btnSubmit.querySelector('.btn-text');
  const btnArrow = btnSubmit.querySelector('.btn-arrow');

  // Batch Form Elements
  const batchUrlsInput = document.getElementById('batch-urls-input');
  const batchDetectedCount = document.getElementById('batch-urls-detected-count');
  const btnBatchPaste = document.getElementById('btn-batch-paste');
  const btnBatchClear = document.getElementById('btn-batch-clear');
  const btnBatchSubmit = document.getElementById('btn-batch-submit');
  const batchSpinner = document.getElementById('batch-spinner');
  const btnBatchText = btnBatchSubmit.querySelector('.btn-batch-text');

  // Result Zones
  const alertBanner = document.getElementById('alert-banner');
  const resultsZone = document.getElementById('results-zone');
  const batchResultsZone = document.getElementById('batch-results-zone');

  // Single Header Overview Elements
  const authorAvatar = document.getElementById('author-avatar');
  const avatarFallback = document.getElementById('author-avatar-fallback');
  const authorName = document.getElementById('author-name');
  const postTitle = document.getElementById('post-title');
  const badgePlatform = document.getElementById('badge-platform');
  const badgeMaxRes = document.getElementById('badge-max-res');
  const badgeDuration = document.getElementById('badge-duration');
  const badgeViews = document.getElementById('badge-views');
  const btnQuickDownloadBest = document.getElementById('btn-quick-download-best');
  const btnQuickDownloadAudio = document.getElementById('btn-quick-download-audio');
  const btnOpenOriginal = document.getElementById('btn-open-original');

  // Tabs Elements
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  // Content Panes
  const videoFormatsGrid = document.getElementById('video-formats-grid');
  const audioFormatsGrid = document.getElementById('audio-formats-grid');
  const playerPreviewVideo = document.getElementById('player-preview-video');
  const playerEmptyNote = document.getElementById('player-empty-note');
  const imagesGrid = document.getElementById('images-grid');
  const imagesEmpty = document.getElementById('images-empty');
  const postTextContent = document.getElementById('post-text-content');
  const statWords = document.getElementById('stat-words');
  const statChars = document.getElementById('stat-chars');
  const btnCopyText = document.getElementById('btn-copy-text');
  const rawJsonViewer = document.getElementById('raw-json-viewer');
  const btnCopyJson = document.getElementById('btn-copy-json');

  // Batch Results Elements
  const badgeBatchCount = document.getElementById('badge-batch-count');
  const batchChaptersList = document.getElementById('batch-chapters-list');

  // History Elements
  const btnShowHistory = document.getElementById('btn-show-history');
  const historyModal = document.getElementById('history-modal');
  const btnCloseHistory = document.getElementById('btn-close-history');
  const historyList = document.getElementById('history-list');
  const btnClearHistory = document.getElementById('btn-clear-history');
  const historyCount = document.getElementById('history-count');

  // Share Modal Elements
  const btnShowShare = document.getElementById('btn-show-share');
  const shareModal = document.getElementById('share-modal');
  const btnCloseShare = document.getElementById('btn-close-share');
  const btnCopyPublicUrl = document.getElementById('btn-copy-public-url');
  const btnCopyLanUrl = document.getElementById('btn-copy-lan-url');
  const publicUrlInput = document.getElementById('public-url-input');
  const lanUrlInput = document.getElementById('lan-url-input');

  // Lightbox Elements
  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxImg = document.getElementById('lightbox-img');
  const btnCloseLightbox = document.getElementById('btn-close-lightbox');
  const lightboxDownload = document.getElementById('lightbox-download');
  const lightboxOpen = document.getElementById('lightbox-open');

  // State
  let currentExtractionData = null;

  // Initialize
  updateHistoryCounter();
  loadNetworkInfo();

  // Mode Switchers
  btnModeSingle.addEventListener('click', () => setMode('single'));
  btnModeBatch.addEventListener('click', () => setMode('batch'));

  function setMode(mode) {
    if (mode === 'single') {
      btnModeSingle.classList.add('active');
      btnModeBatch.classList.remove('active');
      singleForm.classList.remove('hidden');
      batchForm.classList.add('hidden');
      singleSamplesBar.classList.remove('hidden');
      batchResultsZone.classList.add('hidden');
    } else {
      btnModeBatch.classList.add('active');
      btnModeSingle.classList.remove('active');
      singleForm.classList.add('hidden');
      batchForm.classList.remove('hidden');
      singleSamplesBar.classList.add('hidden');
      resultsZone.classList.add('hidden');
    }
  }

  // Single Input UI events
  inputUrl.addEventListener('input', () => {
    if (inputUrl.value.trim().length > 0) {
      btnClear.classList.remove('hidden');
    } else {
      btnClear.classList.add('hidden');
    }
  });

  btnClear.addEventListener('click', () => {
    inputUrl.value = '';
    btnClear.classList.add('hidden');
    inputUrl.focus();
  });

  btnPaste.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        const urls = extractUrlsFromText(text);
        if (urls.length > 1) {
          batchUrlsInput.value = text.trim();
          updateBatchCount();
          setMode('batch');
          showToast(`Pasted ${urls.length} video links into Batch Queue!`);
        } else {
          inputUrl.value = text.trim();
          btnClear.classList.remove('hidden');
          showToast('Video link pasted from clipboard');
          inputUrl.focus();
        }
      }
    } catch {
      showToast('Could not access clipboard. Please paste manually.', 'warning');
    }
  });

  // Batch Input events
  batchUrlsInput.addEventListener('input', updateBatchCount);

  function updateBatchCount() {
    const text = batchUrlsInput.value;
    const urls = extractUrlsFromText(text);
    batchDetectedCount.textContent = urls.length;
  }

  btnBatchPaste.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        batchUrlsInput.value = text.trim();
        updateBatchCount();
        showToast('Pasted into batch queue');
      }
    } catch {
      showToast('Could not access clipboard. Please paste manually.', 'warning');
    }
  });

  btnBatchClear.addEventListener('click', () => {
    batchUrlsInput.value = '';
    updateBatchCount();
  });

  // Quick Sample buttons
  document.querySelectorAll('.sample-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const sampleUrl = btn.getAttribute('data-url');
      inputUrl.value = sampleUrl;
      btnClear.classList.remove('hidden');
      setMode('single');
      performExtraction(sampleUrl);
    });
  });

  // Single Form submit
  singleForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const url = inputUrl.value.trim();
    if (!url) return;
    performExtraction(url);
  });

  // Batch Form submit
  batchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = batchUrlsInput.value.trim();
    const urls = extractUrlsFromText(text);
    if (urls.length === 0) {
      showAlert('No valid video links detected. Please paste URLs.', 'error');
      return;
    }
    performBatchExtraction(text, urls);
  });

  // Perform Single Video Extraction
  async function performExtraction(url) {
    setLoading(true);
    hideAlert();
    resultsZone.classList.add('hidden');
    batchResultsZone.classList.add('hidden');

    try {
      const response = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to extract video information from this URL.');
      }

      currentExtractionData = data;
      renderResults(data);
      saveToHistory(data);
      updateHistoryCounter();
      showToast('Video extracted successfully!');

      setTimeout(() => {
        resultsZone.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      showAlert(err.message || 'An error occurred while extracting video details.', 'error');
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    if (isLoading) {
      btnSubmit.disabled = true;
      spinner.classList.remove('hidden');
      btnText.textContent = 'Extracting Video...';
      btnArrow.classList.add('hidden');
    } else {
      btnSubmit.disabled = false;
      spinner.classList.add('hidden');
      btnText.textContent = 'Download Video';
      btnArrow.classList.remove('hidden');
    }
  }

  // Batch Extraction
  async function performBatchExtraction(rawText, urls) {
    setBatchLoading(true);
    hideAlert();
    batchResultsZone.classList.add('hidden');

    try {
      const response = await fetch('/api/extract-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: rawText, urls: urls })
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Batch extraction failed.');
      }

      renderBatchResults(data);
      showToast(`Extracted ${data.total_extracted} videos!`);
      setTimeout(() => {
        batchResultsZone.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      showAlert(err.message || 'Batch extraction error', 'error');
    } finally {
      setBatchLoading(false);
    }
  }

  function setBatchLoading(isLoading) {
    if (isLoading) {
      btnBatchSubmit.disabled = true;
      batchSpinner.classList.remove('hidden');
      btnBatchText.textContent = 'Fetching Batch...';
    } else {
      btnBatchSubmit.disabled = false;
      batchSpinner.classList.add('hidden');
      btnBatchText.textContent = 'Fetch All Videos';
    }
  }

  // Render Single Results
  function renderResults(data) {
    resultsZone.classList.remove('hidden');

    // Header info
    authorName.textContent = data.uploader || (data.author && data.author.name) || 'Video Creator';
    postTitle.textContent = data.title || data.url;
    btnOpenOriginal.href = data.url;

    // Platform Badge
    const platform = data.platform || { name: 'Video', color: '#e11d48' };
    badgePlatform.textContent = platform.name;
    if (platform.color) {
      badgePlatform.style.background = platform.color;
    }

    // Header stats
    badgeMaxRes.textContent = data.max_resolution || '1080p Full HD';
    badgeDuration.textContent = data.duration_string || 'N/A';
    badgeViews.textContent = data.view_count ? `${Number(data.view_count).toLocaleString()} views` : 'Online Video';

    // Thumbnail / Avatar
    if (data.thumbnail) {
      authorAvatar.src = data.thumbnail;
      authorAvatar.classList.remove('hidden');
      avatarFallback.classList.add('hidden');
    } else {
      authorAvatar.classList.add('hidden');
      avatarFallback.classList.remove('hidden');
      avatarFallback.textContent = '▶';
    }

    // Quick download buttons
    const safeTitle = encodeURIComponent((data.title || 'video').substring(0, 50));
    btnQuickDownloadBest.href = `/api/download-video?url=${encodeURIComponent(data.url)}&quality=best&title=${safeTitle}`;
    btnQuickDownloadAudio.href = `/api/download-audio?url=${encodeURIComponent(data.url)}&bitrate=320&title=${safeTitle}`;

    // Render Video Formats Tab
    renderVideoFormats(data);

    // Render Audio Formats Tab
    renderAudioFormats(data);

    // Render Player Tab
    renderPlayerTab(data);

    // Render Thumbnails Tab
    renderImagesTab(data.images || (data.thumbnail ? [{ url: data.thumbnail, label: 'HD Poster' }] : []));

    // Render Description Tab
    renderTextTab(data.text || data.description || '');

    // Render JSON Tab
    rawJsonViewer.textContent = JSON.stringify(data, null, 2);

    // Default activate video tab
    switchTab('tab-videos');
  }

  // Render Video Downloads (1080p, 720p, 480p, 360p, 240p, 144p, Best)
  function renderVideoFormats(data) {
    videoFormatsGrid.innerHTML = '';
    const formats = data.video_downloads || [];
    const safeTitle = encodeURIComponent((data.title || 'video').substring(0, 50));

    if (formats.length === 0) {
      videoFormatsGrid.innerHTML = `<p class="empty-state">No direct video streams discovered. Try downloading best quality directly.</p>`;
      return;
    }

    formats.forEach(f => {
      const card = document.createElement('div');
      card.className = `format-card ${f.is_best ? 'best-card' : ''}`;

      const resBadgeClass = f.is_best ? 'format-pill pill-best' : 'format-pill';
      const downloadLink = `/api/download-video?url=${encodeURIComponent(data.url)}&quality=${f.quality}&title=${safeTitle}`;

      card.innerHTML = `
        <div>
          <div class="format-card-top">
            <span class="format-res-name">${f.resolution}</span>
            <span class="${resBadgeClass}">${f.badge || 'MP4'}</span>
          </div>
          <div class="format-meta-row">
            <span>Format: <strong>${(f.extension || 'mp4').toUpperCase()}</strong></span>
            ${f.filesize ? `<span>Size: <strong>${f.filesize}</strong></span>` : ''}
          </div>
        </div>
        <div>
          <a href="${downloadLink}" class="btn-format-download" download>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>Download ${f.resolution}</span>
          </a>
        </div>
      `;
      videoFormatsGrid.appendChild(card);
    });
  }

  // Render Audio Downloads (320k, 256k, 192k, 128k MP3)
  function renderAudioFormats(data) {
    audioFormatsGrid.innerHTML = '';
    const audios = data.audio_downloads || [];
    const safeTitle = encodeURIComponent((data.title || 'audio').substring(0, 50));

    audios.forEach(a => {
      const card = document.createElement('div');
      card.className = `format-card ${a.is_best ? 'best-card' : ''}`;

      const downloadLink = `/api/download-audio?url=${encodeURIComponent(data.url)}&bitrate=${a.bitrate}&title=${safeTitle}`;

      card.innerHTML = `
        <div>
          <div class="format-card-top">
            <span class="format-res-name">${a.label}</span>
            <span class="format-pill pill-audio">${a.badge || 'MP3'}</span>
          </div>
          <div class="format-meta-row">
            <span>Codec: <strong>MP3 Audio</strong></span>
            <span>Bitrate: <strong>${a.bitrate} kbps</strong></span>
          </div>
        </div>
        <div>
          <a href="${downloadLink}" class="btn-format-download btn-audio" download>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18V5l12-2v13"></path>
              <circle cx="6" cy="18" r="3"></circle>
              <circle cx="18" cy="16" r="3"></circle>
            </svg>
            <span>Download ${a.badge} MP3</span>
          </a>
        </div>
      `;
      audioFormatsGrid.appendChild(card);
    });
  }

  // Render Player Tab
  function renderPlayerTab(data) {
    if (data.preview_url) {
      playerPreviewVideo.src = data.preview_url;
      playerPreviewVideo.parentElement.classList.remove('hidden');
      playerEmptyNote.classList.add('hidden');
    } else {
      playerPreviewVideo.removeAttribute('src');
      playerPreviewVideo.parentElement.classList.add('hidden');
      playerEmptyNote.classList.remove('hidden');
    }
  }

  // Render Images Tab (Thumbnails / Posters)
  function renderImagesTab(images) {
    imagesGrid.innerHTML = '';
    if (!images || images.length === 0) {
      imagesEmpty.classList.remove('hidden');
      return;
    }
    imagesEmpty.classList.add('hidden');

    images.forEach((img, idx) => {
      const card = document.createElement('div');
      card.className = 'gallery-card';

      const directUrl = img.url || img;
      const downloadUrl = `/api/download?url=${encodeURIComponent(directUrl)}&filename=poster_${idx+1}.jpg`;

      card.innerHTML = `
        <div class="card-img-wrap">
          <img src="${img.proxy_url || directUrl}" alt="Video Poster" loading="lazy" referrerpolicy="no-referrer">
          <div class="img-overlay-zoom">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="11" y1="8" x2="11" y2="14"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </div>
        </div>
        <div class="card-info-bar">
          <span class="card-img-label">${img.label || `Poster #${idx+1}`}</span>
          <div class="card-action-btns">
            <a href="${downloadUrl}" class="btn-card-action" title="Download Poster" download>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </a>
          </div>
        </div>
      `;

      card.querySelector('.card-img-wrap').addEventListener('click', () => openLightbox(directUrl, downloadUrl));
      imagesGrid.appendChild(card);
    });
  }

  // Render Description Tab
  function renderTextTab(text) {
    if (!text || text.trim() === '') {
      postTextContent.innerHTML = '<span style="color: var(--text-muted); font-style: italic;">No description detected for this video.</span>';
      statWords.textContent = '0 words';
      statChars.textContent = '0 characters';
      return;
    }

    const words = text.trim().split(/\s+/).filter(Boolean).length;
    statWords.textContent = `${words} words`;
    statChars.textContent = `${text.length} characters`;

    const escaped = escapeHtml(text);
    const linkified = escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    postTextContent.innerHTML = linkified;
  }

  // Render Batch Results
  function renderBatchResults(batchData) {
    batchResultsZone.classList.remove('hidden');
    const results = batchData.results || [];
    badgeBatchCount.textContent = `${results.length} Videos Extracted`;
    batchChaptersList.innerHTML = '';

    results.forEach((item, idx) => {
      const card = document.createElement('div');
      card.className = 'chapter-card';

      const safeTitle = encodeURIComponent((item.title || `video_${idx+1}`).substring(0, 50));
      const downloadVid = `/api/download-video?url=${encodeURIComponent(item.url)}&quality=best&title=${safeTitle}`;
      const downloadAud = `/api/download-audio?url=${encodeURIComponent(item.url)}&bitrate=320&title=${safeTitle}`;

      card.innerHTML = `
        <div class="chapter-header" style="cursor:default;">
          <div class="chapter-title-group">
            <span class="chapter-idx">#${idx+1}</span>
            <strong class="chapter-title">${escapeHtml(item.title || item.url)}</strong>
            <span class="format-pill pill-best" style="margin-left:8px;">${item.max_resolution || 'HD'}</span>
          </div>
          <div class="card-action-btns">
            <a href="${downloadVid}" class="btn-primary-sm" style="text-decoration:none;" download>Download MP4</a>
            <a href="${downloadAud}" class="btn-secondary-sm" style="text-decoration:none;" download>MP3 320k</a>
          </div>
        </div>
      `;
      batchChaptersList.appendChild(card);
    });
  }

  // Copy Buttons
  btnCopyText.addEventListener('click', () => {
    if (currentExtractionData && currentExtractionData.text) {
      navigator.clipboard.writeText(currentExtractionData.text);
      showToast('Description copied to clipboard');
    }
  });

  btnCopyJson.addEventListener('click', () => {
    if (currentExtractionData) {
      navigator.clipboard.writeText(JSON.stringify(currentExtractionData, null, 2));
      showToast('JSON copied to clipboard');
    }
  });

  // Tab switching logic
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  function switchTab(tabId) {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabPanes.forEach(p => p.classList.remove('active'));

    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    const activePane = document.getElementById(tabId);

    if (activeBtn) activeBtn.classList.add('active');
    if (activePane) activePane.classList.add('active');
  }

  // Lightbox
  function openLightbox(imgUrl, dlUrl) {
    lightboxImg.src = imgUrl;
    lightboxDownload.href = dlUrl;
    lightboxOpen.href = imgUrl;
    lightboxModal.classList.remove('hidden');
  }

  btnCloseLightbox.addEventListener('click', () => lightboxModal.classList.add('hidden'));
  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) lightboxModal.classList.add('hidden');
  });

  // History System
  function saveToHistory(item) {
    let hist = [];
    try {
      hist = JSON.parse(localStorage.getItem('omni_history') || '[]');
    } catch {}
    hist = hist.filter(h => h.url !== item.url);
    hist.unshift({
      url: item.url,
      title: item.title,
      uploader: item.uploader,
      platform: item.platform,
      thumbnail: item.thumbnail,
      timestamp: Date.now()
    });
    hist = hist.slice(0, 40);
    localStorage.setItem('omni_history', JSON.stringify(hist));
  }

  function updateHistoryCounter() {
    try {
      const hist = JSON.parse(localStorage.getItem('omni_history') || '[]');
      historyCount.textContent = hist.length;
    } catch {}
  }

  btnShowHistory.addEventListener('click', () => {
    renderHistoryModal();
    historyModal.classList.remove('hidden');
  });

  btnCloseHistory.addEventListener('click', () => historyModal.classList.add('hidden'));
  historyModal.addEventListener('click', (e) => {
    if (e.target === historyModal) historyModal.classList.add('hidden');
  });

  btnClearHistory.addEventListener('click', () => {
    localStorage.removeItem('omni_history');
    renderHistoryModal();
    updateHistoryCounter();
    showToast('History cleared');
  });

  function renderHistoryModal() {
    let hist = [];
    try {
      hist = JSON.parse(localStorage.getItem('omni_history') || '[]');
    } catch {}

    historyList.innerHTML = '';
    if (hist.length === 0) {
      historyList.innerHTML = '<p class="empty-state">No extraction history recorded yet.</p>';
      return;
    }

    hist.forEach(h => {
      const item = document.createElement('div');
      item.className = 'history-item';
      item.innerHTML = `
        <div class="history-item-info">
          <strong class="history-title">${escapeHtml(h.title || h.url)}</strong>
          <span class="history-meta">${escapeHtml(h.uploader || 'Creator')} &bull; ${new Date(h.timestamp).toLocaleDateString()}</span>
        </div>
        <button class="btn-primary-sm btn-re-extract" data-url="${h.url}">Open</button>
      `;
      item.querySelector('.btn-re-extract').addEventListener('click', () => {
        historyModal.classList.add('hidden');
        inputUrl.value = h.url;
        btnClear.classList.remove('hidden');
        setMode('single');
        performExtraction(h.url);
      });
      historyList.appendChild(item);
    });
  }

  // Network / Share modal
  async function loadNetworkInfo() {
    try {
      const resp = await fetch('/api/network-info');
      const data = await resp.json();
      if (data.lan_url) {
        lanUrlInput.value = data.lan_url;
      }
      if (data.public_url) {
        publicUrlInput.value = data.public_url;
      } else {
        publicUrlInput.value = 'https://omniextract-fb.onrender.com';
      }
    } catch {}
  }

  btnShowShare.addEventListener('click', () => {
    loadNetworkInfo();
    shareModal.classList.remove('hidden');
  });

  btnCloseShare.addEventListener('click', () => shareModal.classList.add('hidden'));
  shareModal.addEventListener('click', (e) => {
    if (e.target === shareModal) shareModal.classList.add('hidden');
  });

  btnCopyPublicUrl.addEventListener('click', () => {
    navigator.clipboard.writeText(publicUrlInput.value);
    showToast('Public URL copied to clipboard!');
  });

  btnCopyLanUrl.addEventListener('click', () => {
    navigator.clipboard.writeText(lanUrlInput.value);
    showToast('LAN Wi-Fi URL copied to clipboard!');
  });

  // Utilities
  function extractUrlsFromText(text) {
    if (!text) return [];
    const matches = text.match(/https?:\/\/[^\s<>"'\)]+/g);
    if (!matches) return [];
    return [...new Set(matches.map(u => u.replace(/[.,;:)]+$/, '')))];
  }

  function showAlert(msg, type = 'error') {
    alertBanner.className = `alert-banner ${type}`;
    alertBanner.innerHTML = msg;
    alertBanner.classList.remove('hidden');
  }

  function hideAlert() {
    alertBanner.classList.add('hidden');
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }
});
