import streamlit as st
from pydub import AudioSegment
import io
import zipfile

# Función para convertir diferentes formatos de tiempo a segundos (float)
def parse_time_to_seconds(time_str: str) -> float:
    time_str = time_str.strip()
    
    # Si contiene dos puntos, es formato de tiempo (MM:SS o HH:MM:SS)
    if ":" in time_str:
        parts = time_str.split(":")
        if len(parts) == 2:  # Formato MM:SS
            minutes = float(parts[0])
            seconds = float(parts[1])
            return (minutes * 60) + seconds
        elif len(parts) == 3:  # Formato HH:MM:SS
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return (hours * 3600) + (minutes * 60) + seconds
        else:
            raise ValueError("Formato de tiempo no reconocido (demasiados segmentos).")
    else:
        # Si no tiene dos puntos, se asume que ya son segundos directos
        return float(time_str)

st.set_page_config(page_title="Cortador de Audio por Lotes", page_icon="✂️")

st.title("✂️ Cortador de Audio por Lotes")
st.write("Sube tu archivo de audio e indica los intervalos de corte.")
st.info("Nota: Puedes ingresar el tiempo en segundos (ej. `125`) o en minutos:segundos (ej. `2:05`).")

# 1. Subir el archivo de audio
uploaded_file = st.file_uploader("Seleccione el archivo de audio", type=["mp3", "wav", "m4a", "ogg"])

# 2. Entrada de texto para las instrucciones de corte
ejemplo_instrucciones = (
    "nombre_corte_1, 1:10, 2:05\n"
    "nombre_corte_2, 70, 125\n"
    "nombre_corte_3, 02:30, 03:15"
)
instrucciones = st.text_area(
    "Introduzca las instrucciones de corte (Nombre, Inicio, Fin):",
    value=ejemplo_instrucciones,
    height=150
)

if uploaded_file and instrucciones:
    if st.button("Procesar y Cortar Audio", type="primary"):
        try:
            formato_audio = uploaded_file.name.split(".")[-1].lower()
            
            st.info("Cargando archivo de audio... Esto puede tomar un momento según el tamaño.")
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
                            
                            # Conversión de tiempo usando la función auxiliar
                            segundo_inicio = parse_time_to_seconds(partes[1])
                            segundo_fin = parse_time_to_seconds(partes[2])
                            
                            # Convertir a milisegundos para pydub
                            inicio_ms = int(segundo_inicio * 1000)
                            fin_ms = int(segundo_fin * 1000)
                            
                            # Validar que los rangos de tiempo sean lógicos
                            if inicio_ms >= fin_ms:
                                st.warning(f"Línea {idx + 1}: El tiempo de inicio no puede ser mayor o igual al de fin ('{linea}').")
                                error_en_lineas = True
                                continue
                            
                            # Realizar el corte
                            corte = audio[inicio_ms:fin_ms]
                            
                            # --- SOLUCIÓN ERROR FFMPEG M4A ---
                            # Si el formato es m4a, indicamos a pydub el formato "ipod" para la codificación correcta
                            formato_exportacion = "ipod" if formato_audio == "m4a" else formato_audio
                            
                            buffer_corte = io.BytesIO()
                            corte.export(buffer_corte, format=formato_exportacion)
                            buffer_corte.seek(0)
                            # ---------------------------------
                            
                            nombre_archivo = f"{nombre}.{formato_audio}"
                            archivo_zip.writestr(nombre_archivo, buffer_corte.read())
                            
                        except ValueError as e:
                            st.warning(f"Error en línea {idx + 1} ('{linea}'): Formato de tiempo no válido. {e}")
                            error_en_lineas = True
                    else:
                        st.warning(f"Línea {idx + 1} ignorada por formato incorrecto: '{linea}'")
                        error_en_lineas = True
            
            zip_buffer.seek(0)
            
            if len(zip_buffer.getvalue()) > 22:
                st.success("¡Procesamiento completado con éxito!")
                st.download_button(
                    label="Descargar todos los cortes (ZIP)",
                    data=zip_buffer,
                    file_name="cortes_audio.zip",
                    mime="application/zip"
                )
            else:
                st.error("No se pudo procesar ningún corte válido.")
                
        except Exception as e:
            st.error(f"Error de procesamiento: {e}")