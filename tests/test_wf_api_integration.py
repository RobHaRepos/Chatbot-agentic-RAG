import os
import time
import pytest
from fastapi.testclient import TestClient
from app.langgraph_code.wf_api import app

@pytest.mark.integration
def test_wf_api_run_workflow_happy():
    with TestClient(app) as client:
        # Wait for readiness
        timeout = int(os.environ.get("INTEGRATION_TIMEOUT", "120"))
        start_time = time.time()
        while True:
            r = client.get("/ready")
            if r.status_code == 200 and r.json().get("status") is True:
                break
            if time.time() - start_time > timeout:
                pytest.fail("WF API did not become ready in time")
            time.sleep(2)
        
        # Health check
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
        
        # Now run the workflow
        payload = {"question": "What is the newest iPhone?", "k": 5}
        r = client.post("/run", json=payload)
        assert r.status_code == 200
        result = r.json()
        assert "result" in result
        assert isinstance(result["result"], dict) 
        assert "iPhone 15 Pro Max".lower() in result["result"].get("answer").lower()