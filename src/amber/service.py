"""FastAPI service for Amber LangGraph agent"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from amber.config import get_settings
from amber.models import AmberState
from amber.workflows import compile_supervisor_graph

# Optional PostgreSQL checkpointer
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    CHECKPOINTER_AVAILABLE = True
except ImportError:
    PostgresSaver = None
    CHECKPOINTER_AVAILABLE = False

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Global state
supervisor_graph: Any = None
checkpointer: Any = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global supervisor_graph, checkpointer

    settings = get_settings()
    logger.info("Starting Amber LangGraph service", log_level=settings.log_level)

    # Initialize PostgreSQL checkpointer if available
    if CHECKPOINTER_AVAILABLE and PostgresSaver:
        try:
            checkpointer = PostgresSaver.from_conn_string(settings.postgres_url)
            checkpointer.setup()
            logger.info("PostgreSQL checkpointer initialized")
        except Exception as e:
            logger.warning("Failed to initialize checkpointer, running without persistence", error=str(e))
            checkpointer = None
    else:
        logger.info("PostgreSQL checkpointer not available, running without persistence")
        checkpointer = None

    # Compile supervisor graph
    supervisor_graph = compile_supervisor_graph(checkpointer=checkpointer)
    logger.info("Supervisor graph compiled", checkpointing_enabled=checkpointer is not None)

    yield

    logger.info("Shutting down Amber LangGraph service")


# Create FastAPI app
app = FastAPI(
    title="Amber LangGraph Service",
    description="AI agent for codebase intelligence and autonomous maintenance",
    version="0.1.0",
    lifespan=lifespan,
)


# Request/Response models
class AmberRequest(BaseModel):
    """Request model for Amber invocation"""

    mode: str | None = None
    trigger: dict[str, Any]
    session_id: str
    project_name: str
    repositories: list[str]


class AmberResponse(BaseModel):
    """Response model for Amber invocation"""

    session_id: str
    status: str
    message: str
    results: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    checkpointer_enabled: bool


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", version="0.1.0", checkpointer_enabled=checkpointer is not None
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Amber LangGraph",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "invoke": "/invoke",
            "invoke_async": "/invoke-async",
            "webhook": "/webhook/{event_type}",
        },
    }


@app.post("/invoke", response_model=AmberResponse)
async def invoke_amber(request: AmberRequest) -> AmberResponse:
    """Synchronous invocation for on-demand mode"""
    global supervisor_graph

    if supervisor_graph is None:
        raise HTTPException(status_code=503, detail="Supervisor graph not initialized")

    logger.info(
        "Invoking Amber synchronously",
        session_id=request.session_id,
        mode=request.mode,
        project=request.project_name,
    )

    try:
        # Build initial state
        initial_state: AmberState = {
            "mode": request.mode or "on-demand",
            "trigger": request.trigger,
            "session_id": request.session_id,
            "project_name": request.project_name,
            "repositories": request.repositories,
            "messages": [],
            "findings": [],
            "recommendations": [],
            "prs_created": [],
            "comments_posted": [],
            "branches_created": [],
            "human_review_required": False,
            "tests_passed": False,
            "linters_passed": False,
            "followup_needed": False,
            "tool_results": [],
            "token_count": 0,
            "constitution_checks": [],
            "violations_detected": [],
            "errors": [],
            "current_phase": "pending",
            "autonomy_level": 2,
            "confidence": 0.0,
            "rollback_instructions": [],
            "plan": {},
        }

        # Configure with thread_id for checkpointing
        config = {"configurable": {"thread_id": request.session_id}}

        # Execute workflow
        result = await supervisor_graph.ainvoke(initial_state, config=config)

        logger.info(
            "Amber execution completed",
            session_id=request.session_id,
            phase=result.get("current_phase"),
            confidence=result.get("confidence"),
        )

        # Extract the agent's response from messages
        response_content = "Analysis complete"
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                response_content = last_msg.content

        return AmberResponse(
            session_id=request.session_id,
            status="completed",
            message=response_content,
            results={
                "findings": result.get("findings", []),
                "recommendations": result.get("recommendations", []),
                "prs_created": result.get("prs_created", []),
                "human_review_required": result.get("human_review_required", False),
                "confidence": result.get("confidence", 0.0),
            },
        )

    except Exception as e:
        logger.error(
            "Amber execution failed", session_id=request.session_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


async def run_amber_workflow(request: AmberRequest) -> None:
    """Execute Amber workflow in background"""
    global supervisor_graph

    if supervisor_graph is None:
        logger.error("Supervisor graph not initialized for background task")
        return

    logger.info(
        "Starting background Amber workflow",
        session_id=request.session_id,
        mode=request.mode,
    )

    try:
        initial_state: AmberState = {
            "mode": request.mode or "background",
            "trigger": request.trigger,
            "session_id": request.session_id,
            "project_name": request.project_name,
            "repositories": request.repositories,
            "messages": [],
            "findings": [],
            "recommendations": [],
            "prs_created": [],
            "comments_posted": [],
            "branches_created": [],
            "human_review_required": False,
            "tests_passed": False,
            "linters_passed": False,
            "followup_needed": False,
            "tool_results": [],
            "token_count": 0,
            "constitution_checks": [],
            "violations_detected": [],
            "errors": [],
            "current_phase": "pending",
            "autonomy_level": 2,
            "confidence": 0.0,
            "rollback_instructions": [],
            "plan": {},
        }

        config = {"configurable": {"thread_id": request.session_id}}

        result = await supervisor_graph.ainvoke(initial_state, config=config)

        logger.info(
            "Background workflow completed",
            session_id=request.session_id,
            prs_created=len(result.get("prs_created", [])),
            human_review_required=result.get("human_review_required", False),
        )

        # TODO: Send notification if human review required
        if result.get("human_review_required"):
            logger.info("Human review required", session_id=request.session_id)

    except Exception as e:
        logger.error(
            "Background workflow failed",
            session_id=request.session_id,
            error=str(e),
            exc_info=True,
        )


@app.post("/invoke-async")
async def invoke_amber_async(
    request: AmberRequest, background_tasks: BackgroundTasks
) -> JSONResponse:
    """Asynchronous invocation for background/scheduled modes"""
    logger.info(
        "Invoking Amber asynchronously",
        session_id=request.session_id,
        mode=request.mode,
    )

    background_tasks.add_task(run_amber_workflow, request)

    return JSONResponse(
        content={
            "session_id": request.session_id,
            "status": "started",
            "message": "Amber workflow started in background",
        }
    )


@app.post("/webhook/{event_type}")
async def github_webhook(
    event_type: str, payload: dict[str, Any], background_tasks: BackgroundTasks
) -> JSONResponse:
    """GitHub webhook receiver"""
    logger.info("Received GitHub webhook", event_type=event_type)

    # Extract repository info
    repo_name = payload.get("repository", {}).get("full_name", "unknown/unknown")
    repo_url = payload.get("repository", {}).get("clone_url", "")

    # Create session ID from event
    session_id = f"webhook-{event_type}-{payload.get('repository', {}).get('id', 'unknown')}"

    request = AmberRequest(
        mode="webhook",
        trigger={"event_type": f"github.{event_type}", "payload": payload},
        session_id=session_id,
        project_name=repo_name.split("/")[-1],
        repositories=[repo_url] if repo_url else [],
    )

    background_tasks.add_task(run_amber_workflow, request)

    return JSONResponse(
        content={
            "status": "accepted",
            "session_id": session_id,
            "event_type": event_type,
        }
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "amber.service:app",
        host=settings.service_host,
        port=settings.service_port,
        log_level=settings.log_level.lower(),
        reload=False,
    )
