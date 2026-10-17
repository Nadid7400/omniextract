/**
 * Omni Extractor — Universal Video & Audio Downloader
 * Frontend Client Controller v2.1
 * Dynamic Resolution Dropdowns, Audio Formats, and Clean Download Triggers
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
  const badgeAudioRes = document.getElementById('badge-audio-res');
  const btnQuickDownloadBest = document.getElementById('btn-quick-download-best');
  const btnQuickDownloadAudio = document.getElementById('btn-quick-download-audio');
  const btnOpenOriginal = document.getElementById('btn-open-original');

  // Interactive Quick Download Bar Elements
  const btnToggleVideo = document.getElementById('btn-toggle-video');
  const btnToggleAudio = document.getElementById('btn-toggle-audio');
  const downloadModeHint = document.getElementById('download-mode-hint');
  const groupVideoDropdown = document.getElementById('group-video-dropdown');
  const groupAudioDropdown = document.getElementById('group-audio-dropdown');
  const selectVideoResolution = document.getElementById('select-video-resolution');
  const selectAudioFormat = document.getElementById('select-audio-format');
  const btnLiveDownload = document.getElementById('btn-live-download');
  const liveDownloadLabel = document.getElementById('live-download-label');
  const liveDownloadSpinner = document.getElementById('live-download-spinner');

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
  let currentMediaMode = 'video'; // 'video' | 'audio'

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

  // Perform Single Video Extraction via /api/info
  async function performExtraction(url) {
    setLoading(true);
    hideAlert();
    resultsZone.classList.add('hidden');
    batchResultsZone.classList.add('hidden');

    try {
      // Call primary /api/info POST endpoint
      let response = await fetch('/api/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      if (!response.ok) {
        // Fallback to GET
        response = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
      }

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.error || 'Failed to extract video information from this URL.');
      }

      currentExtractionData = data;
      renderResults(data);
      populateDynamicDropdowns(data);
      saveToHistory(data);
      updateHistoryCounter();
      showToast('Video analyzed successfully!');

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
      btnText.textContent = 'Analyzing Link...';
      btnArrow.classList.add('hidden');
    } else {
      btnSubmit.disabled = false;
      spinner.classList.add('hidden');
      btnText.textContent = 'Analyze Link';
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
        throw new Error(data.detail || data.error || 'Batch extraction failed.');
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

    // Quick download buttons (using clean /api/download endpoint)
    const safeTitle = encodeURIComponent((data.title || 'video').substring(0, 50));
    const bestDlUrl = `/api/download?url=${encodeURIComponent(data.url)}&type=video&quality=best&title=${safeTitle}`;
    const audioDlUrl = `/api/download?url=${encodeURIComponent(data.url)}&type=audio&format=mp3&bitrate=320&title=${safeTitle}`;
    btnQuickDownloadBest.href = bestDlUrl;
    btnQuickDownloadAudio.href = audioDlUrl;
    btnQuickDownloadBest.onclick = (e) => {
      e.preventDefault();
      startMediaDownload(bestDlUrl, `${data.title || 'video'}.mp4`);
    };
    btnQuickDownloadAudio.onclick = (e) => {
      e.preventDefault();
      startMediaDownload(audioDlUrl, `${data.title || 'audio'}.mp3`);
    };

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

  // -------------------------------------------------------------
  // Dynamic Resolution & Audio Dropdown System
  // -------------------------------------------------------------
  function populateDynamicDropdowns(data) {
    // 1. Populate Video Resolutions Dropdown
    selectVideoResolution.innerHTML = '';
    const videoFormats = data.video_downloads || [];

    if (videoFormats.length > 0) {
      videoFormats.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.quality;
        const sizeInfo = v.filesize ? ` (~${v.filesize})` : '';
        const recInfo = v.is_best ? ' ★ Best Quality' : '';
        opt.textContent = `${v.resolution}${sizeInfo}${recInfo}`;
        selectVideoResolution.appendChild(opt);
      });
    } else {
      const opt = document.createElement('option');
      opt.value = 'best';
      opt.textContent = 'Best Quality (Auto-Detect)';
      selectVideoResolution.appendChild(opt);
    }

    // 2. Populate Audio Formats & Bitrates Dropdown
    selectAudioFormat.innerHTML = '';
    const audioFormats = data.audio_downloads || [];

    if (audioFormats.length > 0) {
      audioFormats.forEach(a => {
        const opt = document.createElement('option');
        opt.value = `${a.codec || 'mp3'}:${a.bitrate || '320'}`;
        const bestInfo = a.is_best ? ' ★ Recommended' : '';
        opt.textContent = `${a.label}${bestInfo}`;
        selectAudioFormat.appendChild(opt);
      });
    } else {
      const opt = document.createElement('option');
      opt.value = 'mp3:320';
      opt.textContent = 'MP3 Studio (320 kbps CBR)';
      selectAudioFormat.appendChild(opt);
    }

    // Reset mode to Video
    setMediaDownloadMode('video');
  }

  // Video / Audio Mode Switcher in Quick Download Bar
  btnToggleVideo.addEventListener('click', () => setMediaDownloadMode('video'));
  btnToggleAudio.addEventListener('click', () => setMediaDownloadMode('audio'));

  function setMediaDownloadMode(mode) {
    currentMediaMode = mode;
    if (mode === 'video') {
      btnToggleVideo.classList.add('active');
      btnToggleAudio.classList.remove('active', 'active-audio');
      groupVideoDropdown.classList.remove('hidden');
      groupAudioDropdown.classList.add('hidden');
      btnLiveDownload.classList.remove('btn-audio-mode');
      downloadModeHint.textContent = 'Live dynamic resolutions detected for this video:';
      updateLiveDownloadButtonText();
    } else {
      btnToggleAudio.classList.add('active', 'active-audio');
      btnToggleVideo.classList.remove('active');
      groupAudioDropdown.classList.remove('hidden');
      groupVideoDropdown.classList.add('hidden');
      btnLiveDownload.classList.add('btn-audio-mode');
      downloadModeHint.textContent = 'Master studio audio extraction (up to 320 kbps MP3, M4A, FLAC, WAV):';
      updateLiveDownloadButtonText();
    }
  }

  selectVideoResolution.addEventListener('change', updateLiveDownloadButtonText);
  selectAudioFormat.addEventListener('change', updateLiveDownloadButtonText);

  function updateLiveDownloadButtonText() {
    if (currentMediaMode === 'video') {
      const selOpt = selectVideoResolution.options[selectVideoResolution.selectedIndex];
      const optText = selOpt ? selOpt.textContent.split('(')[0].trim() : 'Video';
      liveDownloadLabel.textContent = `Download ${optText} MP4`;
    } else {
      const selOpt = selectAudioFormat.options[selectAudioFormat.selectedIndex];
      const optText = selOpt ? selOpt.textContent.split('(')[0].trim() : 'Audio';
      liveDownloadLabel.textContent = `Download ${optText}`;
    }
  }

  // -------------------------------------------------------------
  // Robust Universal Media Downloader with Live Progress & Error Handling
  // -------------------------------------------------------------
  async function startMediaDownload(downloadUrl, mediaName = 'media') {
    hideAlert();
    showToast(`⚡ Server is preparing ${mediaName}... Please wait!`, 'info');

    // Visual feedback on button
    btnLiveDownload.disabled = true;
    liveDownloadSpinner.classList.remove('hidden');
    liveDownloadLabel.textContent = 'Server converting...';

    try {
      const response = await fetch(downloadUrl);

      if (!response.ok) {
        let errorMsg = 'Download failed on server.';
        try {
          const errJson = await response.json();
          errorMsg = errJson.detail || errJson.error || errorMsg;
        } catch {
          errorMsg = await response.text() || errorMsg;
        }
        throw new Error(errorMsg);
      }

      liveDownloadLabel.textContent = 'Receiving file...';
      const blob = await response.blob();

      // Extract filename from Content-Disposition header if available
      let outFileName = mediaName;
      const disposition = response.headers.get('content-disposition');
      if (disposition && disposition.includes('filename=')) {
        const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          outFileName = match[1].replace(/['"]/g, '').trim();
        }
      }

      // Create blob URL and trigger clean single download
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = outFileName;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        a.remove();
        window.URL.revokeObjectURL(blobUrl);
      }, 1000);

      showToast(`✅ ${outFileName} downloaded successfully!`, 'success');

    } catch (err) {
      console.error('Download error:', err);
      showAlert(`Download Error: ${err.message}`, 'error');
      showToast(`Download failed: ${err.message}`, 'error');
    } finally {
      btnLiveDownload.disabled = false;
      liveDownloadSpinner.classList.add('hidden');
      updateLiveDownloadButtonText();
    }
  }

  // Clean Download Trigger Execution
  btnLiveDownload.addEventListener('click', () => triggerLiveDownload());

  function triggerLiveDownload() {
    if (!currentExtractionData || !currentExtractionData.url) {
      showToast('No active video to download.', 'warning');
      return;
    }

    const rawTitle = currentExtractionData.title || 'media';
    const safeTitle = encodeURIComponent(rawTitle.substring(0, 60));
    let downloadUrl = '';
    let targetName = '';

    if (currentMediaMode === 'video') {
      const quality = selectVideoResolution.value || 'best';
      downloadUrl = `/api/download?url=${encodeURIComponent(currentExtractionData.url)}&type=video&quality=${quality}&title=${safeTitle}`;
      targetName = `${rawTitle}.mp4`;
    } else {
      const val = selectAudioFormat.value || 'mp3:320';
      const [format, bitrate] = val.split(':');
      downloadUrl = `/api/download?url=${encodeURIComponent(currentExtractionData.url)}&type=audio&format=${format}&bitrate=${bitrate}&title=${safeTitle}`;
      targetName = `${rawTitle}.${format || 'mp3'}`;
    }

    startMediaDownload(downloadUrl, targetName);
  }

  // -------------------------------------------------------------
  // Render Video Formats Grid Tab
  // -------------------------------------------------------------
  function renderVideoFormats(data) {
    videoFormatsGrid.innerHTML = '';
    const formats = data.video_downloads || [];
    formats.forEach(f => {
      const card = document.createElement('div');
      card.className = `format-card ${f.is_best ? 'best-card' : ''}`;

      const resBadgeClass = f.is_best ? 'format-pill pill-best' : 'format-pill';
      const downloadLink = `/api/download?url=${encodeURIComponent(data.url)}&type=video&quality=${f.quality}&title=${safeTitle}`;

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
          <button type="button" class="btn-format-download">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>Download ${f.resolution}</span>
          </button>
        </div>
      `;

      const btnDl = card.querySelector('.btn-format-download');
      btnDl.addEventListener('click', (e) => {
        e.preventDefault();
        startMediaDownload(downloadLink, `${data.title || 'video'}_${f.quality}p.mp4`);
      });

      videoFormatsGrid.appendChild(card);
    });
  }

  // -------------------------------------------------------------
  // Render Audio Formats Grid Tab
  // -------------------------------------------------------------
  function renderAudioFormats(data) {
    audioFormatsGrid.innerHTML = '';
    const audios = data.audio_downloads || [];
    audios.forEach(a => {
      const card = document.createElement('div');
      card.className = `format-card ${a.is_best ? 'best-card' : ''}`;

      const codec = a.codec || 'mp3';
      const bitrate = a.bitrate || '320';
      const downloadLink = `/api/download?url=${encodeURIComponent(data.url)}&type=audio&format=${codec}&bitrate=${bitrate}&title=${safeTitle}`;

      card.innerHTML = `
        <div>
          <div class="format-card-top">
            <span class="format-res-name">${a.label}</span>
            <span class="format-pill pill-audio">${a.badge || codec.toUpperCase()}</span>
          </div>
          <div class="format-meta-row">
            <span>Codec: <strong>${codec.toUpperCase()}</strong></span>
            <span>Quality: <strong>${bitrate === 'lossless' ? 'Lossless Hi-Res' : bitrate === 'uncompressed' ? 'PCM 16-bit' : `${bitrate} kbps`}</strong></span>
          </div>
          ${a.desc ? `<p style="font-size:0.82rem; color:var(--text-muted); margin-bottom:14px;">${a.desc}</p>` : ''}
        </div>
        <div>
          <button type="button" class="btn-format-download btn-audio">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18V5l12-2v13"></path>
              <circle cx="6" cy="18" r="3"></circle>
              <circle cx="18" cy="16" r="3"></circle>
            </svg>
            <span>Download ${a.badge}</span>
          </button>
        </div>
      `;

      const btnDl = card.querySelector('.btn-format-download');
      btnDl.addEventListener('click', (e) => {
        e.preventDefault();
        startMediaDownload(downloadLink, `${data.title || 'audio'}_${bitrate}k.${codec}`);
      });

      audioFormatsGrid.appendChild(card);
    });
  }

  // Render Watch Preview Player
  function renderPlayerTab(data) {
    if (data.preview_url) {
      playerPreviewVideo.src = data.preview_url;
      playerPreviewVideo.classList.remove('hidden');
      playerEmptyNote.classList.add('hidden');
    } else {
      playerPreviewVideo.pause();
      playerPreviewVideo.removeAttribute('src');
      playerPreviewVideo.classList.add('hidden');
      playerEmptyNote.classList.remove('hidden');
    }
  }

  // Render Thumbnails & Poster
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

      const directUrl = typeof img === 'string' ? img : img.url;
      const proxyUrl = (typeof img === 'object' && img.proxy_url) ? img.proxy_url : directUrl;
      const downloadUrl = `/api/download?direct_url=${encodeURIComponent(directUrl)}&filename=poster_${idx+1}.jpg`;
      const label = (typeof img === 'object' && img.label) ? img.label : `Poster #${idx+1}`;

      card.innerHTML = `
        <div class="card-img-wrap">
          <img src="${proxyUrl}" alt="${label}" referrerpolicy="no-referrer" loading="lazy">
          <div class="img-overlay">
            <span>Enlarge</span>
          </div>
        </div>
        <div class="gallery-card-body">
          <span class="gallery-img-type">${label}</span>
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

      card.querySelector('.card-img-wrap').addEventListener('click', () => openLightbox(proxyUrl, downloadUrl));
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
      const downloadVid = `/api/download?url=${encodeURIComponent(item.url)}&type=video&quality=best&title=${safeTitle}`;
      const downloadAud = `/api/download?url=${encodeURIComponent(item.url)}&type=audio&format=mp3&bitrate=320&title=${safeTitle}`;

      card.innerHTML = `
        <div class="chapter-header" style="cursor:default;">
          <div class="chapter-title-group">
            <span class="chapter-idx">#${idx+1}</span>
            <strong class="chapter-title">${escapeHtml(item.title || item.url)}</strong>
            <span class="format-pill pill-best" style="margin-left:8px;">${item.max_resolution || 'HD'}</span>
          </div>
          <div class="card-action-btns">
            <button type="button" class="btn-primary-sm btn-batch-dl-vid">Download MP4</button>
            <button type="button" class="btn-secondary-sm btn-batch-dl-aud">MP3 320k</button>
          </div>
        </div>
      `;

      card.querySelector('.btn-batch-dl-vid').addEventListener('click', (e) => {
        e.preventDefault();
        startMediaDownload(downloadVid, `${item.title || `video_${idx+1}`}.mp4`);
      });
      card.querySelector('.btn-batch-dl-aud').addEventListener('click', (e) => {
        e.preventDefault();
        startMediaDownload(downloadAud, `${item.title || `audio_${idx+1}`}.mp3`);
      });

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
        publicUrlInput.value = 'https://omniextract-9h5t.onrender.com';
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

  function showAlert(msg, type = 'error') {
    alertBanner.className = `alert-banner ${type}`;
    let html = escapeHtml(msg).replace(/\n/g, '<br>');
    alertBanner.innerHTML = html;
    alertBanner.classList.remove('hidden');
    alertBanner.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
