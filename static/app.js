/**
 * OmniExtract Facebook — Frontend Client Controller
 * Version 1.1.0 with Single & Batch Extraction
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

  // Single Header and Profile Elements
  const authorAvatar = document.getElementById('author-avatar');
  const avatarFallback = document.getElementById('author-avatar-fallback');
  const authorName = document.getElementById('author-name');
  const postTitle = document.getElementById('post-title');
  const badgeType = document.getElementById('badge-type');
  const badgeImages = document.getElementById('badge-images-count');
  const badgeVideos = document.getElementById('badge-videos-count');
  const btnOpenOriginal = document.getElementById('btn-open-original');
  const btnDownloadZip = document.getElementById('btn-download-all-zip');

  // Tabs Elements
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const tabImgCounter = document.getElementById('tab-img-counter');
  const tabVidCounter = document.getElementById('tab-vid-counter');

  // Content Panes
  const postTextContent = document.getElementById('post-text-content');
  const statWords = document.getElementById('stat-words');
  const statChars = document.getElementById('stat-chars');
  const btnCopyText = document.getElementById('btn-copy-text');
  const btnDownloadTxt = document.getElementById('btn-download-txt');

  const imagesGrid = document.getElementById('images-grid');
  const imagesEmpty = document.getElementById('images-empty');

  const videosContainer = document.getElementById('videos-container');
  const videosEmpty = document.getElementById('videos-empty');

  const rawJsonViewer = document.getElementById('raw-json-viewer');
  const btnCopyJson = document.getElementById('btn-copy-json');

  // Batch Results Elements
  const batchSummarySubtitle = document.getElementById('batch-summary-subtitle');
  const badgeBatchCount = document.getElementById('badge-batch-count');
  const badgeBatchTotalWords = document.getElementById('badge-batch-total-words');
  const batchChaptersList = document.getElementById('batch-chapters-list');
  const btnDownloadCompiledNovel = document.getElementById('btn-download-compiled-novel');
  const btnDownloadBatchZip = document.getElementById('btn-download-batch-zip');

  // History Elements
  const btnShowHistory = document.getElementById('btn-show-history');
  const historyModal = document.getElementById('history-modal');
  const btnCloseHistory = document.getElementById('btn-close-history');
  const historyList = document.getElementById('history-list');
  const btnClearHistory = document.getElementById('btn-clear-history');
  const historyCount = document.getElementById('history-count');

  // API Docs Elements
  const btnShowApi = document.getElementById('btn-show-api-docs');
  const apiModal = document.getElementById('api-modal');
  const btnCloseApi = document.getElementById('btn-close-api');

  // Lightbox Elements
  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxImg = document.getElementById('lightbox-img');
  const btnCloseLightbox = document.getElementById('btn-close-lightbox');
  const lightboxDownload = document.getElementById('lightbox-download');
  const lightboxOpen = document.getElementById('lightbox-open');

  // State
  let currentExtractionData = null;
  let currentBatchData = null;

  // Initialize
  updateHistoryCounter();

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

  // Detect Facebook URLs helper
  function extractUrlsFromText(text) {
    if (!text) return [];
    const spaced = text.replace(/(\d+\.)?(https?:\/\/)/g, ' $2');
    const matches = spaced.match(/https?:\/\/(?:[a-zA-Z0-9_\-\.]+\.)?facebook\.com\/[^\s\)\]"]+/g) || [];
    return [...new Set(matches.map(u => u.replace(/[\)\]",']+$/, '').trim()))];
  }

  // Single Input event listeners
  inputUrl.addEventListener('input', () => {
    const val = inputUrl.value.trim();
    if (val.length > 0) {
      btnClear.classList.remove('hidden');
      // If user pasted multiple links into single input, automatically suggest/switch to batch mode!
      const urls = extractUrlsFromText(val);
      if (urls.length > 1) {
        batchUrlsInput.value = val;
        updateBatchCount();
        setMode('batch');
        showToast(`Detected ${urls.length} Facebook links! Switched to Batch Mode.`, 'info');
      }
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
          showToast(`Pasted ${urls.length} links into Batch Mode!`);
        } else {
          inputUrl.value = text.trim();
          btnClear.classList.remove('hidden');
          showToast('Link pasted from clipboard');
          inputUrl.focus();
        }
      }
    } catch (err) {
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
        showToast('Text pasted into batch queue');
      }
    } catch {
      showToast('Could not access clipboard. Please paste manually.', 'warning');
    }
  });

  btnBatchClear.addEventListener('click', () => {
    batchUrlsInput.value = '';
    updateBatchCount();
  });

  // Sample buttons
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
  batchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = batchUrlsInput.value.trim();
    const urls = extractUrlsFromText(text);
    if (urls.length === 0) {
      showAlert('No valid Facebook links detected. Please paste Facebook URLs.', 'error');
      return;
    }
    performBatchExtraction(text, urls);
  });

  // Extraction logic (Single)
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
        throw new Error(data.error || 'Failed to extract content from this Facebook URL.');
      }

      currentExtractionData = data;
      renderResults(data);
      saveToHistory(data);
      updateHistoryCounter();
      showToast('Extracted successfully!');

      setTimeout(() => {
        resultsZone.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      const errMsg = err.message || 'An error occurred during extraction. Make sure the Facebook link is public.';
      if (errMsg.toLowerCase().includes('locked') || errMsg.toLowerCase().includes('login wall') || errMsg.toLowerCase().includes('restrict')) {
        showAlert(
          `🔒 <strong>Restricted / Locked Facebook Content:</strong> Make sure you pasted a valid profile link, ID link (e.g. <code>profile.php?id=...</code>), or numeric UID.`,
          'warning'
        );
      } else {
        showAlert(errMsg, 'error');
      }
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    if (isLoading) {
      btnSubmit.disabled = true;
      spinner.classList.remove('hidden');
      btnText.textContent = 'Extracting...';
      btnArrow.classList.add('hidden');
    } else {
      btnSubmit.disabled = false;
      spinner.classList.add('hidden');
      btnText.textContent = 'Extract Everything';
      btnArrow.classList.remove('hidden');
    }
  }

  // Batch Extraction Logic
  async function performBatchExtraction(rawText, urls) {
    setBatchLoading(true);
    hideAlert();
    batchResultsZone.classList.add('hidden');
    resultsZone.classList.add('hidden');

    try {
      showToast(`Extracting ${urls.length} chapters... Please wait.`, 'info');

      const response = await fetch('/api/extract-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: rawText, urls })
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Batch extraction encountered an error.');
      }

      currentBatchData = data;
      renderBatchResults(data);
      showToast(`Batch extraction complete! ${data.results.length} chapters processed.`);

      setTimeout(() => {
        batchResultsZone.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      showAlert(err.message || 'Batch extraction failed.', 'error');
    } finally {
      setBatchLoading(false);
    }
  }

  function setBatchLoading(isLoading) {
    if (isLoading) {
      btnBatchSubmit.disabled = true;
      batchSpinner.classList.remove('hidden');
      btnBatchText.textContent = 'Extracting All Links...';
    } else {
      btnBatchSubmit.disabled = false;
      batchSpinner.classList.add('hidden');
      btnBatchText.textContent = 'Extract All Links';
    }
  }

  function showAlert(msg, type = 'error') {
    alertBanner.className = `alert-banner ${type}`;
    if (typeof msg === 'string' && (msg.includes('<') || msg.includes('&'))) {
      alertBanner.innerHTML = msg;
    } else {
      alertBanner.textContent = msg;
    }
    alertBanner.classList.remove('hidden');
  }

  function hideAlert() {
    alertBanner.classList.add('hidden');
  }

  function renderResults(data) {
    resultsZone.classList.remove('hidden');

    const author = data.author || {};
    authorName.textContent = author.name || 'Facebook Post';
    postTitle.textContent = data.title || data.url;
    btnOpenOriginal.href = data.url;

    if (author.avatar) {
      authorAvatar.src = author.avatar;
      authorAvatar.classList.remove('hidden');
      avatarFallback.classList.add('hidden');
    } else {
      authorAvatar.classList.add('hidden');
      avatarFallback.classList.remove('hidden');
      avatarFallback.textContent = (author.name || 'FB').charAt(0).toUpperCase();
    }

    if (data.type === 'locked_profile' || data.is_locked_profile) {
      badgeType.textContent = '🔒 LOCKED PROFILE';
    } else if (data.type === 'profile') {
      badgeType.textContent = 'PROFILE';
    } else {
      badgeType.textContent = (data.type || 'Post').toUpperCase();
    }

    const totalImages = (data.images || []).length;
    const totalVideos = (data.videos || []).length;

    badgeImages.textContent = `${totalImages} ${totalImages === 1 ? 'Image' : 'Images'}`;
    badgeVideos.textContent = `${totalVideos} ${totalVideos === 1 ? 'Video' : 'Videos'}`;
    tabImgCounter.textContent = totalImages;
    tabVidCounter.textContent = totalVideos;

    // Facebook numeric UID badge with one-click copy
    const badgeUid = document.getElementById('badge-uid');
    const uidValue = document.getElementById('uid-value');
    const uid = data.uid || (data.author && data.author.uid);
    if (badgeUid && uidValue) {
      if (uid) {
        uidValue.textContent = uid;
        badgeUid.classList.remove('hidden');
        badgeUid.onclick = async () => {
          try {
            await navigator.clipboard.writeText(uid);
            showToast(`Facebook UID: ${uid} copied to clipboard!`);
          } catch {
            showToast(`UID: ${uid}`);
          }
        };
      } else {
        badgeUid.classList.add('hidden');
      }
    }

    // Direct Permanent Facebook ID Link Badge (e.g. facebook.com/profile.php?id=...)
    const badgeIdLink = document.getElementById('badge-id-link');
    const idLinkValue = document.getElementById('id-link-value');
    const idLink = data.id_link || (uid ? `https://www.facebook.com/profile.php?id=${uid}` : null);
    if (badgeIdLink && idLinkValue) {
      if (idLink) {
        idLinkValue.textContent = uid ? `id=${uid}` : 'Profile Link';
        badgeIdLink.href = idLink;
        badgeIdLink.classList.remove('hidden');
        badgeIdLink.onclick = async (e) => {
          e.preventDefault();
          try {
            await navigator.clipboard.writeText(idLink);
            showToast(`Permanent ID Link copied: ${idLink}`);
          } catch {
            showToast(`ID Link: ${idLink}`);
          }
        };
      } else {
        badgeIdLink.classList.add('hidden');
      }
    }

    // Locked post / locked profile unlock status badge
    const badgeLock = document.getElementById('badge-lock-status');
    if (badgeLock) {
      if (data.is_locked_profile || data.type === 'locked_profile') {
        badgeLock.classList.remove('hidden');
        badgeLock.textContent = '🔓 Locked Profile Assets Unlocked';
      } else if (data.lock_bypass_used || data.is_locked) {
        badgeLock.classList.remove('hidden');
        const stratMap = {
          'authenticated_session': '🔓 Unlocked (Auth Session)',
          'authenticated_friend_session': '🔓 Unlocked (Friend Session)',
          'profile_lock_bypass': '🔓 Profile Lock Unlocked',
          'mbasic': '🔓 Unlocked (mbasic Engine)',
          'archive_cache': '🔓 Unlocked (Archive)',
          'mobile_ua': '🔓 Unlocked (Mobile Engine)'
        };
        badgeLock.textContent = stratMap[data.lock_bypass_used] || '🔓 Locked Content Unlocked';
      } else {
        badgeLock.classList.add('hidden');
      }
    }

    renderTextTab(data.text || '');
    renderImagesTab(data.images || []);
    renderVideosTab(data.videos || []);
    rawJsonViewer.textContent = JSON.stringify(data, null, 2);

    if (data.type === 'profile' || data.type === 'locked_profile') {
      switchTab('tab-images');
    } else if (totalVideos > 0 && totalImages === 0 && !data.text) {
      switchTab('tab-videos');
    } else if (totalImages > 0 && !data.text) {
      switchTab('tab-images');
    } else {
      switchTab('tab-text');
    }
  }

  function renderTextTab(text) {
    if (!text || text.trim() === '') {
      postTextContent.innerHTML = '<span style="color: var(--text-muted); font-style: italic;">No caption or textual post content detected for this URL.</span>';
      statWords.textContent = '0 words';
      statChars.textContent = '0 characters';
      return;
    }

    const words = text.trim().split(/\s+/).filter(Boolean).length;
    const chars = text.length;

    statWords.textContent = `${words} ${words === 1 ? 'word' : 'words'}`;
    statChars.textContent = `${chars} characters`;

    const escaped = escapeHtml(text);
    const linkified = escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    postTextContent.innerHTML = linkified;
  }

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

      const directUrl = img.url;
      const proxyUrl = img.proxy_url || `/api/proxy?url=${encodeURIComponent(directUrl)}`;
      const downloadUrl = img.download_url || `/api/download?url=${encodeURIComponent(directUrl)}&filename=fb_photo_${idx+1}.jpg`;

      card.innerHTML = `
        <div class="card-img-wrap" data-img="${directUrl}" data-proxy="${proxyUrl}">
          <img src="${directUrl}" alt="Facebook Photo ${idx+1}" referrerpolicy="no-referrer" loading="lazy" onerror="this.onerror=null; this.src='${proxyUrl}';">
          <div class="img-overlay-zoom">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="11" y1="8" x2="11" y2="14"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </div>
        </div>
        <div class="card-info-bar">
          <span class="card-img-label">${img.label || `Photo #${idx+1}`}</span>
          <div class="card-action-btns">
            <button type="button" class="btn-card-action btn-copy-link" data-url="${directUrl}" title="Copy Image CDN URL">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
              </svg>
            </button>
            <a href="${downloadUrl}" class="btn-card-action" title="Download Image">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </a>
          </div>
        </div>
      `;

      const wrap = card.querySelector('.card-img-wrap');
      wrap.addEventListener('click', () => openLightbox(directUrl, downloadUrl));

      const copyBtn = card.querySelector('.btn-copy-link');
      copyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(directUrl);
        showToast('Image URL copied to clipboard');
      });

      imagesGrid.appendChild(card);
    });
  }

  function renderVideosTab(videos) {
    videosContainer.innerHTML = '';
    if (!videos || videos.length === 0) {
      videosEmpty.classList.remove('hidden');
      return;
    }
    videosEmpty.classList.add('hidden');

    videos.forEach((vid, idx) => {
      const card = document.createElement('div');
      card.className = 'video-card';

      const downloadUrl = vid.download_url || `/api/download?url=${encodeURIComponent(vid.url)}&filename=fb_video_${idx+1}.mp4`;
      const quality = vid.quality || 'Standard Quality';
      const durationStr = vid.duration ? `${Math.floor(vid.duration / 60)}m ${Math.floor(vid.duration % 60)}s` : 'Unknown';

      card.innerHTML = `
        <div class="video-player-box">
          <video controls preload="metadata" playsinline>
            <source src="${vid.url}" type="video/mp4">
            Your browser does not support HTML5 video streaming.
          </video>
        </div>
        <div class="video-details-box">
          <div>
            <span class="video-quality-tag">${quality}</span>
            <ul class="video-meta-list">
              <li><strong>Stream Format:</strong> ${vid.format || 'mp4'}</li>
              <li><strong>Duration:</strong> ${durationStr}</li>
              <li><strong>Source:</strong> ${vid.source || 'Facebook Stream'}</li>
            </ul>
          </div>
          <div class="video-actions-group">
            <a href="${downloadUrl}" class="btn-primary-sm" style="display:inline-flex; align-items:center; gap:8px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <span>Download MP4</span>
            </a>
            <button type="button" class="btn-secondary-sm btn-copy-vid-url" data-url="${vid.url}">
              Copy Stream URL
            </button>
          </div>
        </div>
      `;

      const copyVidBtn = card.querySelector('.btn-copy-vid-url');
      copyVidBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(vid.url);
        showToast('Video stream link copied to clipboard');
      });

      videosContainer.appendChild(card);
    });
  }

  // Render Batch Results
  function renderBatchResults(batchData) {
    batchResultsZone.classList.remove('hidden');

    const results = batchData.results || [];
    let totalWords = 0;
    results.forEach(r => {
      if (r.text) {
        totalWords += r.text.trim().split(/\s+/).filter(Boolean).length;
      }
    });

    badgeBatchCount.textContent = `${results.length} Chapters Extracted`;
    badgeBatchTotalWords.textContent = `${totalWords.toLocaleString()} Words Total`;
    batchSummarySubtitle.textContent = `Compiled text ready for reading or full export`;

    batchChaptersList.innerHTML = '';

    results.forEach((ch, idx) => {
      const card = document.createElement('div');
      card.className = 'batch-chapter-card';

      const chText = ch.text || '[No text extracted]';
      const wordsCount = chText.trim().split(/\s+/).filter(Boolean).length;
      const title = ch.title || `Chapter / Part ${ch.index || (idx + 1)}`;

      card.innerHTML = `
        <div class="chapter-header" data-id="${idx}">
          <div class="chapter-title-group">
            <span class="chapter-number-pill">Part ${ch.index || (idx + 1)}</span>
            <span class="chapter-title">${escapeHtml(title)}</span>
          </div>
          <div class="chapter-meta-right">
            <span class="chapter-word-count">${wordsCount.toLocaleString()} words</span>
            <svg class="chevron-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </div>
        <div class="chapter-body" id="chapter-body-${idx}">
          <div class="chapter-actions-top">
            <button type="button" class="btn-card-action btn-copy-chapter" data-id="${idx}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy Chapter</span>
            </button>
            <a href="${ch.url}" target="_blank" rel="noopener noreferrer" class="btn-card-action">
              <span>Facebook Link</span>
            </a>
          </div>
          <div class="chapter-text-content">${escapeHtml(chText)}</div>
        </div>
      `;

      // Accordion toggle
      const header = card.querySelector('.chapter-header');
      const body = card.querySelector('.chapter-body');
      header.addEventListener('click', () => {
        body.classList.toggle('open');
      });

      // Copy chapter
      const copyBtn = card.querySelector('.btn-copy-chapter');
      copyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(chText);
        showToast(`Chapter ${ch.index || (idx + 1)} copied to clipboard!`);
      });

      batchChaptersList.appendChild(card);
    });
  }

  // Batch Downloads
  btnDownloadCompiledNovel.addEventListener('click', async () => {
    if (!currentBatchData || !currentBatchData.results) return;
    showToast('Compiling novel document...');

    try {
      const resp = await fetch('/api/download-compiled-txt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: "Facebook_Compiled_Novel",
          chapters: currentBatchData.results
        })
      });

      if (!resp.ok) throw new Error('Download failed');
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Compiled_Novel_${Date.now()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Downloaded Compiled Novel (.TXT)!');
    } catch {
      showToast('Failed to compile novel document.', 'error');
    }
  });

  btnDownloadBatchZip.addEventListener('click', async () => {
    if (!currentBatchData || !currentBatchData.results) return;
    showToast('Preparing batch ZIP package with all chapters...');

    try {
      // Gather all images from all chapters
      let allImages = [];
      currentBatchData.results.forEach(r => {
        if (r.images) {
          allImages.push(...r.images.map(img => img.url));
        }
      });

      const payload = {
        title: "Facebook_Full_Series",
        text: currentBatchData.compiled_text || "",
        url: currentBatchData.results[0]?.url || "https://facebook.com",
        images: allImages.slice(0, 50),
        videos: []
      };

      const resp = await fetch('/api/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) throw new Error('ZIP bundling failed');
      const blob = await resp.blob();
      const zipUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = zipUrl;
      a.download = `fb_series_bundle_${Date.now()}.zip`;
      a.click();
      URL.revokeObjectURL(zipUrl);
      showToast('ZIP archive downloaded successfully!');
    } catch {
      showToast('Failed to package ZIP bundle.', 'error');
    }
  });

  // Tab switching
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      switchTab(targetId);
    });
  });

  function switchTab(targetId) {
    tabBtns.forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === targetId));
    tabPanes.forEach(p => p.classList.toggle('active', p.id === targetId));
  }

  // Copy buttons
  btnCopyText.addEventListener('click', () => {
    if (!currentExtractionData || !currentExtractionData.text) {
      showToast('No text available to copy', 'warning');
      return;
    }
    navigator.clipboard.writeText(currentExtractionData.text);
    showToast('Post text copied to clipboard!');
  });

  btnDownloadTxt.addEventListener('click', () => {
    if (!currentExtractionData || !currentExtractionData.text) {
      showToast('No text available to download', 'warning');
      return;
    }
    const blob = new Blob([currentExtractionData.text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `facebook_post_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Saved post_text.txt');
  });

  btnCopyJson.addEventListener('click', () => {
    if (!currentExtractionData) return;
    navigator.clipboard.writeText(JSON.stringify(currentExtractionData, null, 2));
    showToast('JSON metadata copied to clipboard!');
  });

  // Download all as ZIP
  btnDownloadZip.addEventListener('click', async () => {
    if (!currentExtractionData) return;
    showToast('Preparing ZIP package, please wait...');

    try {
      const payload = {
        title: currentExtractionData.title || 'facebook_extracted',
        text: currentExtractionData.text || '',
        author: (currentExtractionData.author && currentExtractionData.author.name) || '',
        url: currentExtractionData.url,
        images: (currentExtractionData.images || []).map(img => img.url),
        videos: (currentExtractionData.videos || []).map(v => v.url)
      };

      const resp = await fetch('/api/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) throw new Error('ZIP bundling failed');

      const blob = await resp.blob();
      const zipUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = zipUrl;
      a.download = `fb_extracted_${Date.now()}.zip`;
      a.click();
      URL.revokeObjectURL(zipUrl);
      showToast('ZIP bundle downloaded successfully!');
    } catch {
      showToast('Failed to download ZIP archive.', 'error');
    }
  });

  // Lightbox
  function openLightbox(imgUrl, downloadUrl) {
    lightboxImg.src = imgUrl;
    lightboxDownload.href = downloadUrl;
    lightboxOpen.href = imgUrl;
    lightboxModal.classList.remove('hidden');
  }

  function closeLightbox() {
    lightboxModal.classList.add('hidden');
    lightboxImg.src = '';
  }

  btnCloseLightbox.addEventListener('click', closeLightbox);
  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) closeLightbox();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeLightbox();
      historyModal.classList.add('hidden');
      apiModal.classList.add('hidden');
    }
  });

  // History Drawer
  btnShowHistory.addEventListener('click', () => {
    renderHistoryModal();
    historyModal.classList.remove('hidden');
  });

  btnCloseHistory.addEventListener('click', () => {
    historyModal.classList.add('hidden');
  });

  historyModal.addEventListener('click', (e) => {
    if (e.target === historyModal) historyModal.classList.add('hidden');
  });

  btnClearHistory.addEventListener('click', () => {
    localStorage.removeItem('fb_extract_history');
    renderHistoryModal();
    updateHistoryCounter();
    showToast('Extraction history cleared');
  });

  function getHistory() {
    try {
      return JSON.parse(localStorage.getItem('fb_extract_history') || '[]');
    } catch {
      return [];
    }
  }

  function saveToHistory(data) {
    const list = getHistory();
    const item = {
      id: Date.now(),
      url: data.url,
      title: data.title || (data.author && data.author.name) || 'Facebook Post',
      author: (data.author && data.author.name) || '',
      type: data.type || 'post',
      imagesCount: (data.images || []).length,
      videosCount: (data.videos || []).length,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const filtered = list.filter(x => x.url !== data.url);
    filtered.unshift(item);
    if (filtered.length > 25) filtered.pop();

    localStorage.setItem('fb_extract_history', JSON.stringify(filtered));
  }

  function updateHistoryCounter() {
    const list = getHistory();
    historyCount.textContent = list.length;
  }

  function renderHistoryModal() {
    const list = getHistory();
    historyList.innerHTML = '';

    if (list.length === 0) {
      historyList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 30px;">No extractions yet.</div>';
      return;
    }

    list.forEach(item => {
      const el = document.createElement('div');
      el.className = 'history-item';
      el.innerHTML = `
        <div class="history-item-info">
          <div class="history-item-title">${escapeHtml(item.title)}</div>
          <div class="history-item-url">${escapeHtml(item.url)}</div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${item.timestamp}</div>
      `;

      el.addEventListener('click', () => {
        historyModal.classList.add('hidden');
        inputUrl.value = item.url;
        btnClear.classList.remove('hidden');
        setMode('single');
        performExtraction(item.url);
      });

      historyList.appendChild(el);
    });
  }

  // API Docs Modal
  btnShowApi.addEventListener('click', () => {
    apiModal.classList.remove('hidden');
  });

  btnCloseApi.addEventListener('click', () => {
    apiModal.classList.add('hidden');
  });

  apiModal.addEventListener('click', (e) => {
    if (e.target === apiModal) apiModal.classList.add('hidden');
  });

  // Public / Share Modal Elements & Logic
  const btnShowShare = document.getElementById('btn-show-share');
  const shareModal = document.getElementById('share-modal');
  const btnCloseShare = document.getElementById('btn-close-share');
  const publicUrlInput = document.getElementById('public-url-input');
  const btnCopyPublicUrl = document.getElementById('btn-copy-public-url');
  const lanUrlInput = document.getElementById('lan-url-input');
  const btnCopyLanUrl = document.getElementById('btn-copy-lan-url');
  const shareLivePill = document.getElementById('share-live-pill');
  const modalLiveStatusPill = document.getElementById('modal-live-status-pill');

  async function loadNetworkInfo() {
    try {
      const resp = await fetch('/api/network-info');
      if (resp.ok) {
        const net = await resp.json();
        if (net.public_url) {
          publicUrlInput.value = net.public_url;
          if (shareLivePill) shareLivePill.textContent = 'LIVE';
          if (modalLiveStatusPill) modalLiveStatusPill.textContent = 'Global Online';
        } else {
          publicUrlInput.value = `${window.location.origin} (Run with --public for ngrok)`;
          if (shareLivePill) shareLivePill.textContent = 'LAN';
          if (modalLiveStatusPill) modalLiveStatusPill.textContent = 'LAN Online';
        }

        if (net.lan_url) {
          lanUrlInput.value = net.lan_url;
        } else {
          lanUrlInput.value = `${window.location.protocol}//${window.location.hostname}:8000`;
        }
      }
    } catch {
      // Fallback to current browser location
      if (publicUrlInput) publicUrlInput.value = window.location.href;
      if (lanUrlInput) lanUrlInput.value = `${window.location.protocol}//${window.location.hostname}:8000`;
    }
  }

  if (btnShowShare && shareModal) {
    btnShowShare.addEventListener('click', () => {
      loadNetworkInfo();
      shareModal.classList.remove('hidden');
    });

    if (btnCloseShare) {
      btnCloseShare.addEventListener('click', () => {
        shareModal.classList.add('hidden');
      });
    }

    shareModal.addEventListener('click', (e) => {
      if (e.target === shareModal) shareModal.classList.add('hidden');
    });
  }

  if (btnCopyPublicUrl && publicUrlInput) {
    btnCopyPublicUrl.addEventListener('click', () => {
      const url = publicUrlInput.value;
      if (url) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('Public HTTPS link copied to clipboard!');
        }).catch(() => {
          publicUrlInput.select();
          document.execCommand('copy');
          showToast('Public link copied!');
        });
      }
    });
  }

  if (btnCopyLanUrl && lanUrlInput) {
    btnCopyLanUrl.addEventListener('click', () => {
      const url = lanUrlInput.value;
      if (url) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('Local LAN Wi-Fi link copied!');
        }).catch(() => {
          lanUrlInput.select();
          document.execCommand('copy');
          showToast('LAN link copied!');
        });
      }
    });
  }

  // Load network info on initial boot
  loadNetworkInfo();

  // Toast Notification
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: ${type === 'warning' ? '#f59e0b' : '#38bdf8'};">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
});
