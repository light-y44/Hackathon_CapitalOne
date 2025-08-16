from transformers import pipeline

def load_asr_model(model_id: str = "ARTPARK-IISc/whisper-tiny-vaani-hindi", device: int = 0):
    """
    Loads the Hindi ASR (speech-to-text) model once and returns the pipeline.
    """
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model_id,
        chunk_length_s=30,
        device=device
    )
    # Force Hindi transcription mode
    pipe.model.config.forced_decoder_ids = pipe.tokenizer.get_decoder_prompt_ids(
        language="hi", task="transcribe"
    )
    return pipe

def transcribe_hindi_audio(audio_path: str, asr_pipe) -> str:
    """
    Transcribes Hindi speech from an audio file into Hindi text.
    
    Args:
        audio_path (str): Path to the input audio file (mp3, wav, mp4 etc.)
        asr_pipe: HuggingFace ASR pipeline loaded with load_asr_model().
    
    Returns:
        str: Transcribed Hindi text
    """
    result = asr_pipe(audio_path)
    return result["text"]

# ---------------- Example Usage ---------------- #
# if __name__ == "__main__":
#     # Load the ASR model only once
#     # Transcribe an audio file
#     hindi_text = transcribe_hindi_audio("/content/audio_hindi.mp4", asr_pipe)
#     print("Transcribed Hindi text:", hindi_text)

