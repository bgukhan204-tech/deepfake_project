// ─────────────────────────────────────────────────────────
//  DeepShield — Dual-Modal Analysis Script
//  Handles: Image tab (ELA + Model) & Video tab (frame-by-frame)
// ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

    // ── Tab state ──────────────────────────────────────────
    function switchTab(tab) {
        const isImage = tab === 'image';
        document.getElementById('tab-image').classList.toggle('active', isImage);
        document.getElementById('tab-video').classList.toggle('active', !isImage);
        document.getElementById('panel-image').classList.toggle('hidden', !isImage);
        document.getElementById('panel-video').classList.toggle('hidden', isImage);
    }
    window.switchTab = switchTab;

    // ── IMAGE TAB ──────────────────────────────────────────
    const uploadZone   = document.getElementById('upload-zone');
    const fileInput    = document.getElementById('file-input');
    const uploadIdle   = document.getElementById('upload-idle');
    const uploadPreview= document.getElementById('upload-preview');
    const imagePreview = document.getElementById('image-preview');
    const removeBtn    = document.getElementById('remove-btn');
    const analyzeBtn   = document.getElementById('analyze-btn');
    const btnDefault   = document.getElementById('btn-default');
    const btnLoading   = document.getElementById('btn-loading');
    const errorAlert   = document.getElementById('error-alert');
    const errorText    = document.getElementById('error-text');
    const resultsPanel = document.getElementById('results-panel');
    const cybercrimeBlock = document.getElementById('cybercrime-block');

    // Image result elements
    const confidenceValue  = document.getElementById('confidence-value');
    const verdictBanner    = document.getElementById('verdict-banner');
    const verdictIcon      = document.getElementById('verdict-status-icon');
    const verdictTitle     = document.getElementById('verdict-title');
    const verdictMono      = document.getElementById('verdict-mono-text');
    const authenticValue   = document.getElementById('authentic-value');
    const manipulatedValue = document.getElementById('manipulated-value');
    const fillAuthentic    = document.getElementById('fill-authentic');
    const fillManipulated  = document.getElementById('fill-manipulated');
    // Breakdown
    const modelBadge     = document.getElementById('model-badge');
    const modelFakePct   = document.getElementById('model-fake-pct');
    const fillModelFake  = document.getElementById('fill-model-fake');
    const elaBadge       = document.getElementById('ela-badge');
    const elaPct         = document.getElementById('ela-pct');
    const fillEla        = document.getElementById('fill-ela');

    let currentFile = null;

    // Drag and drop events
    ['dragenter','dragover','dragleave','drop'].forEach(e => {
        uploadZone.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); });
    });
    uploadZone.addEventListener('dragenter', () => uploadZone.classList.add('dragover'));
    uploadZone.addEventListener('dragover',  () => uploadZone.classList.add('dragover'));
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
    uploadZone.addEventListener('drop', e => {
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer?.files?.length) loadImageFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', e => {
        if (e.target.files.length) loadImageFile(e.target.files[0]);
    });
    removeBtn.addEventListener('click', resetImageUI);
    analyzeBtn.addEventListener('click', analyzeImage);

    function loadImageFile(file) {
        if (!file.type.startsWith('image/')) {
            showImageError('Please upload a valid image (PNG, JPG, WEBP).');
            return;
        }
        currentFile = file;
        hideImageError();
        hideImageResults();

        const reader = new FileReader();
        reader.onload = e => {
            imagePreview.src = e.target.result;
            uploadIdle.classList.add('hidden');
            uploadPreview.classList.remove('hidden');
            uploadZone.classList.add('has-image');
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function resetImageUI() {
        currentFile = null;
        fileInput.value = '';
        imagePreview.src = '';
        uploadPreview.classList.add('hidden');
        uploadIdle.classList.remove('hidden');
        uploadZone.classList.remove('has-image');
        analyzeBtn.disabled = true;
        hideImageError();
        hideImageResults();
        [fillAuthentic, fillManipulated, fillModelFake, fillEla].forEach(el => el.style.width = '0%');
    }

    function showImageError(msg) { errorText.textContent = msg; errorAlert.classList.remove('hidden'); }
    function hideImageError()    { errorAlert.classList.add('hidden'); }
    function hideImageResults()  { resultsPanel.classList.add('hidden'); cybercrimeBlock.classList.add('hidden'); }

    async function analyzeImage() {
        if (!currentFile) return;

        btnDefault.classList.add('hidden');
        btnLoading.classList.remove('hidden');
        analyzeBtn.disabled = true;
        hideImageError();
        hideImageResults();
        [fillAuthentic, fillManipulated, fillModelFake, fillEla].forEach(el => el.style.width = '0%');

        const form = new FormData();
        form.append('file', currentFile);

        try {
            const res  = await fetch('/predict', { method:'POST', body:form });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            displayImageResults(data);
        } catch (err) {
            showImageError(err.message || 'Analysis failed. Please try again.');
        } finally {
            btnDefault.classList.remove('hidden');
            btnLoading.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    }

    function displayImageResults(data) {
        resultsPanel.classList.remove('hidden');
        const isReal = data.status === 'REAL';

        confidenceValue.textContent = data.confidence;

        verdictBanner.className = 'verdict-banner ' + (isReal ? 'real' : 'fake');
        verdictIcon.textContent = isReal ? '✅' : '⚠️';
        verdictTitle.textContent  = isReal ? 'Authentic Image' : 'Manipulated / AI-Generated';
        verdictTitle.style.color  = isReal ? '#22c55e' : '#ef4444';
        verdictMono.textContent   = isReal ? 'STATUS::GENUINE' : 'STATUS::SUSPICIOUS';
        
        // Display Reason
        const reasonEl = document.getElementById('verdict-reason');
        if (reasonEl) reasonEl.textContent = data.reason || (isReal ? "Authentic content." : "Manipulated content.");

        authenticValue.textContent   = data.authentic_score + '%';
        manipulatedValue.textContent = data.manipulated_score + '%';

        // Breakdown — model
        if (data.model_available && data.model_fake_score !== null) {
            modelBadge.textContent = data.model_fake_score + '% fake';
            modelFakePct.textContent = data.model_fake_score + '%';
        } else {
            modelBadge.textContent = 'N/A';
            modelFakePct.textContent = 'N/A';
        }
        // Breakdown — ELA
        elaBadge.textContent = data.ela_score + '%';
        elaPct.textContent = data.ela_score + '%';

        // Animate bars
        requestAnimationFrame(() => setTimeout(() => {
            fillAuthentic.style.width   = data.authentic_score + '%';
            fillManipulated.style.width = data.manipulated_score + '%';
            if (data.model_fake_score !== null) fillModelFake.style.width = data.model_fake_score + '%';
            fillEla.style.width = data.ela_score + '%';
        }, 50));

        // Cybercrime
        cybercrimeBlock.classList.toggle('hidden', isReal);
    }

    // ── VIDEO TAB ──────────────────────────────────────────
    const videoZone        = document.getElementById('video-zone');
    const videoInput       = document.getElementById('video-input');
    const videoIdle        = document.getElementById('video-idle');
    const videoSelected    = document.getElementById('video-selected');
    const videoFileName    = document.getElementById('video-file-name');
    const videoFileSize    = document.getElementById('video-file-size');
    const videoRemoveBtn   = document.getElementById('video-remove-btn');
    const analyzeVideoBtn  = document.getElementById('analyze-video-btn');
    const videoBtnDefault  = document.getElementById('video-btn-default');
    const videoBtnLoading  = document.getElementById('video-btn-loading');
    const videoErrorAlert  = document.getElementById('video-error-alert');
    const videoErrorText   = document.getElementById('video-error-text');
    const videoResultsPanel= document.getElementById('video-results-panel');
    const videoCyberBlock  = document.getElementById('video-cybercrime-block');

    // Video result elements
    const videoConfidence   = document.getElementById('video-confidence-value');
    const videoVerdictBanner= document.getElementById('video-verdict-banner');
    const videoVerdictIcon  = document.getElementById('video-verdict-icon');
    const videoVerdictTitle = document.getElementById('video-verdict-title');
    const videoVerdictMono  = document.getElementById('video-verdict-mono');
    const videoAuthValue    = document.getElementById('video-authentic-value');
    const videoManipValue   = document.getElementById('video-manipulated-value');
    const videoFillAuth     = document.getElementById('video-fill-authentic');
    const videoFillManip    = document.getElementById('video-fill-manipulated');
    const videoDuration     = document.getElementById('video-duration');
    const videoTotalFrames  = document.getElementById('video-total-frames');
    const videoFramesAnalyz = document.getElementById('video-frames-analyzed');
    const videoElaScore     = document.getElementById('video-ela-score');
    const frameTimeline     = document.getElementById('frame-timeline');

    let currentVideo = null;

    // Drag and drop for video zone
    ['dragenter','dragover','dragleave','drop'].forEach(e => {
        videoZone.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); });
    });
    videoZone.addEventListener('dragenter', () => videoZone.classList.add('dragover'));
    videoZone.addEventListener('dragover',  () => videoZone.classList.add('dragover'));
    videoZone.addEventListener('dragleave', () => videoZone.classList.remove('dragover'));
    videoZone.addEventListener('drop', e => {
        videoZone.classList.remove('dragover');
        if (e.dataTransfer?.files?.length) loadVideoFile(e.dataTransfer.files[0]);
    });

    videoInput.addEventListener('change', e => {
        if (e.target.files.length) loadVideoFile(e.target.files[0]);
    });
    videoRemoveBtn.addEventListener('click', resetVideoUI);
    analyzeVideoBtn.addEventListener('click', analyzeVideo);

    function loadVideoFile(file) {
        const allowed = ['video/mp4','video/avi','video/quicktime','video/x-matroska','video/webm','video/x-msvideo'];
        if (!allowed.some(t => file.type === t) && !file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
            showVideoError('Unsupported format. Please upload MP4, AVI, MOV, MKV or WEBM.');
            return;
        }
        currentVideo = file;
        videoFileName.textContent = file.name;
        videoFileSize.textContent = (file.size / (1024 * 1024)).toFixed(1) + ' MB';
        videoIdle.classList.add('hidden');
        videoSelected.classList.remove('hidden');
        analyzeVideoBtn.disabled = false;
        hideVideoError();
        hideVideoResults();
    }

    function resetVideoUI() {
        currentVideo = null;
        videoInput.value = '';
        videoSelected.classList.add('hidden');
        videoIdle.classList.remove('hidden');
        analyzeVideoBtn.disabled = true;
        hideVideoError();
        hideVideoResults();
    }

    function showVideoError(msg) { videoErrorText.textContent = msg; videoErrorAlert.classList.remove('hidden'); }
    function hideVideoError()    { videoErrorAlert.classList.add('hidden'); }
    function hideVideoResults()  { videoResultsPanel.classList.add('hidden'); videoCyberBlock.classList.add('hidden'); }

    async function analyzeVideo() {
        if (!currentVideo) return;

        videoBtnDefault.classList.add('hidden');
        videoBtnLoading.classList.remove('hidden');
        analyzeVideoBtn.disabled = true;
        hideVideoError();
        hideVideoResults();

        const form = new FormData();
        form.append('file', currentVideo);

        try {
            const res  = await fetch('/predict_video', { method:'POST', body:form });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            displayVideoResults(data);
        } catch (err) {
            showVideoError(err.message || 'Video analysis failed. Please try again.');
        } finally {
            videoBtnDefault.classList.remove('hidden');
            videoBtnLoading.classList.add('hidden');
            analyzeVideoBtn.disabled = false;
        }
    }

    function displayVideoResults(data) {
        videoResultsPanel.classList.remove('hidden');
        const isReal = data.status === 'REAL';

        videoConfidence.textContent = data.confidence;

        videoVerdictBanner.className = 'verdict-banner ' + (isReal ? 'real' : 'fake');
        videoVerdictIcon.textContent  = isReal ? '✅' : '⚠️';
        videoVerdictTitle.textContent = isReal ? 'Authentic Video' : 'Manipulated / AI-Generated';
        videoVerdictTitle.style.color = isReal ? '#22c55e' : '#ef4444';
        videoVerdictMono.textContent  = isReal ? 'STATUS::GENUINE' : 'STATUS::SUSPICIOUS';
        
        // Display Reason
        const vReasonEl = document.getElementById('video-verdict-reason');
        if (vReasonEl) vReasonEl.textContent = data.reason || (isReal ? "Authentic video." : "Manipulated video.");

        videoAuthValue.textContent  = data.authentic_score + '%';
        videoManipValue.textContent = data.manipulated_score + '%';

        // Stats
        videoDuration.textContent     = data.duration + 's';
        videoTotalFrames.textContent  = data.total_frames;
        videoFramesAnalyz.textContent = data.frames_analyzed;
        videoElaScore.textContent     = data.ela_score + '%';

        requestAnimationFrame(() => setTimeout(() => {
            videoFillAuth.style.width  = data.authentic_score + '%';
            videoFillManip.style.width = data.manipulated_score + '%';
        }, 50));

        // Frame timeline
        frameTimeline.innerHTML = '';
        (data.frame_results || []).forEach(f => {
            const score = f.model_fake_score !== null ? f.model_fake_score : f.ela_score;
            const isFake = score > 50;
            const div = document.createElement('div');
            div.className = 'timeline-frame ' + (isFake ? 'tl-fake-frame' : 'tl-real-frame');
            div.innerHTML = `<span class="frame-ts">${f.timestamp}s</span><span class="frame-score">${score.toFixed(0)}%</span>`;
            div.title = `Frame at ${f.timestamp}s — ELA: ${f.ela_score}%${f.model_fake_score !== null ? ', Model fake: ' + f.model_fake_score + '%' : ''}`;
            frameTimeline.appendChild(div);
        });

        // Cybercrime
        videoCyberBlock.classList.toggle('hidden', isReal);
    }

    // ── NAVIGATION PILLS ───────────────────────────────────
    document.querySelectorAll('.pill').forEach(p => {
        p.style.cursor = 'pointer';
        p.addEventListener('click', () => {
            if (p.textContent.includes('Videos')) {
                switchTab('video');
            } else {
                switchTab('image');
            }
        });
    });

});
 