from fastapi import APIRouter
from app.worker.tasks import resolve_workspace_task

router = APIRouter(prefix="/workspaces", tags=["Resolution"])

@router.post("/{workspace_id}/resolve", status_code=202)
async def trigger_resolution(workspace_id: int):
    """
    Manually triggers Entity Resolution and Temporal Normalization for a workspace.
    """
    task = resolve_workspace_task.delay(workspace_id)
    return {"message": "Resolution triggered", "task_id": task.id}
