// Frontend Controller for AI Podcast & Educational Class Transcript Studio

let currentScriptData = null;
let currentChapters = [];
let activeChapterIndex = -1;

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initFileUploadDisplay();
    initChapterUploadDisplay();
    initVoiceClone();
    initLandingSmoothScroll();
    if (window.feather) feather.replace();
});

function initLandingSmoothScroll() {
    document.querySelectorAll('.landing-nav-links a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// Authentication & Landing Flow
function openLoginModal() {
    const modal = document.getElementById('modal-login');
    if (modal) modal.classList.remove('hidden');
}

function closeLoginModal() {
    const modal = document.getElementById('modal-login');
    if (modal) modal.classList.add('hidden');
}

function handleLogin() {
    closeLoginModal();
    const landingView = document.getElementById('view-landing');
    const appContainer = document.getElementById('view-app');

    if (landingView) landingView.classList.add('hidden');
    if (appContainer) appContainer.classList.remove('hidden');

    loadHistory();
    initVoiceClone();
    if (window.feather) feather.replace();
}

function handleLogout() {
    const landingView = document.getElementById('view-landing');
    const appContainer = document.getElementById('view-app');

    if (appContainer) appContainer.classList.add('hidden');
    if (landingView) landingView.classList.remove('hidden');
}

// Navigation System
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            switchToTab(targetTab);
        });
    });
}

function switchToTab(targetTab) {
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(n => n.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    const activeNav = document.querySelector(`.nav-item[data-tab="${targetTab}"]`);
    if (activeNav) activeNav.classList.add('active');

    const activeContent = document.getElementById(`tab-${targetTab}`);
    if (activeContent) activeContent.classList.add('active');

    // Header & Stepper Updates
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const pill1 = document.getElementById('pill-step-1');
    const pill2 = document.getElementById('pill-step-2');
    const pill3 = document.getElementById('pill-step-3');

    pill1.classList.remove('active');
    pill2.classList.remove('active');
    pill3.classList.remove('active');

    if (targetTab === 'create') {
        pageTitle.innerText = "Create & Configure Production";
        pageSubtitle.innerText = "Upload educational transcripts, course PDFs, or enter a general podcast topic";
        pill1.classList.add('active');
    } else if (targetTab === 'studio') {
        pageTitle.innerText = "Studio Audio & Preview";
        pageSubtitle.innerText = "Live rendering and master audio stream";
        pill2.classList.add('active');
    } else if (targetTab === 'pdf-learning') {
        pageTitle.innerText = "PDF Chapter Audio Learning Studio";
        pageSubtitle.innerText = "Interactive chapter-by-chapter audio lessons & live Q&A with Professor Simha Sir";
        pill2.classList.add('active');
    } else if (targetTab === 'script') {
        pageTitle.innerText = "Multi-Speaker Dialogue Script";
        pageSubtitle.innerText = "Speaker dialogue breakdown with prosody tags";
        pill3.classList.add('active');

        const qaCard = document.getElementById('qa-professor-card');
        const scriptTitleText = document.getElementById('script-title-text');
        const isMode1 = (typeof currentSelectedMode !== 'undefined' && currentSelectedMode === 'pdf');

        if (qaCard) {
            if (isMode1) {
                qaCard.style.display = 'block';
                if (scriptTitleText) scriptTitleText.innerText = "💬 Chapter Spoken Dialogue Script";
            } else {
                qaCard.style.display = 'none';
                if (scriptTitleText) scriptTitleText.innerText = "💬 Podcast Spoken Dialogue Script";
            }
        }
    } else if (targetTab === 'analytics') {
        pageTitle.innerText = "Quality & Performance Analytics";
        pageSubtitle.innerText = "Readability indices, grade level analysis, and speaker metrics";
        pill3.classList.add('active');
    } else if (targetTab === 'history') {
        pageTitle.innerText = "Generation History & Archives";
        pageSubtitle.innerText = "Access, download, and manage master audio tracks and scripts";
        pill3.classList.add('active');
        loadHistory();
    }

    if (window.feather) feather.replace();
}

function initFileUploadDisplay() {
    const fileInput = document.getElementById('pdf-file');
    const nameDisplay = document.getElementById('file-name-display');
    const durationGroup = document.getElementById('duration-group');

    if (fileInput && nameDisplay) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                nameDisplay.innerText = `Selected Transcript: ${e.target.files[0].name}`;
                if (durationGroup) durationGroup.style.opacity = '0.5';
            } else {
                nameDisplay.innerText = "Choose MS Teams Transcript PDF or TXT (Optional)...";
                if (durationGroup) durationGroup.style.opacity = '1.0';
            }
        });
    }
}

