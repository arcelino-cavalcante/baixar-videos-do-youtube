import streamlit as st
from pytube import YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable
import os
import yt_dlp
import shutil

def ffmpeg_installed():
    """Verifica se o FFmpeg está instalado no sistema."""
    return shutil.which("ffmpeg") is not None

def get_video_details(url):
    """
    Tenta obter os detalhes do vídeo usando pytube.
    Caso haja erro, utiliza yt_dlp como fallback.
    """
    try:
        yt = YouTube(url)
        details = {
            'title': yt.title,
            'author': yt.author,
            'views': yt.views,
            'length': yt.length,
            'thumbnail_url': yt.thumbnail_url,
        }
        return details
    except Exception as e:
        st.warning("Não foi possível obter todos os detalhes com pytube. Tentando com yt_dlp...")
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            details = {
                'title': info.get('title', 'Título indisponível'),
                'author': info.get('uploader', 'Autor indisponível'),
                'views': info.get('view_count', 'Indisponível'),
                'length': info.get('duration', 'Indisponível'),
                'thumbnail_url': info.get('thumbnail', None),
            }
            return details
        except Exception as e2:
            st.error("Erro ao carregar os detalhes do vídeo.")
            st.error(e2)
            return None

def download_video(url, stream_option="video", path="downloads"):
    """
    Realiza o download do vídeo utilizando yt_dlp para evitar erros 403.
    stream_option pode ser:
      - "video": vídeo com áudio (melhor qualidade progressiva sem precisar de FFmpeg)
      - "audio": apenas áudio (convertido para mp3, necessita de FFmpeg)
      - "video_only": apenas o vídeo sem áudio
    """
    ydl_opts = {}
    
    if stream_option == "video":
        # Tenta usar uma stream progressiva (já com áudio e vídeo) para evitar merge com FFmpeg
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif stream_option == "audio":
        # Para converter para mp3, é necessário que o FFmpeg esteja instalado
        if not ffmpeg_installed():
            st.error("FFmpeg não está instalado. Instale-o para converter áudio para mp3 ou escolha outra opção.")
            raise Exception("FFmpeg não instalado")
        ydl_opts['format'] = 'bestaudio'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif stream_option == "video_only":
        ydl_opts['format'] = 'bestvideo[ext=mp4]'
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'
    
    # Define o template do nome do arquivo
    ydl_opts['outtmpl'] = os.path.join(path, '%(title)s.%(ext)s')
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    
    filename = ydl.prepare_filename(info)
    return filename

def main():
    st.title("Baixar Vídeos do YouTube")
    st.write("Insira o link do vídeo do YouTube para visualizar os detalhes e fazer o download.")
    
    video_url = st.text_input("URL do Vídeo:")
    
    stream_option = st.selectbox(
        "Selecione o tipo de download:",
        ["Vídeo (áudio e vídeo)", "Som (áudio apenas)", "Vídeo sem áudio"]
    )
    
    # Mapeamento das opções para facilitar o tratamento
    stream_mapping = {
        "Vídeo (áudio e vídeo)": "video",
        "Som (áudio apenas)": "audio",
        "Vídeo sem áudio": "video_only"
    }
    
    if video_url:
        details = get_video_details(video_url)
        if details:
            st.subheader("Detalhes do Vídeo")
            if details.get('thumbnail_url'):
                st.image(details.get('thumbnail_url'), width=300)
            st.write("**Título:**", details.get('title'))
            st.write("**Autor:**", details.get('author'))
            st.write("**Visualizações:**", details.get('views'))
            st.write("**Duração:**", details.get('length'), "segundos")
        
        if st.button("Baixar"):
            try:
                with st.spinner("Baixando o vídeo..."):
                    filename = download_video(video_url, stream_option=stream_mapping[stream_option])
                st.success("Download concluído!")
                
                mime_type = "audio/mp3" if stream_mapping[stream_option] == "audio" else "video/mp4"
                with open(filename, "rb") as file:
                    st.download_button(
                        label="Clique para baixar o arquivo",
                        data=file,
                        file_name=os.path.basename(filename),
                        mime=mime_type
                    )
            except RegexMatchError:
                st.error("Link inválido. Por favor, insira uma URL válida do YouTube.")
            except VideoUnavailable:
                st.error("O vídeo não está disponível. Tente outro link.")
            except Exception as e:
                st.error("Ocorreu um erro ao tentar baixar o vídeo. Verifique o link e tente novamente.")
                st.error(e)
                st.info("Caso o erro persista, verifique sua conexão ou tente atualizar as bibliotecas.")

if __name__ == "__main__":
    main()
