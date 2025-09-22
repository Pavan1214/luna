from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, ChatMessage
from livekit.plugins import google, noise_cancellation

# Import your custom modules
from Jarvis_prompts import instructions_prompt, Reply_prompts
from memory_loop import MemoryExtractor
from jarvis_reasoning import thinking_capability
from voice_monitor import voice_monitor
import asyncio

load_dotenv()

class Assistant(Agent):
    def __init__(self, chat_ctx) -> None:
        super().__init__(
            chat_ctx=chat_ctx,
            instructions=instructions_prompt,
            llm=google.beta.realtime.RealtimeModel(voice="Charon"),
            tools=[thinking_capability]
        )

async def entrypoint(ctx: agents.JobContext):
    # Start voice monitoring
    monitor_task = asyncio.create_task(voice_monitor.start_monitoring())
    
    session = AgentSession(
        preemptive_generation=True
    )
    
    # Getting the current memory chat
    current_ctx = session.history.items
    
    await session.start(
        room=ctx.room,
        agent=Assistant(chat_ctx=current_ctx),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    
    await session.generate_reply(
        instructions=Reply_prompts
    )
    
    conv_ctx = MemoryExtractor()
    await conv_ctx.run(current_ctx)
    
    # Clean up monitoring when done
    voice_monitor.stop_monitoring()
    await monitor_task

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))