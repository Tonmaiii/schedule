import asyncio
import json
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from data import ScheduleData
from display_schedule import SaveSchedule
from schedule import Schedule
from utils import create_file

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to restrict allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_data: Dict[str, ScheduleData] = {}  # Stores JSON input
data_queues: Dict[str, asyncio.Queue[Any]] = {}  # Stores message queues
session_schedules: Dict[str, Schedule] = {}  # Stores schedules


async def event_stream(session_id: str):
    """SSE event stream for a given session ID."""
    queue = data_queues.get(session_id)
    if queue is None:
        yield "event: error\ndata: Session not found\n\n"
        return

    while True:
        result = await queue.get()
        if result is None:
            yield "event: cancel\n\n"
            print("Scheduling process cancelled.")
            break

        obj = json.loads(result)
        data = ScheduleData(obj["input"])
        variables = obj["output"]

        saver = SaveSchedule(data, variables)
        csv_string = saver.schedule_csv()
        yield f"data: {json.dumps(csv_string)}\n\n"


def data_callback(session_id: str, data: Any):
    """Callback function to send data to the client's SSE connection."""

    async def put_data():
        if session_id in data_queues:
            await data_queues[session_id].put(data)

    asyncio.create_task(put_data())


async def test_async_function(session_id: str):
    """Simulate an async function that streams results over time."""
    for i in range(5):
        await asyncio.sleep(1)  # Simulate delay
        data = {"message": f"Message {i+1} from async function", "index": i + 1}
        data_callback(session_id, data)  # Pass data to the callback


@app.post("/upload-data")
async def upload_data(request: Request):
    """Receives large JSON input via POST and stores it with a session ID."""
    data = await request.json()

    # Generate a unique session ID
    session_id = str(uuid.uuid4())

    with create_file(f"sessions/{session_id}.json") as f:
        json.dump(data, f)

    schedule_data = ScheduleData(data)

    # Store the data in memory
    session_data[session_id] = schedule_data
    data_queues[session_id] = asyncio.Queue()

    return {"session_id": session_id}


@app.get("/solve/{session_id}")
async def solve(session_id: str):
    """Starts the scheduling process for a given session and streams updates."""
    if session_id not in session_data:
        raise HTTPException(status_code=404, detail="Session ID not found")

    # Fetch stored data
    data = session_data[session_id]
    schedule = Schedule(data)
    session_schedules[session_id] = schedule

    # Run the scheduling function asynchronously
    asyncio.create_task(
        # test_async_function(session_id)
        schedule.solve_async(lambda data: data_callback(session_id, data))
    )

    del session_data[session_id]

    # Return SSE response
    return StreamingResponse(event_stream(session_id), media_type="text/event-stream")


@app.get("/cancel/{session_id}")
async def cancel(session_id: str):
    """Cancels the scheduling process for a given session."""
    if session_id not in session_schedules:
        raise HTTPException(status_code=404, detail="Session ID not found")

    # Cancel the scheduling process
    await session_schedules[session_id].cancel()
    if session_id in data_queues:
        await data_queues[session_id].put(None)

    # Remove the schedule from memory
    del session_schedules[session_id]
    # Remove the data from memory
    del session_data[session_id]

    return {"message": "Scheduling process cancelled"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
