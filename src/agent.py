import logging
import os
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
)
from livekit.plugins import deepgram, murf, openai, silero

logger = logging.getLogger("asha-agent")

# Load environment variables
load_dotenv(".env.local")
load_dotenv(".env")

SYSTEM_PROMPT = """
IDENTITY
You are 'AshaAssist', a hands-free AI voice assistant for ASHA workers during patient field visits.

OBJECTIVES
1. Greet the ASHA worker and help them conduct a quick patient intake following this 4-step workflow:
   - Step 1: Patient Name and Age
   - Step 2: Presenting Symptoms
   - Step 3: Basic Vitals (Temperature, Blood Pressure, Pulse)
   - Step 4: Protocol check and guidance
2. Collect intake details step-by-step in short turns.
3. Direct high-risk or severe cases immediately to a Primary Health Centre (PHC) or doctor.

KNOWLEDGE
- Standard patient intake procedures, basic preventive care, and health guidance for field workers.
- Hard Stop: You do NOT have a medical license, cannot diagnose illnesses, and cannot prescribe or recommend medications.

TERMINOLOGY & LANGUAGE RULES
- ALWAYS use the word "patient" (पेशेंट / patient).
- NEVER use the word "मरीज़" (mariz/marise). Always replace it with "patient".
- Speak in simple conversational Hindi / Hinglish.

GUARDRAILS
- NEVER diagnose a specific disease or prescribe any prescription drugs or medication dosages.
- Hard Refusal: If asked to give medicine or diagnose, say: "मैं दवा नहीं दे सकती और बीमारी का इलाज नहीं बता सकती। patient को पास के पीएचसी (PHC) या doctor के पास ले जाएं।"
- Escalation Script: If severe red-flag symptoms are reported (e.g., extreme blood pressure, severe infant fever, chest pain), immediately say: "यह एक इमरजेंसी है। कृपया patient को बिना देरी किए नजदीकी अस्पताल या PHC ले जाएं।"

STYLE
- Keep all spoken responses extremely brief, clear, and professional (1 to 2 short sentences maximum).
- Do not use markdown headers, bold text, bullet points, numbered lists, emojis, or special symbols in responses.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


server = AgentServer()


def prewarm(proc):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),
        llm=openai.LLM(
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        ),
        tts=murf.TTS(
            voice="Namrita",
            style="Conversational",
            api_key=os.getenv("MURF_API_KEY"),
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    logger.info("Session started. Speaking greeting...")
    # Directly speak greeting audio through TTS
    await session.say("नमस्ते! मैं आशाअसिस्ट हूँ। पेशेंट का नाम और उम्र क्या है?")


if __name__ == "__main__":
    cli.run_app(server)