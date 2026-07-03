import streamlit as st
from pydub import AudioSegment
import io
import zipfile

def parse_time_to_seconds(time_str: str) -> float:
    time_str = time_str.strip()
    if ":" in time_str:
        parts = time_str.split(":")
        if len(parts) == 2:  # MM:SS
            minutes = float(parts[0])
            seconds = float(parts[1])
            return (minutes * 60) + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return (hours * 3600) + (minutes * 60) + seconds
        else:
            raise ValueError("Formato de tiempo no reconocido.")
    else:
        return float(time_str)

st.set_page_config(page_title="Cortador de Audio por Lotes", page_icon="✂️")

st.title("✂️ Cortador de Audio por Lotes")
st.write("Sube tu archivo de audio (.m4a, .mp3, .wav) e introduce las instrucciones de corte.")

st.info("💡 **Formatos admitidos de tiempo:** Segundos (ej. `125`) o Minutos:Segundos (ej. `2:05`).")

# El selector de archivos acepta m4a de forma nativa
uploaded_file = st.file_uploader(
    "1. Selecciona el archivo de audio", 
    type=["m4a", "mp3", "wav", "ogg"]
)

ejemplo_instrucciones = (
    "nombre_corte_1, 1:10, 2:05\n"
    "nombre_corte_2, 70, 125"
)
instrucciones = st.text_area(
    "2. Introduce las instrucciones de corte (Nombre, Inicio, Fin):",
    value=ejemplo_instrucciones,
    height=150
)

if uploaded_file and instrucciones:
    if st.button("Procesar y Cortar Audio", type="primary"):
        try:
            # Detecta si es m4a, mp3 o wav
            formato_audio = uploaded_file.name.split(".")[-1].lower()
            
            st.info("Procesando archivo de audio... Esto puede tomar un momento según el tamaño del archivo.")
            audio = AudioSegment.from_file(io.BytesIO(uploaded_file.read()), format=formato_audio)
            
            lineas = [linea.strip() for linea in instrucciones.strip().split("\n") if linea.strip()]
            zip_buffer = io.BytesIO()
            error_en_lineas = False
            
            with zipfile.ZipFile(zip_buffer, "w") as archivo_zip:
                for idx, linea in enumerate(lineas):
                    partes = linea.split(",")
                    if len(partes) == 3:
                        try:
                            nombre = partes[0].strip()
                            segundo_inicio = parse_time_to_seconds(partes[1])
                            segundo_fin = parse_time_to_seconds(partes[2])
                            
                            inicio_ms = int(segundo_inicio * 1000)
                            fin_ms = int(segundo_fin * 1000)
                            
                            if inicio_ms >= fin_ms:
                                st.warning(f"Línea {idx + 1}: El tiempo de inicio no puede ser mayor o igual al de fin.")
                                error_en_lineas = True
                                continue
                            
                            corte = audio[inicio_ms:fin_ms]
                            
                            buffer_corte = io.BytesIO()
                            # Exporta el corte manteniendo el mismo formato de entrada (ej. m4a)
                            corte.export(buffer_corte, format=formato_audio)
                            buffer_corte.seek(0)
                            
                            nombre_archivo = f"{nombre}.{formato_audio}"
                            archivo_zip.writestr(nombre_archivo, buffer_corte.read())
                            
                        except ValueError as e:
                            st.warning(f"Error en línea {idx + 1} ('{linea}'): Formato no válido.")
                            error_en_lineas = True
                    else:
                        st.warning(f"Línea {idx + 1} ignorada: Formato incorrecto.")
                        error_en_lineas = True
            
            zip_buffer.seek(0)
            
            if len(zip_buffer.getvalue()) > 22:
                st.success("¡Cortes generados exitosamente!")
                st.download_button(
                    label=f"⬇️ Descargar todos los cortes ({formato_audio.upper()}) (ZIP)",
                    data=zip_buffer,
                    file_name="cortes_audio.zip",
                    mime="application/zip"
                )
            else:
                st.error("No se pudo procesar ningún fragmento válido.")
                
        except Exception as e:
            st.error(f"Error de procesamiento: {e}")