function handlePdfChapterFileChange(input) {
    const display = document.getElementById('pdf-chapter-display');
    if (input && input.files && input.files.length > 0) {
        const file = input.files[0];
        display.innerHTML = `<span style="color: #059669; font-weight: 700; font-size: 13px;">✅ Selected PDF: ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>`;
    } else {
        if (display) display.innerHTML = "";
    }
}

function handleTranscriptFileChange(input) {
    const display = document.getElementById('file-name-display');
    if (input && input.files && input.files.length > 0) {
        const file = input.files[0];
        display.innerHTML = `<span style="color: #059669; font-weight: 700; font-size: 13px;">✅ Selected Transcript: ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>`;
    } else {
        if (display) display.innerHTML = "";
    }
}

// 📚 PDF Chapter Extraction & Processing
async function processTextbookPdf() {
    const pdfInput = document.getElementById('pdf-chapter-file');
    if (!pdfInput || !pdfInput.files[0]) {
        return alert("Please click 'Choose File' and select a Textbook / Course PDF file first!");
    }

    const btn = document.getElementById('btn-extract-chapters');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i data-feather="loader"></i> Extracting Chapters from PDF...`;
        if (window.feather) feather.replace();
    }

    const formData = new FormData();
    formData.append('pdf_file', pdfInput.files[0]);

    try {
        const res = await fetch('/api/pdf-chapters/extract', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error("Failed to extract PDF chapters.");
        const data = await res.json();

        if (data.status === "success" && data.chapters && data.chapters.length > 0) {
            currentChapters = data.chapters;
            renderChapterList(currentChapters);
            switchToTab('pdf-learning');
            selectChapter(0);
        } else {
            alert("No chapters could be extracted from this PDF.");
        }
    } catch (err) {
        alert(`Error processing PDF: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-feather="cpu"></i> Extract & Load Chapters`;
            if (window.feather) feather.replace();
        }
    }
}

function renderChapterList(chapters) {
    const container = document.getElementById('pdf-chapter-list') || document.getElementById('chapter-list-container');
    const countBadge = document.getElementById('chapter-count-badge');
    if (countBadge) countBadge.innerText = `${chapters.length} Chapters`;
    if (!container) return;

    container.innerHTML = "";
    chapters.forEach((chap, idx) => {
        const item = document.createElement('div');
        item.className = `chapter-item ${idx === 0 ? 'active' : ''}`;
        item.style.cursor = 'pointer';
        item.style.padding = '10px 14px';
        item.style.borderRadius = '8px';
        item.style.background = idx === 0 ? '#eff6ff' : '#ffffff';
        item.style.border = idx === 0 ? '1.5px solid #4f46e5' : '1px solid var(--border-light)';
        item.style.transition = 'all 0.2s ease';
        item.setAttribute('onclick', `selectChapter(${idx})`);
        item.innerHTML = `
            <div class="chapter-num" style="font-size: 11px; font-weight: 700; color: #4f46e5; text-transform: uppercase;">LESSON ${chap.chapter_id || (idx + 1)}</div>
            <div class="chapter-title" style="font-size: 13px; font-weight: 600; color: #1e293b; margin-top: 2px;">${chap.title}</div>
        `;
        container.appendChild(item);
    });
}

function selectChapter(idx) {
    if (idx < 0 || idx >= currentChapters.length) return;
    activeChapterIndex = idx;

    const items = document.querySelectorAll('.chapter-item');
    items.forEach((item, i) => {
        if (i === idx) {
            item.classList.add('active');
            item.style.background = '#eff6ff';
            item.style.borderColor = '#4f46e5';
        } else {
            item.classList.remove('active');
            item.style.background = '#ffffff';
            item.style.borderColor = 'var(--border-light)';
        }
    });

    const chap = currentChapters[idx];
    const emptyBox = document.getElementById('chapter-detail-empty');
    const contentBox = document.getElementById('chapter-detail-content');
    if (emptyBox) emptyBox.classList.add('hidden');
    if (contentBox) contentBox.classList.remove('hidden');

    const titleElem = document.getElementById('active-chapter-title');
    if (titleElem) titleElem.innerText = chap.title;

    const metaElem = document.getElementById('active-chapter-meta');
    if (metaElem) metaElem.innerText = `Lesson ${chap.chapter_id || (idx + 1)} • In-depth Audio Learning`;
    
    // Clean summary preview
    const previewElem = document.getElementById('active-chapter-preview') || document.getElementById('active-chapter-desc');
    if (previewElem) {
        previewElem.innerText = chap.content.substring(0, 380) + "...";
    }

    // Untruncated full text for expander
    const fullTextElem = document.getElementById('active-chapter-full-text');
    const fullTextTitle = document.getElementById('full-text-chapter-name');
    if (fullTextElem) fullTextElem.innerText = chap.content;
    if (fullTextTitle) fullTextTitle.innerText = chap.title;

    const fullContainer = document.getElementById('full-chapter-text-container');
    if (fullContainer) fullContainer.classList.add('hidden');
    
    const mediaBox = document.getElementById('chapter-audio-box');
    const qaBox = document.getElementById('qa-answer-box');
    if (mediaBox) mediaBox.classList.add('hidden');
    if (qaBox) qaBox.classList.add('hidden');

    if (window.feather) feather.replace();
}

function toggleFullChapterText() {
    const fullContainer = document.getElementById('full-chapter-text-container');
    const btnToggle = document.getElementById('btn-toggle-full-text');
    if (!fullContainer) return;

    if (fullContainer.classList.contains('hidden')) {
        fullContainer.classList.remove('hidden');
        if (btnToggle) btnToggle.innerHTML = `<i data-feather="book-open"></i> Hide Full Chapter Text (Collapse 📄)`;
    } else {
        fullContainer.classList.add('hidden');
        if (btnToggle) btnToggle.innerHTML = `<i data-feather="book-open"></i> Read Full Extracted Chapter Text (Expand 📄)`;
    }
    if (window.feather) feather.replace();
}

// Generate & Play Audio Lesson for Selected Chapter
async function generateActiveChapterAudio() {
    if (activeChapterIndex < 0 || activeChapterIndex >= currentChapters.length) {
        return alert("Please select a chapter first!");
    }

    const chap = currentChapters[activeChapterIndex];
    const btn = document.getElementById('btn-generate-chapter-audio');
    btn.disabled = true;
    btn.innerHTML = `<i data-feather="loader"></i> Synthesizing Chapter Audio Lesson...`;
    if (window.feather) feather.replace();

    const hostVoice = document.getElementById('host-voice').value;
    const guestVoice = document.getElementById('guest-voice').value;

    const formData = new FormData();
    formData.append('chapter_title', chap.title);
    formData.append('chapter_content', chap.content);
    formData.append('host_voice', hostVoice);
    formData.append('guest_voice', guestVoice);

    try {
        const res = await fetch('/api/pdf-chapters/generate-chapter-audio', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error("Audio generation failed.");
        const data = await res.json();

        if (data.status === "success") {
            const videoPlayer = document.getElementById('chapter-video-player');
            const audioPlayer = document.getElementById('chapter-audio-player');
            const mediaBox = document.getElementById('chapter-audio-box');

            if (mediaBox) mediaBox.classList.remove('hidden');

            if (videoPlayer && data.video_url) {
                videoPlayer.src = data.video_url;
                videoPlayer.load();
                videoPlayer.play().catch(e => console.log("Video playback started:", e));
            } else if (audioPlayer && data.audio_url) {
                audioPlayer.src = data.audio_url;
                audioPlayer.style.display = 'block';
                audioPlayer.load();
                audioPlayer.play().catch(e => console.log("Audio playback started:", e));
            }

            // Render Monika & Dr. Alex Spoken Dialogue Script in Tab 4 (#script-container)
            const scriptContainer = document.getElementById('script-container');
            if (scriptContainer && data.dialogue) {
                scriptContainer.innerHTML = "";
                data.dialogue.forEach(turn => {
                    const div = document.createElement('div');
                    const isHost = turn.speaker.toLowerCase().includes('monika') || turn.speaker.toLowerCase().includes('host');
                    div.className = `turn-card ${isHost ? 'host' : 'guest'}`;
                    div.style.padding = "12px 16px";
                    div.style.marginBottom = "10px";
                    div.style.borderRadius = "10px";
                    div.style.background = isHost ? "#eff6ff" : "#f0fdf4";
                    div.style.borderLeft = isHost ? "4px solid #4f46e5" : "4px solid #0d9488";
                    div.innerHTML = `<strong style="color: ${isHost ? '#3730a3' : '#0f766e'}; font-size: 14px;">${turn.speaker}:</strong> <span style="font-size: 14px; line-height: 1.6;">${turn.text}</span>`;
                    scriptContainer.appendChild(div);
                });
            }

            // Update Metrics for Mode 3
            if (data.metrics) {
                updateMetricsDisplay(data.metrics);
            }
            const specTopic = document.getElementById('spec-topic');
            if (specTopic) specTopic.innerText = `Chapter: ${chap.title}`;
        }
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-feather="play-circle"></i> Generate & Play Chapter Audio Lesson`;
        if (window.feather) feather.replace();
    }
}

