# Audio Analyzer

Aplicación de escritorio en **Python + CustomTkinter** para analizar colecciones de audio y exportar métricas técnicas en formato tabular.

## ¿Qué hace?

Este proyecto permite escanear carpetas con archivos de audio y obtener, por archivo, datos como:

- **LUFS integrado** (loudness).
- **True Peak** en dB.
- **Sample Rate**.
- **Canales** (Mono/Stereo o número de canales).
- **Bit depth / subtipo** del archivo.
- **Ruta del archivo** (opcional).

Formatos soportados en el análisis:

- `.wav`
- `.flac`
- `.mp3`

## Tecnologías y dependencias

- **Interfaz gráfica:** `customtkinter`
- **Lectura de audio:** `soundfile`
- **Loudness:** `pyloudnorm`
- **Análisis externo:** `ffmpeg` / `ffprobe`
- **Tablas y exportación:** `prettytable`, `pandas`, `openpyxl`

Dependencias Python declaradas en `requirements.txt` con versiones mínimas flexibles para evitar pins innecesarios.

---

## Requisitos previos

1. **Python 3.10+** recomendado.
2. **FFmpeg y FFprobe** instalados y disponibles en el `PATH`.
3. Sistema operativo con soporte para interfaz de escritorio.

> Nota: FFmpeg/FFprobe se instalan por fuera del proyecto; la app solo verifica que estén disponibles en el `PATH`.

## Instalación rápida

### Opción A — instalación manual

```bash
pip install -r requirements.txt
```

### Opción B — instalador incluido

El proyecto incluye `lib_installer.py`, que:

- verifica/activa `pip`,
- recorre directorios para detectar `requirements.txt`,
- instala paquetes faltantes respetando los rangos flexibles declarados.

## Uso

Ejecuta la app:

```bash
python main.py
```

Flujo general de trabajo:

1. Seleccionar carpeta raíz con audios.
2. Elegir formatos a incluir (`wav`, `flac`, `mp3`).
3. Marcar métricas a analizar (LUFS, Peak, etc.).
4. Lanzar análisis.
5. Revisar resultados y exportar si aplica.

## Estructura del proyecto

```text
Audio_analyzer/
├── main.py            # App principal + UI + funciones de análisis
├── lib_installer.py   # Instalación/verificación de dependencias
├── requirements.txt   # Dependencias Python del proyecto
└── README.md
```

## Consideraciones técnicas

- El cálculo de LUFS se realiza con `pyloudnorm` y adapta el bloque para audios muy cortos.
- El True Peak se extrae mediante `ffmpeg` (`volumedetect`).
- El conteo de canales se obtiene con `ffprobe`.
- Existe una versión de análisis concurrente con `ThreadPoolExecutor` para acelerar el procesamiento por lotes.

## Problemas comunes

### 1) `ffmpeg` no encontrado

Asegúrate de tener FFmpeg instalado y que `ffmpeg`/`ffprobe` funcionen desde terminal.

### 2) Errores de lectura de archivos

Revisa permisos, integridad del archivo y codecs soportados por tu instalación de FFmpeg/libsndfile.

### 3) Conflictos de versiones Python

Si trabajas en desarrollo, usa un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Roadmap sugerido

- Añadir tests automatizados para funciones de análisis.
- Mejorar cobertura de tests automatizados para exportación y análisis por lotes.
- Implementar exportación configurable (CSV/XLSX con plantillas).
- Agregar validación visual de errores por archivo en la UI.

## Licencia

Actualmente el repositorio no declara licencia explícita.
Si vas a distribuir o reutilizar el código, añade un archivo `LICENSE`.
