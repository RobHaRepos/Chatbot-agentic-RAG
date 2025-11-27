import os
import pytest
from fastapi.testclient import TestClient
from app.langgraph_code.wf_api import app
from tests.test_retriever import _service_up

@pytest.mark.skipif(not _service_up(url=os.environ.get("RETRIEVER_SERVICE_URL", "http://localhost:8001")), reason="Retriever service is not running")
@pytest.mark.integration
def test_wf_api_run_workflow_happy():
    """Integration test: run workflow end-to-end when services are available."""
    with TestClient(app) as client:
        while True:
            r = client.get("/ready")
            if r.status_code == 200 and r.json().get("status") is True:
                break
        
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
        
        payload = {"question": "What is the newest iPhone?", "k": 5}
        r = client.post("/run", json=payload)
        assert r.status_code == 200
        result = r.json()
        assert "result" in result
        assert isinstance(result["result"], dict) 
        assert "iphone" in result["result"].get("answer", "").lower()

@pytest.mark.skipif(not _service_up(url=os.environ.get("RETRIEVER_SERVICE_URL", "http://localhost:8001")), reason="Retriever service is not running")
@pytest.mark.integration
def test_wf_api_run_workflow_multiple_retrieves():
    """Integration: multiple retrievals and answer contains expected keywords."""
    with TestClient(app) as client:
        while True:
            r = client.get("/ready")
            if r.status_code == 200 and r.json().get("status") is True:
                break
    
        payload = {"question": "What is the newest iphone, what display does it have, what camera does it have?", "k": 5}
        r = client.post("/run", json=payload)
        assert r.status_code == 200
        result = r.json()
        assert "result" in result
        assert isinstance(result["result"], dict) 
        assert "display" in result["result"].get("answer", "").lower()  
        assert "camera" in result["result"].get("answer", "").lower()
    

@pytest.mark.skipif(not _service_up(url=os.environ.get("RETRIEVER_SERVICE_URL", "http://localhost:8001")), reason="Retriever service is not running")
@pytest.mark.integration
def test_run_workflow_no_question():
    """Integration: empty question returns clarify action with a suggestion message."""
    with TestClient(app) as client:
        while True:
            r = client.get("/ready")
            if r.status_code == 200 and r.json().get("status") is True:
                break
    
        payload = {"question": "", "k": 5}
        r = client.post("/run", json=payload)
        assert r.status_code == 200
        result = r.json()
        assert "result" in result
        assert "The query seems to be unrelated to phones. Could you be more specific? Which phone model or what detail do you mean (brand/model/specs/price)?" in result["result"].get("answer", "")
        
        