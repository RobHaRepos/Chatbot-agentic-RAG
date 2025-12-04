import io
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
import soundfile
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.langgraph_code.src import tts_api
from tests.retriever.test_retriever import _service_up

SAMPLE_RATE_TTS = int(os.getenv("SAMPLE_RATE_TTS", "24000"))
TEST_TTS_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:8005")

tts_api.TTS_SERVICE_URL = TEST_TTS_URL

app_test = FastAPI()
app_test.include_router(tts_api.router)

@pytest.mark.integration
@pytest.mark.skipif(not _service_up(url=TEST_TTS_URL), reason="TTS service is not running")
def test_synthesize_speech_integration():
    """Integration test: synthesize speech end-to-end."""
    client = TestClient(app_test)

    response = client.post("/tts", json={"text": "This is an integration test."})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    
    wav_bytes = io.BytesIO(response.content)
    data, samplerate = soundfile.read(wav_bytes)
    assert samplerate == SAMPLE_RATE_TTS
    assert data.size > 0
    
@pytest.mark.integration
@pytest.mark.skipif(not _service_up(url=TEST_TTS_URL), reason="TTS service is not running")
def test_save_local_audio_file():
    """Test saving synthesized audio to a local file."""
    test_directory = Path(__file__).parent.parent / "out"
    test_directory.mkdir(exist_ok=True)
    output_dir = test_directory / "test_output.wav"
    
    payload = {
        "text": "Saving this audio file locally.",
        "voice": "am_onyx",
        "speed": 1.0,
    }
    
    client = TestClient(app_test)

    response = client.post("/tts", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0
    
    with open(output_dir, "wb") as f:
        f.write(response.content)
        
    assert os.path.exists(output_dir)
    
    try:
        os.startfile(str(output_dir))
        print(f"Playing audio file: {output_dir}")
    except Exception as e:
        print(f"Could not play audio file automatically: {e}")
        print(f"Please open the file manually at: {output_dir}")

def test_tts_error_handling_http_error():
    """Unit test: Test error handling when TTS service returns HTTP error."""
    client = TestClient(app_test)
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    async def mock_post(*args, **kwargs):
        raise httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
    
    with patch("httpx.AsyncClient.post", new=mock_post):
        response = client.post("/tts", json={"text": "Test error handling"})
        
        assert response.status_code == 200
        assert "error" in response.json()
        assert "500" in response.json()["error"]