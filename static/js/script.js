document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const selectedFileArea = document.getElementById('selected-file');
    const processingArea = document.getElementById('processing-area');
    const resultArea = document.getElementById('result-area');
    const fileNameDisplay = document.getElementById('file-name');
    const fileSizeDisplay = document.getElementById('file-size');
    const processBtn = document.getElementById('process-btn');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const progressBar = document.getElementById('progress-bar');

    let selectedFile = null;

    // Drag and Drop Events
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

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            selectedFile = files[0];
            
            // Format size
            let size = selectedFile.size;
            let sizeStr = '';
            if (size > 1024 * 1024) {
                sizeStr = (size / (1024 * 1024)).toFixed(2) + ' MB';
            } else {
                sizeStr = (size / 1024).toFixed(2) + ' KB';
            }

            fileNameDisplay.textContent = selectedFile.name;
            fileSizeDisplay.textContent = sizeStr;

            dropZone.classList.add('hidden');
            selectedFileArea.classList.remove('hidden');
        }
    }

    // Process Video
    processBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        selectedFileArea.classList.add('hidden');
        processingArea.classList.remove('hidden');
        
        // Start simulated progress bar
        let progress = 0;
        progressBar.style.width = '0%';
        const interval = setInterval(() => {
            if(progress < 90) {
                progress += Math.random() * 2;
                progressBar.style.width = `${progress}%`;
            }
        }, 500);

        const formData = new FormData();
        formData.append('video', selectedFile);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                checkStatus(data.job_id, interval);
            } else {
                alert('Error: ' + data.error);
                resetUI();
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            alert('An error occurred while uploading the file.');
            resetUI();
        }
    });

    function checkStatus(jobId, interval) {
        const statusInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${jobId}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    clearInterval(statusInterval);
                    clearInterval(interval);
                    progressBar.style.width = '100%';
                    
                    setTimeout(() => {
                        processingArea.classList.add('hidden');
                        resultArea.classList.remove('hidden');
                        downloadBtn.href = `/download/${data.output_file}`;
                    }, 500);
                } else if (data.status === 'error') {
                    clearInterval(statusInterval);
                    clearInterval(interval);
                    alert('Error processing video: ' + data.error);
                    resetUI();
                }
            } catch (error) {
                console.error('Error checking status:', error);
            }
        }, 2000);
    }

    resetBtn.addEventListener('click', resetUI);

    function resetUI() {
        selectedFile = null;
        fileInput.value = '';
        dropZone.classList.remove('hidden');
        selectedFileArea.classList.add('hidden');
        processingArea.classList.add('hidden');
        resultArea.classList.add('hidden');
        progressBar.style.width = '0%';
    }
});
