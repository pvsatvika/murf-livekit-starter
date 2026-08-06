import logging
import os
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
)
from livekit.plugins import deepgram, murf,silero

logger = logging.getLogger("asha-agent")
load_dotenv(".env.local")

SYSTEM_PROMPT = """You are 'AshaAssist', a hands-free voice assistant for ASHA workers during patient field visits.

Your primary duty is to help ASHA workers conduct quick patient intake and triage.
Follow this 4-step workflow:
1. Patient Name and Age
2. Presenting Symptoms
3. Basic Vitals (Temperature, Blood Pressure, Pulse)
4. Protocol check & guidance

Behavior Rules:
- Keep all spoken responses extremely brief, clear, and professional (1 to 2 sentences maximum).
- Do not use markdown headers, bold text, bullet points, emojis, or special symbols in responses."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


server = AgentServer()


def prewarm(proc):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm="openai/gpt-4o-mini",
        tts=murf.TTS(voice="en-IN-anisha", style="Conversational", api_key=os.getenv("MURF_API_KEY")),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    await session.generate_reply(
        instructions="Greet the ASHA worker briefly in 1 sentence and ask for the patient's name and age to begin intake."
    )


if __name__ == "__main__":
    cli.run_app(server)