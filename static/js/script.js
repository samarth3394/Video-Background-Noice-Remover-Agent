document.addEventListener('DOMContentLoaded', () => {
    // Feature card animations on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('[data-animate]').forEach((el, index) => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(20px)';
        el.style.transition = `all 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s`;
        observer.observe(el);
    });

    // File Upload Logic
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    // Cards
    const uploadCard = document.getElementById('upload-card');
    const fileCard = document.getElementById('file-card');
    const processingCard = document.getElementById('processing-card');
    const doneCard = document.getElementById('done-card');
    
    // Elements
    const fileNameEl = document.getElementById('file-name');
    const fileSizeEl = document.getElementById('file-size');
    const removeBtn = document.getElementById('remove-file-btn');
    const processBtn = document.getElementById('process-btn');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    
    const progressFill = document.getElementById('progress-fill');
    const progressLabel = document.getElementById('progress-label');
    const processingStatus = document.getElementById('processing-status');

    let currentFile = null;
    let jobId = null;
    let checkInterval = null;

    // Helper: Format file size
    const formatSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    // Helper: Switch Cards
    const showCard = (cardToShow) => {
        [uploadCard, fileCard, processingCard, doneCard].forEach(card => {
            if (card === cardToShow) {
                card.classList.remove('hidden');
                // Tiny delay to ensure display:block applies before animating opacity if we added that
            } else {
                card.classList.add('hidden');
            }
        });
    };

    // Handle Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('video/')) {
                currentFile = file;
                fileNameEl.textContent = file.name;
                fileSizeEl.textContent = formatSize(file.size);
                showCard(fileCard);
            } else {
                alert('Please upload a valid video file.');
            }
        }
    }

    removeBtn.addEventListener('click', () => {
        currentFile = null;
        fileInput.value = '';
        showCard(uploadCard);
    });

    resetBtn.addEventListener('click', (e) => {
        e.preventDefault();
        currentFile = null;
        fileInput.value = '';
        jobId = null;
        if (checkInterval) clearInterval(checkInterval);
        showCard(uploadCard);
    });

    // Process Video
    processBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        showCard(processingCard);
        
        // Setup initial UI
        progressFill.style.width = '0%';
        progressLabel.textContent = '0%';
        processingStatus.textContent = 'Uploading video securely...';

        const formData = new FormData();
        formData.append('video', currentFile);

        try {
            // Simulated upload progress since fetch doesn't natively support it easily without XHR
            let uploadProgress = 0;
            const uploadSim = setInterval(() => {
                uploadProgress += 5;
                if (uploadProgress <= 90) {
                    progressFill.style.width = `${uploadProgress}%`;
                    progressLabel.textContent = `${uploadProgress}%`;
                }
            }, 200);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            clearInterval(uploadSim);

            const data = await response.json();

            if (data.job_id) {
                jobId = data.job_id;
                progressFill.style.width = '10%';
                progressLabel.textContent = '10%';
                processingStatus.textContent = 'Isolating voice using Meta Demucs AI... (This may take a few minutes)';
                pollStatus();
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            alert('Error: ' + error.message);
            showCard(fileCard);
        }
    });

    let progressInterval = null;

    function pollStatus() {
        // UI Dummy Progress (Independent of network)
        progressInterval = setInterval(() => {
            let currentWidth = parseFloat(progressFill.style.width) || 10;
            if (currentWidth < 95) {
                currentWidth += 0.5; 
                progressFill.style.width = `${currentWidth}%`;
                progressLabel.textContent = `${currentWidth.toFixed(1)}%`;
            }
        }, 1000); // 0.5% per second = ~3 mins to reach 95%

        // Network Polling
        let errorCount = 0;
        const checkStatus = async () => {
            try {
                const res = await fetch(`/status/${jobId}`);
                const data = await res.json();
                errorCount = 0; // Reset on success

                if (data.status === 'completed') {
                    clearInterval(progressInterval);
                    progressFill.style.width = '100%';
                    progressLabel.textContent = '100%';
                    
                    setTimeout(() => {
                        downloadBtn.href = `/download/${data.output_file}`;
                        showCard(doneCard);
                    }, 500);
                    return; // Stop polling
                } else if (data.status === 'error') {
                    clearInterval(progressInterval);
                    alert('Processing failed: ' + (data.error || 'Unknown error'));
                    showCard(fileCard);
                    return; // Stop polling
                }
            } catch (error) {
                console.error('Error checking status:', error);
                errorCount++;
                if (errorCount > 10) { // If it fails 10 times in a row (~30 seconds), server probably crashed
                    clearInterval(progressInterval);
                    alert('Connection lost. The AI process likely ran out of memory and crashed. Try a shorter video.');
                    showCard(fileCard);
                    return;
                }
            }
            
            // Queue next check
            checkInterval = setTimeout(checkStatus, 3000);
        };

        checkStatus();
    }

    // 3D Tilt Effect
    const interactiveCards = document.querySelectorAll('.upload-card, .state-card');
    
    interactiveCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * -3; // max 3 deg tilt
            const rotateY = ((x - centerX) / centerX) * 3;  // max 3 deg tilt
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            card.style.transition = `transform 0.1s ease-out`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)`;
            card.style.transition = `transform 0.6s cubic-bezier(0.23, 1, 0.32, 1)`;
        });
    });
});
