// Estado de la aplicación
let selectedFormat = 'mp3';
let selectedQuality = 'best';
let isProcessing = false;
let downloadUrl = null;

// Elementos del DOM
const urlInput = document.getElementById('youtube-url');
const urlError = document.getElementById('url-error');
const formatBtns = document.querySelectorAll('.format-btn');
const qualityBtns = document.querySelectorAll('.quality-btn');
const qualitySection = document.getElementById('quality-section');
const videoInfo = document.getElementById('video-info');
const progressContainer = document.getElementById('progress-container');
const successMessage = document.getElementById('success-message');
const errorAlert = document.getElementById('error-alert');
const convertBtn = document.getElementById('convert-btn');
const resetBtn = document.getElementById('reset-btn');
const downloadBtn = document.getElementById('download-btn');
const progressFill = document.getElementById('progress-fill');
const progressPercent = document.getElementById('progress-percent');
const errorText = document.getElementById('error-text');
const successText = document.getElementById('success-text');

// Event Listeners
formatBtns.forEach(btn => {
    btn.addEventListener('click', handleFormatChange);
});

qualityBtns.forEach(btn => {
    btn.addEventListener('click', handleQualityChange);
});

convertBtn.addEventListener('click', handleConvert);
resetBtn.addEventListener('click', resetForm);
downloadBtn.addEventListener('click', handleDownload);

urlInput.addEventListener('input', () => {
    urlError.textContent = '';
});

// Funciones
function handleFormatChange(e) {
    if (isProcessing) return;
    
    formatBtns.forEach(btn => btn.classList.remove('active'));
    e.currentTarget.classList.add('active');
    selectedFormat = e.currentTarget.dataset.format;
    
    // Mostrar/ocultar sección de calidad
    if (selectedFormat === 'mp3') {
        qualitySection.style.display = 'none';
    } else {
        qualitySection.style.display = 'block';
    }
}

function handleQualityChange(e) {
    if (isProcessing) return;
    
    qualityBtns.forEach(btn => btn.classList.remove('active'));
    e.currentTarget.classList.add('active');
    selectedQuality = e.currentTarget.dataset.quality;
}

function extractVideoId(url) {
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
        /^([a-zA-Z0-9_-]{11})$/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    return null;
}

function validateUrl(url) {
    if (!url.trim()) {
        return 'Por favor, ingresa una URL de YouTube';
    }
    
    const videoId = extractVideoId(url);
    if (!videoId) {
        return 'URL de YouTube no válida. Ejemplo: https://www.youtube.com/watch?v=VIDEO_ID';
    }
    
    return null;
}

async function handleConvert() {
    if (isProcessing) return;
    
    const url = urlInput.value;
    const error = validateUrl(url);
    
    if (error) {
        urlError.textContent = error;
        return;
    }
    
    // Ocultar mensajes previos
    hideAllMessages();
    
    // Iniciar proceso
    isProcessing = true;
    convertBtn.disabled = true;
    formatBtns.forEach(btn => btn.disabled = true);
    qualityBtns.forEach(btn => btn.disabled = true);
    urlInput.disabled = true;
    
    convertBtn.classList.add('loading');
    convertBtn.querySelector('span').textContent = 'Procesando...';
    
    progressContainer.style.display = 'block';
    
    try {
        // Extraer video ID
        const videoId = extractVideoId(url);
        
        // Llamada al backend Flask
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                video_id: videoId,
                format: selectedFormat,
                quality: selectedQuality
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al convertir el video');
        }
        
        // Obtener el resultado
        const data = await response.json();
        
        // Simular progreso mientras se procesa
        await simulateProgress();
        
        // Mostrar éxito
        downloadUrl = data.download_url;
        const formatText = selectedFormat.toUpperCase();
        const qualityText = selectedFormat !== 'mp3' ? ` - Calidad: ${selectedQuality}` : '';
        
        successText.textContent = `Tu archivo está listo para descargar en formato ${formatText}${qualityText}`;
        successMessage.style.display = 'flex';
        resetBtn.style.display = 'block';
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Error al convertir el video. Por favor, intenta nuevamente.');
    } finally {
        isProcessing = false;
        convertBtn.disabled = false;
        convertBtn.classList.remove('loading');
        convertBtn.querySelector('span').textContent = 'Convertir';
        progressContainer.style.display = 'none';
        formatBtns.forEach(btn => btn.disabled = false);
        qualityBtns.forEach(btn => btn.disabled = false);
        urlInput.disabled = false;
    }
}

async function simulateProgress() {
    return new Promise((resolve) => {
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            progressFill.style.width = `${progress}%`;
            progressPercent.textContent = `${progress}%`;
            
            if (progress >= 100) {
                clearInterval(interval);
                resolve();
            }
        }, 200);
    });
}

function handleDownload() {
    if (downloadUrl) {
        // Descargar el archivo
        window.location.href = downloadUrl;
    }
}

function resetForm() {
    urlInput.value = '';
    urlInput.disabled = false;
    selectedFormat = 'mp3';
    selectedQuality = 'best';
    isProcessing = false;
    downloadUrl = null;
    
    formatBtns.forEach(btn => {
        btn.classList.remove('active');
        btn.disabled = false;
    });
    formatBtns[0].classList.add('active');
    
    qualityBtns.forEach(btn => {
        btn.classList.remove('active');
        btn.disabled = false;
    });
    qualityBtns[qualityBtns.length - 1].classList.add('active');
    
    qualitySection.style.display = 'none';
    hideAllMessages();
    
    resetBtn.style.display = 'none';
    convertBtn.disabled = false;
    convertBtn.classList.remove('loading');
    convertBtn.querySelector('span').textContent = 'Convertir';
    
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';
}

function showError(message) {
    errorText.textContent = message;
    errorAlert.style.display = 'block';
    resetBtn.style.display = 'block';
}

function hideAllMessages() {
    urlError.textContent = '';
    videoInfo.style.display = 'none';
    progressContainer.style.display = 'none';
    successMessage.style.display = 'none';
    errorAlert.style.display = 'none';
}
