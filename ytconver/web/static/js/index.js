$(document).ready(function() {
    // =============== ELEMENTOS ===============
    const $videoUrl = $('#videoUrl');
    const $opcionesDesplegable = $('#opcionesDesplegable');
    const $calidades = $('#calidades');
    const $qualityButtons = $('.quality-btn');
    const $btnConvertir = $('#btnConvertir');
    
    // Nuevos elementos para la sección de información
    const $seccionPrincipal = $('#seccionFormulario');
    const $seccionInfoVideo = $('#seccionInfoVideo');
    const $thumbnail = $('#thumbnail');
    const $tituloYt = $('#titulo-yt');
    const $nombreCanal = $('#nombre-canal');
    const $duracionViews = $('#duracion-views');
    const $btnDescargarDirecto = $('#btnDescargarDirecto');
    const $btnConvertirOtro = $('#btnConvertirOtro');
    
    // Variables de estado
    let calidadSeleccionada = null;
    let formatoSeleccionado = 'MP3';
    let urlActual = '';
    let videoInfo = null;
    
    // =============== INICIALIZACIÓN ===============
    $calidades.hide();
    $seccionInfoVideo.hide();
    
    // =============== EVENTOS ===============

    // Cambio de formato
    $opcionesDesplegable.on('change', function() {
        formatoSeleccionado = $(this).val();
        
        if (formatoSeleccionado === 'MP3') {
            console.log("Selecionado MP3");
            $calidades.hide();
            $qualityButtons.removeClass('active');
            calidadSeleccionada = null;
        } else {
            
            console.log("Selecionado MP4");
            $calidades.show();
            $qualityButtons.removeClass('active');
            $qualityButtons.last().addClass('active');
            calidadSeleccionada = 5;
        }
    });
    
    // Botones de calidad
    $qualityButtons.on('click', function() {
        $qualityButtons.removeClass('active');
        $(this).addClass('active');
        calidadSeleccionada = $qualityButtons.index($(this)) + 1;
    });
    
    // =============== BOTÓN PRINCIPAL "CONVERTIR" ===============
    $btnConvertir.on('click', function() {
        // 1. Obtener valores
        const url = $videoUrl.val().trim();
        formatoSeleccionado = $opcionesDesplegable.val();
        
        // 2. Validaciones
        if (!url) {
            mostrarAlerta('Ingresa una URL de YouTube', 'warning');
            return;
        }
        
        if (!esUrlYouTubeValida(url)) {
            mostrarAlerta('Ingresa una URL válida de YouTube', 'warning');
            return;
        }
        
        if (formatoSeleccionado === 'MP4' && !calidadSeleccionada) {
            mostrarAlerta('Selecciona una calidad para MP4', 'warning');
            return;
        }
        
        // 3. Guardar URL actual
        urlActual = url;
        
        // 4. Cambiar estado del botón
        const $btn = $(this);
        const originalText = $btn.html();
        $btn.html('<span class="spinner-border spinner-border-sm" role="status"></span> Obteniendo información...');
        $btn.prop('disabled', true);
        
        // 5. Obtener información del video
        obtenerInfoVideo(url)
            .then(function(info) {
                videoInfo = info;
                
                // 6. Mostrar información del video
                mostrarInformacionVideo(info);
                
                // 7. Cambiar a sección de información
                $seccionPrincipal.hide();
                $seccionInfoVideo.show().addClass('seccion-activa');
                
                // 8. Preparar botón de descarga directa
                prepararDescargaDirecta(url, formatoSeleccionado, calidadSeleccionada);
            })
            .catch(function(error) {
                console.error('Error:', error);
                mostrarAlerta('Error al obtener información del video: ' + error.message, 'danger');
            })
            .finally(function() {
                $btn.html(originalText);
                $btn.prop('disabled', false);
            });
    });
    
    // =============== BOTÓN "DESCARGAR AHORA" ===============
    $btnDescargarDirecto.on('click', function() {
        if (!urlActual) {
            mostrarAlerta('No hay URL disponible', 'warning');
            return;
        }
        
        // Obtener calidad si es MP4
        let calidad = null;
        if (formatoSeleccionado === 'MP4') {
            const $botonActivo = $('.quality-btn.active');
            if ($botonActivo.length === 0) {
                mostrarAlerta('Selecciona una calidad', 'warning');
                return;
            }
            calidad = $qualityButtons.index($botonActivo) + 1;
        }
        
        // Iniciar descarga
        iniciarDescarga(urlActual, formatoSeleccionado, calidad);
    });
    
    // =============== BOTÓN "CONVERTIR OTRO VIDEO" ===============
    $btnConvertirOtro.on('click', function() {
        // Resetear formulario
        $videoUrl.val('');
        $opcionesDesplegable.val('MP3').trigger('change');
        
        // Mostrar sección principal
        $seccionInfoVideo.hide().removeClass('seccion-activa');
        $seccionPrincipal.show();
        
        // Enfocar en el input
        $videoUrl.focus();
    });
    
    // =============== FUNCIONES ===============
    
    // Validar URL de YouTube
    function esUrlYouTubeValida(url) {
        const patrones = [
            /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]{11}/,
            /^(https?:\/\/)?youtu\.be\/[\w-]{11}/,
            /^(https?:\/\/)?(www\.)?youtube\.com\/embed\/[\w-]{11}/,
            /^(https?:\/\/)?(www\.)?youtube\.com\/v\/[\w-]{11}/
        ];
        return patrones.some(patron => patron.test(url));
    }
    
    // Obtener información del video
    function obtenerInfoVideo(url) {
        return new Promise(function(resolve, reject) {
            const encodedUrl = encodeURIComponent(url);
            const apiUrl = `/request?urlVideo=${encodedUrl}`;
            
            $.ajax({
                url: apiUrl,
                method: 'GET',
                success: function(data) {
                    if (data.success) {
                        resolve(data);
                    } else {
                        reject(new Error('No se pudo obtener información del video'));
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    reject(new Error('Error de conexión: ' + textStatus));
                }
            });
        });
    }
    
    // Mostrar información del video
    function mostrarInformacionVideo(info) {
        // Imagen
        $thumbnail.attr('src', info.thumbnail);
        $thumbnail.attr('alt', info.titulo || 'Miniatura del video');
        
        // Título
        $tituloYt.text(info.titulo || 'Título no disponible');
        
        // Canal
        $nombreCanal.text(info.canal || 'Canal no disponible');
        
        // Duración y vistas
        const duracion = formatearDuracion(info.duracion || 0);
        const vistas = formatearVistas(info.views || 0);
        $duracionViews.text(`Duración: ${duracion} • Visualizaciones: ${vistas}`);
        
        // Actualizar botón de descarga
        const extension = formatoSeleccionado.toLowerCase();
        $btnDescargarDirecto.html(`<i class="bi bi-download me-2"></i>Descargar ${extension.toUpperCase()}`);
    }
    
    // Preparar descarga directa
    function prepararDescargaDirecta(url, formato, calidad) {
        // Actualizar evento del botón de descarga
        $btnDescargarDirecto.off('click').on('click', function() {
            iniciarDescarga(url, formato, calidad);
        });
    }



    async function iniciarDescarga(url, formato, calidad) {
    const encodedUrl = encodeURIComponent(url);
    let downloadUrl;

    if (formato === 'MP3') {
        downloadUrl = `/conversion/mp3?url=${encodedUrl}`;
    } else {
        downloadUrl = `/conversion/mp4?url=${encodedUrl}&calidad=${calidad}`;
    }

    const $btn = $btnDescargarDirecto;
    const originalText = $btn.html();

    $btn.html('<span class="spinner-border spinner-border-sm"></span> Descargando...');
    $btn.prop('disabled', true);

    try {
        const response = await fetch(downloadUrl, { method: 'GET' });

        if (!response.ok) {
            throw new Error('La calidad seleccionada no está disponible');

            $seccionInfoVideo.hide();
            $seccionPrincipal.show();            
        }

        // 👉 Si existe, ahora sí descargar
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        mostrarAlerta(
                        'Descarga iniciada.<br><small>Por favor espera un momento…</small>',
                        'success'
                    );


    } catch (error) {
        mostrarAlerta(error.message, 'danger');
        // 🔙 Volver a la sección anterior SIN borrar la URL
        $seccionInfoVideo.hide();
        $seccionPrincipal.show();
    } finally {
        $btn.html(originalText);
        $btn.prop('disabled', false);
    }
}



    
  function mostrarAlerta(mensaje, tipo = 'danger', tiempo = 4000) {
    // Eliminar alertas previas
    $('.alert-temp').remove();

    const alertHtml = `
        <div class="alert alert-dark alert-dismissible fade show alert-temp
                    position-fixed top-0 end-0 m-3"
            style="z-index: 9999; min-width: 300px;">
            ${mensaje}
            <button type="button" class="btn-close"></button>
        </div>
    `;

    const $alerta = $(alertHtml);
    $('body').append($alerta);

    // Botón cerrar manual
    $alerta.find('.btn-close').on('click', function () {
        $alerta.fadeOut(300, () => $alerta.remove());
    });

    // Auto cerrar
    setTimeout(() => {
        $alerta.fadeOut(400, () => $alerta.remove());
    }, tiempo);
}

    
    // Formatear duración (segundos a MM:SS)
    function formatearDuracion(segundos) {
        if (!segundos) return '--:--';
        
        const minutos = Math.floor(segundos / 60);
        const segs = segundos % 60;
        return `${minutos}:${segs.toString().padStart(2, '0')}`;
    }
    
    // Formatear vistas
    function formatearVistas(vistas) {
        if (!vistas) return '--';
        
        if (vistas >= 1000000) {
            return (vistas / 1000000).toFixed(1) + 'M';
        } else if (vistas >= 1000) {
            return (vistas / 1000).toFixed(1) + 'K';
        }
        return vistas.toString();
    }
    
    // Inicializar calidad máxima para MP4
    if (formatoSeleccionado === 'MP4') {
        $qualityButtons.last().addClass('active');
        calidadSeleccionada = 5;
    }
});