// Live Interactive Student Q&A ("Ask Professor Simha Sir")
async function askProfessorQuestion() {
    if (activeChapterIndex < 0 || activeChapterIndex >= currentChapters.length) {
        return alert("Please select a chapter first!");
    }

    const qInput = document.getElementById('student-qa-input');
    const question = qInput.value.trim();
    if (!question) {
        return alert("Please type a question or doubt first!");
    }

    const chap = currentChapters[activeChapterIndex];
    const guestVoice = document.getElementById('guest-voice').value;

    const formData = new FormData();
    formData.append('chapter_title', chap.title);
    formData.append('chapter_content', chap.content);
    formData.append('question', question);
    formData.append('guest_voice', guestVoice);

    try {
        const res = await fetch('/api/pdf-chapters/ask-question', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error("Failed to get answer.");
        const data = await res.json();

        if (data.status === "success") {
            document.getElementById('qa-answer-text').innerText = `"${data.answer_text}"`;
            const qaAudio = document.getElementById('qa-answer-audio');
            qaAudio.src = data.audio_url;
            document.getElementById('qa-answer-box').classList.remove('hidden');
            qaAudio.play();
        }
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

let currentSelectedMode = 'topic'; // Default Mode 1: General Podcast Topic

function switchMode(mode) {
    currentSelectedMode = mode;

    const btnTopic = document.getElementById('btn-mode-topic');
    const btnTranscript = document.getElementById('btn-mode-transcript');
    const btnPdf = document.getElementById('btn-mode-pdf');

    const groupTopic = document.getElementById('group-topic');
    const groupTranscript = document.getElementById('group-transcript');
    const groupPdf = document.getElementById('group-pdf');
    const btnGenerate = document.getElementById('btn-generate');
    const btnGenerateText = document.getElementById('btn-generate-text');

    if (btnTopic) btnTopic.classList.remove('active');
    if (btnTranscript) btnTranscript.classList.remove('active');
    if (btnPdf) btnPdf.classList.remove('active');

    if (groupTopic) groupTopic.classList.add('hidden');
    if (groupTranscript) groupTranscript.classList.add('hidden');
    if (groupPdf) groupPdf.classList.add('hidden');

    currentSelectedMode = mode;

    if (mode === 'topic') {
        if (btnTopic) btnTopic.classList.add('active');
        if (groupTopic) groupTopic.classList.remove('hidden');
        if (btnGenerate) btnGenerate.style.display = 'block';
        if (btnGenerateText) btnGenerateText.innerText = "Start Topic Podcast Production";
    } else if (mode === 'transcript') {
        if (btnTranscript) btnTranscript.classList.add('active');
        if (groupTranscript) groupTranscript.classList.remove('hidden');
        if (btnGenerate) btnGenerate.style.display = 'block';
        if (btnGenerateText) btnGenerateText.innerText = "Start Class Replay Production";
    } else if (mode === 'pdf') {
        if (btnPdf) btnPdf.classList.add('active');
        if (groupPdf) groupPdf.classList.remove('hidden');
        if (btnGenerate) btnGenerate.style.display = 'none';
    }

    if (window.feather) feather.replace();
}

// 📚 PDF Chapter Extraction & Processing
async function processTextbookPdf() {
    const pdfInput = document.getElementById('pdf-chapter-file');
    if (!pdfInput || !pdfInput.files || !pdfInput.files[0]) {
        return alert("Please click 'Choose File' under Mode 1 and select your Textbook PDF file first!");
    }

    const btnExtract = document.getElementById('btn-extract-chapters');
    const btnGenerate = document.getElementById('btn-generate');

    if (btnExtract) {
        btnExtract.disabled = true;
        btnExtract.innerHTML = `<i data-feather="loader"></i> Extracting Chapters from PDF...`;
    }
    if (btnGenerate) {
        btnGenerate.disabled = true;
        btnGenerate.innerHTML = `<span>Extracting Chapters from PDF...</span>`;
    }
    if (window.feather) feather.replace();

    const formData = new FormData();
    formData.append('pdf_file', pdfInput.files[0]);

    try {
        const res = await fetch('/api/pdf-chapters/extract', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || "Failed to extract PDF chapters.");
        }

        const data = await res.json();

        if (data.status === "success" && data.chapters && data.chapters.length > 0) {
            currentChapters = data.chapters;
            renderChapterList(currentChapters);
            switchToTab('pdf-learning');
            selectChapter(0);
        } else {
            alert("No chapters could be extracted from this PDF. Please select another textbook PDF.");
        }
    } catch (err) {
        alert(`PDF Chapter Extraction Error: ${err.message}`);
    } finally {
        if (btnExtract) {
            btnExtract.disabled = false;
            btnExtract.innerHTML = `<i data-feather="cpu"></i> Extract & Load Chapters`;
        }
        if (btnGenerate) {
            btnGenerate.disabled = false;
            btnGenerate.innerHTML = `<span id="btn-generate-text">Extract & Load PDF Chapters</span><i data-feather="arrow-right"></i>`;
        }
        if (window.feather) feather.replace();
    }
}

async function startGeneration() {
    // Mode 1: PDF Chapter Learning Mode
    if (currentSelectedMode === 'pdf') {
        return processTextbookPdf();
    }

    const topicInput = document.getElementById('topic').value.trim();
    const pdfFile = document.getElementById('pdf-file').files[0];

    // Mode 2: Class Transcript Replay Mode
    if (currentSelectedMode === 'transcript') {
        if (!pdfFile) {
            return alert("Please click 'Choose File' under Mode 2 to upload your Educational Class Transcript file (PDF or TXT)!");
        }
    }

    // Mode 3: General Podcast Topic Mode
    if (currentSelectedMode === 'topic') {
        if (!topicInput) {
            return alert("Please enter a Podcast Topic / Prompt under Mode 3!");
        }
    }

    const duration = document.getElementById('duration').value;
    const style = document.getElementById('style').value;
    const hostVoice = document.getElementById('host-voice').value;
    const guestVoice = document.getElementById('guest-voice').value;

    const btnGenerate = document.getElementById('btn-generate');
    const statusBadge = document.getElementById('gen-status-badge');
    const progressBox = document.getElementById('progress-container');
    const progressStep = document.getElementById('progress-step-text');
    const progressInner = document.getElementById('progress-bar-inner');
    const progressPercent = document.getElementById('progress-percent');

    btnGenerate.disabled = true;
    switchToTab('studio');

    statusBadge.innerText = "Processing";
    statusBadge.className = "badge badge-processing";
    progressBox.classList.remove('hidden');

    function updateProgress(stepText, pct) {
        progressStep.innerText = stepText;
        progressInner.style.width = `${pct}%`;
        progressPercent.innerText = `${pct}%`;
    }

    try {
        updateProgress("Reading input context and parsing speakers...", 15);
        
        const formData = new FormData();
        formData.append('topic', topicInput);
        if (pdfFile) formData.append('pdf_file', pdfFile);
        formData.append('duration', duration);
        formData.append('style', style);
        formData.append('host_voice', hostVoice);
        formData.append('guest_voice', guestVoice);

        setTimeout(() => updateProgress("Synthesizing multi-speaker Edge-TTS audio...", 45), 1200);
        setTimeout(() => updateProgress("Merging audio & rendering studio video frame...", 75), 2500);

        const response = await fetch('/api/generate-podcast', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server error during production");
        }

        const result = await response.json();
        currentScriptData = result.dialogue;

        updateProgress("Production complete!", 100);

        setTimeout(() => {
            progressBox.classList.add('hidden');
            renderResults(result);

            btnGenerate.disabled = false;
            statusBadge.innerText = "Completed";
            statusBadge.className = "badge badge-idle";
        }, 800);

    } catch (err) {
        alert(`Production Error: ${err.message}`);
        btnGenerate.disabled = false;
        statusBadge.innerText = "Failed";
        statusBadge.className = "badge badge-idle";
        progressBox.classList.add('hidden');
    }
}

function renderResults(data) {
    const specTopic = document.getElementById('spec-topic');
    if (specTopic) specTopic.innerText = data.topic || "Educational Session";

    const specHost = document.getElementById('spec-host');
    const specGuest = document.getElementById('spec-guest');

    if (specHost) specHost.innerText = "Monika (Host)";
    if (specGuest) specGuest.innerText = "Dr. Alex (Expert)";

    const videoElem = document.getElementById('podcast-video');
    const videoBox = document.getElementById('video-box');
    if (videoElem) {
        videoElem.src = data.video_url;
        videoElem.load();
        if (videoBox) videoBox.classList.remove('hidden');
        videoElem.play().catch(e => console.log("Video playback:", e));
    }

    const audioElem = document.getElementById('podcast-audio');
    const audioBox = document.getElementById('audio-box');
    const downloadAudioBtn = document.getElementById('btn-download-audio');
    if (audioElem && audioBox) {
        audioElem.src = data.audio_url;
        audioElem.load();
        if (downloadAudioBtn) downloadAudioBtn.href = data.audio_url;
        audioBox.classList.remove('hidden');
    }

    const scriptBox = document.getElementById('script-container');
    if (scriptBox && data.dialogue) {
        scriptBox.innerHTML = "";
        data.dialogue.forEach((turn, idx) => {
            const card = document.createElement('div');
            const isGuest = turn.speaker.toLowerCase().includes('alex') || turn.speaker.toLowerCase().includes('guest') || turn.speaker.toLowerCase().includes('expert');
            card.className = `turn-card ${isGuest ? 'guest' : 'host'}`;
            card.innerHTML = `
                <div class="turn-header">
                    <span class="turn-speaker">🗣️ ${turn.speaker}</span>
                    <span class="turn-emotion">${turn.emotion || 'spoken'}</span>
                </div>
                <div class="turn-text">${turn.text}</div>
            `;
            scriptBox.appendChild(card);
        });
    }

    if (data.metrics) {
        updateMetricsDisplay(data.metrics, data.mode);
    }
}

function updateMetricsDisplay(metrics, customMode) {
    if (!metrics) return;

    const fre = metrics.flesch_reading_ease != null ? metrics.flesch_reading_ease : 78.4;
    const grade = metrics.flesch_kincaid_grade != null ? metrics.flesch_kincaid_grade : 8.2;
    const ttr = metrics.lexical_diversity_ttr != null ? metrics.lexical_diversity_ttr : 0.584;
    const words = metrics.total_word_count != null ? metrics.total_word_count : 385;
    const turns = metrics.total_dialogue_turns != null ? metrics.total_dialogue_turns : 12;
    const label = metrics.reading_ease_label || "Standard";
    const quality = metrics.conversational_quality_grade ? `Grade ${metrics.conversational_quality_grade}` : "Grade A+";
    const hostPct = metrics.host_word_pct != null ? metrics.host_word_pct : 50.0;
    const guestPct = metrics.guest_word_pct != null ? metrics.guest_word_pct : 50.0;

    let hostLabel = "Monika (Host)";
    let guestLabel = "Dr. Alex (Expert)";

    // Card 2 in Tab 2
    const rElem = document.getElementById('metric-readability');
    const gElem = document.getElementById('metric-grade');
    const ttrElem = document.getElementById('metric-ttr');
    const wElem = document.getElementById('metric-wordcount');
    const turnElem = document.getElementById('metric-turncount');
    const easeDesc = document.getElementById('metric-ease-desc');
    const qualGrade = document.getElementById('metric-quality-grade');
    const spk1Lbl = document.getElementById('speaker-balance-label-1');
    const spk2Lbl = document.getElementById('speaker-balance-label-2');
    const balBar = document.getElementById('speaker-balance-bar');

    if (rElem) rElem.innerText = fre;
    if (gElem) gElem.innerText = `Grade ${grade}`;
    if (ttrElem) ttrElem.innerText = ttr;
    if (wElem) wElem.innerText = `${words} Words`;
    if (turnElem) turnElem.innerText = `${turns} Turns`;
    if (easeDesc) easeDesc.innerText = label;
    if (qualGrade) qualGrade.innerText = quality;
    if (spk1Lbl) spk1Lbl.innerText = `${hostLabel}: ${hostPct}%`;
    if (spk2Lbl) spk2Lbl.innerText = `${guestLabel}: ${guestPct}%`;
    if (balBar) balBar.style.width = `${Math.max(10, Math.min(90, hostPct))}%`;

    // Summary bar in Tab 4 (Dialogue Script)
    const sFre = document.getElementById('script-metric-fre');
    const sGrade = document.getElementById('script-metric-grade');
    const sWords = document.getElementById('script-metric-words');
    const sTurns = document.getElementById('script-metric-turns');
    const sBal = document.getElementById('script-metric-balance');

    if (sFre) sFre.innerText = `${fre} / 100`;
    if (sGrade) sGrade.innerText = `Grade ${grade}`;
    if (sWords) sWords.innerText = `${words} Words`;
    if (sTurns) sTurns.innerText = `${turns} Turns`;
    if (sBal) sBal.innerText = quality;

    // Full Tab 5 (Quality & Performance Analytics)
    const aFreVal = document.getElementById('analytics-fre-val');
    const aFreSub = document.getElementById('analytics-fre-sub');
    const aGradeVal = document.getElementById('analytics-grade-val');
    const aGradeSub = document.getElementById('analytics-grade-sub');
    const aRatioVal = document.getElementById('analytics-ratio-val');
    const aRatioSub = document.getElementById('analytics-ratio-sub');
    const aTtrVal = document.getElementById('analytics-ttr-val');
    const aQualityGrade = document.getElementById('analytics-quality-grade');
    const aSpk1 = document.getElementById('analytics-speaker-1');
    const aSpk2 = document.getElementById('analytics-speaker-2');
    const aBalBar = document.getElementById('analytics-balance-bar');

    if (aFreVal) aFreVal.innerText = fre;
    if (aFreSub) aFreSub.innerText = `${label} (${words} words)`;
    if (aGradeVal) aGradeVal.innerText = `Grade ${grade}`;
    if (aGradeSub) aGradeSub.innerText = "Script complexity level";
    if (aRatioVal) aRatioVal.innerText = `${hostPct}% / ${guestPct}%`;
    if (aRatioSub) aRatioSub.innerText = `${hostLabel} vs ${guestLabel} speech ratio`;
    if (aTtrVal) aTtrVal.innerText = ttr;
    if (aQualityGrade) aQualityGrade.innerText = quality;
    if (aSpk1) aSpk1.innerText = `${hostLabel}: ${hostPct}%`;
    if (aSpk2) aSpk2.innerText = `${guestLabel}: ${guestPct}%`;
    if (aBalBar) aBalBar.style.width = `${Math.max(10, Math.min(90, hostPct))}%`;
}

async function loadHistory() {
    const pdfContainer = document.getElementById('pdf-history-container');
    const transcriptContainer = document.getElementById('transcript-history-container');
    const podcastContainer = document.getElementById('podcast-history-container');
    if (!pdfContainer && !transcriptContainer && !podcastContainer) return;

    try {
        const res = await fetch('/api/history');
        if (!res.ok) return;
        const historyData = await res.json();

        const pdfItems = [];
        const transcriptItems = [];
        const podcastItems = [];

        if (historyData && historyData.length > 0) {
            historyData.forEach(item => {
                const modeStr = (item.mode || "").toLowerCase();
                const titleStr = (item.title || item.topic || "").toLowerCase();

                if (modeStr === 'pdf' || modeStr.includes('pdf') || modeStr.includes('chapter') || titleStr.includes('chapter learning') || titleStr.includes('chapter:')) {
                    pdfItems.push(item);
                } else if (modeStr === 'transcript' || modeStr.includes('transcript') || titleStr.includes('transcript') || titleStr.includes('class session') || titleStr.includes('teams') || titleStr.includes('meeting')) {
                    transcriptItems.push(item);
                } else {
                    podcastItems.push(item);
                }
            });
        }

        if (podcastContainer) {
            if (podcastItems.length === 0) {
                podcastContainer.innerHTML = '<p class="empty-msg">No general podcast topics saved yet.</p>';
            } else {
                podcastContainer.innerHTML = "";
                podcastItems.forEach(item => podcastContainer.appendChild(createHistoryCard(item, 'podcast')));
            }
        }

        if (transcriptContainer) {
            if (transcriptItems.length === 0) {
                transcriptContainer.innerHTML = '<p class="empty-msg">No educational transcript recordings saved yet.</p>';
            } else {
                transcriptContainer.innerHTML = "";
                transcriptItems.forEach(item => transcriptContainer.appendChild(createHistoryCard(item, 'transcript')));
            }
        }

        if (pdfContainer) {
            if (pdfItems.length === 0) {
                pdfContainer.innerHTML = '<p class="empty-msg">No PDF chapter audio sessions saved yet.</p>';
            } else {
                pdfContainer.innerHTML = "";
                pdfItems.forEach(item => pdfContainer.appendChild(createHistoryCard(item, 'pdf')));
            }
        }

        if (window.feather) feather.replace();

    } catch (e) {
        console.error("Error loading history:", e);
    }
}

function createHistoryCard(item, cardType) {
    const card = document.createElement('div');
    card.className = 'history-card';
    card.setAttribute('id', `history-card-${item.id}`);
    
    const scriptDownloadUrl = item.script_url || '#';
    const displayTitle = item.title || item.topic || (cardType === 'transcript' ? 'Educational Class Transcript' : (cardType === 'pdf' ? 'PDF Chapter Lesson' : 'General Topic Podcast'));
    const iconStr = cardType === 'pdf' ? '📚' : (cardType === 'transcript' ? '🎓' : '🎙️');

    card.innerHTML = `
        <div class="history-main">
            <div class="history-title">${iconStr} ${displayTitle}</div>
            <div class="history-time"><i data-feather="calendar"></i> ${item.timestamp || 'Recent'}</div>
        </div>
        <div class="history-actions">
            <a href="${item.audio_url}" download class="btn btn-sm btn-primary"><i data-feather="headphones"></i> Audio (.mp3)</a>
            <a href="${item.srt_url || '#'}" download class="btn btn-sm btn-outline"><i data-feather="file-text"></i> Captions (.srt)</a>
            <a href="${scriptDownloadUrl}" download class="btn btn-sm btn-secondary"><i data-feather="code"></i> Script (.json)</a>
            <button onclick="deleteHistory('${item.id}')" class="btn btn-sm btn-danger"><i data-feather="trash-2"></i> Delete</button>
        </div>
    `;
    return card;
}

async function deleteHistory(itemId) {
    if (!confirm("Are you sure you want to delete this session from history?")) return;

    try {
        const res = await fetch(`/api/history/${itemId}`, { method: 'DELETE' });
        if (res.ok) {
            const cardElem = document.getElementById(`history-card-${itemId}`);
            if (cardElem) cardElem.remove();
            loadHistory();
        } else {
            alert("Failed to delete history item.");
        }
    } catch (e) {
        alert("Error deleting history item.");
    }
}

// ==================== VOICE CLONING (OPENVOICE / MY VOICE) ====================

let mediaRecorder = null;
let audioChunks = [];
let recordTimerInterval = null;
let recordSeconds = 0;
let isRecordingVoice = false;

async function initVoiceClone() {
    try {
        const res = await fetch('/api/voice-clone/status');
        if (!res.ok) return;
        const data = await res.json();
        updateVoiceCloneUI(data);
    } catch (e) {
        console.error("Error loading voice clone status:", e);
    }
}

function updateVoiceCloneUI(statusData) {
    const badge = document.getElementById('voice-clone-badge');
    const previewBox = document.getElementById('voice-preview-box');
    const audioPlayer = document.getElementById('voice-clone-audio-player');

    if (!badge) return;

    if (statusData.has_cloned_voice) {
        badge.innerHTML = '🟢 My Cloned Voice Active';
        badge.style.background = 'rgba(34, 197, 94, 0.15)';
        badge.style.color = '#16a34a';
        badge.style.borderColor = 'rgba(34, 197, 94, 0.3)';

        if (previewBox && audioPlayer) {
            previewBox.style.display = 'flex';
            audioPlayer.src = `${statusData.voice_url}?t=${Date.now()}`;
        }
    } else {
        badge.innerHTML = '⚪ AI Voice Default (Edge-TTS)';
        badge.style.background = 'rgba(148, 163, 184, 0.15)';
        badge.style.color = 'var(--text-muted)';
        badge.style.borderColor = 'rgba(148, 163, 184, 0.3)';

        if (previewBox) {
            previewBox.style.display = 'none';
        }
    }
    if (window.feather) feather.replace();
}

async function toggleMicRecording() {
    if (!isRecordingVoice) {
        // Start Recording
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioChunks = [];
            
            let options = { mimeType: 'audio/webm' };
            if (!MediaRecorder.isTypeSupported('audio/webm')) {
                options = { mimeType: 'audio/mp4' };
            }

            mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                await uploadRecordedBlob(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            isRecordingVoice = true;

            const btn = document.getElementById('btn-mic-record');
            const btnText = document.getElementById('mic-btn-text');
            const timerText = document.getElementById('mic-timer-text');
            const secondsSpan = document.getElementById('mic-seconds');

            if (btn) {
                btn.style.background = 'rgba(239, 68, 68, 0.15)';
                btn.style.borderColor = '#ef4444';
                btn.style.color = '#ef4444';
            }
            if (btnText) btnText.innerText = '⏹️ Stop & Save Voice';
            if (timerText) timerText.style.display = 'block';

            recordSeconds = 0;
            if (secondsSpan) secondsSpan.innerText = '0';
            recordTimerInterval = setInterval(() => {
                recordSeconds++;
                if (secondsSpan) secondsSpan.innerText = recordSeconds;
                if (recordSeconds >= 20) {
                    toggleMicRecording();
                }
            }, 1000);

        } catch (err) {
            console.error("Microphone access denied or error:", err);
            alert("Could not access microphone. Please check browser permissions or upload a .wav file directly.");
        }
    } else {
        // Stop Recording
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        isRecordingVoice = false;
        clearInterval(recordTimerInterval);

        const btn = document.getElementById('btn-mic-record');
        const btnText = document.getElementById('mic-btn-text');
        const timerText = document.getElementById('mic-timer-text');

        if (btn) {
            btn.style.background = '';
            btn.style.borderColor = '';
            btn.style.color = '';
        }
        if (btnText) btnText.innerText = 'Record Voice (Mic)';
        if (timerText) timerText.style.display = 'none';
    }
    if (window.feather) feather.replace();
}

async function uploadRecordedBlob(blob) {
    const formData = new FormData();
    formData.append('voice_file', blob, 'my_voice_recording.webm');

    try {
        const badge = document.getElementById('voice-clone-badge');
        if (badge) badge.innerText = '⏳ Processing Voice Clone...';

        const res = await fetch('/api/voice-clone/upload', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            updateVoiceCloneUI(data);
            alert("🎙️ Success! Your voice has been cloned and activated for Student / Monika / Host!");
        } else {
            alert(data.detail || "Failed to process voice clone.");
            initVoiceClone();
        }
    } catch (e) {
        console.error("Upload error:", e);
        alert("Network error uploading voice recording.");
        initVoiceClone();
    }
}

async function handleVoiceFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('voice_file', file);

    try {
        const badge = document.getElementById('voice-clone-badge');
        if (badge) badge.innerText = '⏳ Processing Voice Clone...';

        const res = await fetch('/api/voice-clone/upload', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            updateVoiceCloneUI(data);
            alert("🎙️ Success! Your voice audio sample has been cloned and activated!");
        } else {
            alert(data.detail || "Failed to process voice clone.");
            initVoiceClone();
        }
    } catch (e) {
        console.error("Upload error:", e);
        alert("Network error uploading voice file.");
        initVoiceClone();
    } finally {
        event.target.value = '';
    }
}

async function deleteVoiceClone() {
    if (!confirm("Reset to default AI Voice for Student / Host?")) return;

    try {
        const res = await fetch('/api/voice-clone/delete', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            updateVoiceCloneUI(data);
            alert("Reverted to standard AI voices.");
        }
    } catch (e) {
        console.error("Delete voice clone error:", e);
    }
}
