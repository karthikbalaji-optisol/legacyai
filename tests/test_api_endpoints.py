import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db.database import init_db
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Live probe
        res_live = await client.get("/health/live")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "alive"

        # 2. Ready probe
        res_ready = await client.get("/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"

        # 3. Prometheus metrics
        res_metrics = await client.get("/metrics")
        assert res_metrics.status_code == 200
        assert "legacylens" in res_metrics.text

@pytest.mark.asyncio
async def test_full_api_workflow_journey():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Repository via sample
        res_repo = await client.post("/api/v1/repositories", data={"use_sample": "true"})
        assert res_repo.status_code == 201
        repo_data = res_repo.json()
        repo_id = repo_data["repository_id"]
        assert repo_id is not None

        # 2. Start Analysis
        res_analysis = await client.post(f"/api/v1/analyses/repositories/{repo_id}/analyze")
        assert res_analysis.status_code == 202
        analysis_id = res_analysis.json()["analysis_id"]

        # 3. Poll Analysis status until complete
        completed = False
        for _ in range(40):
            await asyncio.sleep(0.5)
            res_status = await client.get(f"/api/v1/analyses/{analysis_id}")
            assert res_status.status_code == 200
            st_data = res_status.json()
            if st_data["status"] in ["completed", "awaiting_review"]:
                completed = True
                assert st_data["validation_score"] is not None
                break

        assert completed is True

        # 4. Fetch Evidence
        res_ev = await client.get(f"/api/v1/analyses/{analysis_id}/evidence")
        assert res_ev.status_code == 200
        evidence_list = res_ev.json()
        assert len(evidence_list) > 0

        # 5. Fetch BRD
        res_brd = await client.get(f"/api/v1/analyses/{analysis_id}/brd")
        assert res_brd.status_code == 200
        brd_data = res_brd.json()
        assert len(brd_data["functional_requirements"]) > 0

        # 6. Fetch Impact Graph
        res_graph = await client.get(f"/api/v1/analyses/{analysis_id}/impact-graph")
        assert res_graph.status_code == 200
        graph_data = res_graph.json()
        assert len(graph_data["nodes"]) > 0
        assert len(graph_data["edges"]) > 0

        # 7. Update Requirement review status
        first_req_id = brd_data["functional_requirements"][0]["id"]
        res_patch = await client.patch(
            f"/api/v1/analyses/{analysis_id}/requirements/{first_req_id}",
            json={"review_status": "APPROVED", "reviewer_notes": "Verified by Lead BA"}
        )
        assert res_patch.status_code == 200
        updated_brd = res_patch.json()
        assert any(r["id"] == first_req_id and r["review_status"] == "APPROVED" for r in updated_brd["functional_requirements"])

        # 8. Export BRD to DOCX
        res_export = await client.post(f"/api/v1/analyses/{analysis_id}/export")
        assert res_export.status_code == 200
        export_data = res_export.json()
        assert "download_url" in export_data

        # 9. Download DOCX
        download_url = export_data["download_url"]
        res_dl = await client.get(download_url)
        assert res_dl.status_code == 200
        assert len(res_dl.content) > 1000

        # 10. Verify SSE Streaming Endpoint returns historical events
        res_stream = await client.get(f"/api/v1/analyses/{analysis_id}/events")
        assert res_stream.status_code == 200
        assert "text/event-stream" in res_stream.headers.get("content-type", "")
        assert "data: " in res_stream.text
