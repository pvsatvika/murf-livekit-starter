import logging
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    llm,
    voice,
)
from livekit.plugins import deepgram, groq, murf, silero
from src.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asha-agent")

init_db()


@llm.function_tool(description="Look up the nearest Primary Health Centre (PHC), hospital, or emergency helpline for a given district or city in India.")
async def lookup_nearest_phc(district: str) -> str:  # <-- FIXED: Made this an async function
    logger.info(f"🔍 [TOOL CALLED] lookup_nearest_phc for district: {district}")
    
    today_str = datetime.date.today().strftime("%d %B %Y")
    
    phc_registry = {
        "hyderabad": {
            "facility": "Osmania General Hospital & Community Health Centre",
            "address": "Afzal Gunj, Hyderabad",
            "timing": "24x7 Emergency Services",
            "helpline": "108",
        },
        "delhi": {
            "facility": "Primary Health Centre (PHC) Mehrauli",
            "address": "Near Qutub Minar, New Delhi",
            "timing": "8:00 AM to 4:00 PM",
            "helpline": "102 / 108",
        },
        "mumbai": {
            "facility": "KEM Hospital & Municipal Health Centre",
            "address": "Parel, Mumbai",
            "timing": "24x7 Emergency Services",
            "helpline": "108",
        }
    }
    
    key = district.lower().strip()
    if key in phc_registry:
        data = phc_registry[key]
        return (
            f"As of {today_str}, the nearest facility in {district.capitalize()} is {data['facility']}, "
            f"located at {data['address']}. Timings: {data['timing']}. Emergency Helpline: {data['helpline']}."
        )
    else:
        return (
            f"No local PHC directory entry found for '{district}' as of {today_str}. "
            f"Direct the user to call the National Health Helpline at 104 or Emergency Ambulance at 108 immediately."
        )


SYSTEM_PROMPT = """
You are AshaAssist (आशाअसिस्ट), a warm and empathetic AI healthcare assistant for India.

LANGUAGE & SCRIPT RULES:
Always write every language in its own native script.
Hindi → Devanagari (नमस्ते), never romanized (never "namaste").
Same rule for all non-English languages.

INSTRUCTIONS:
1. Speak naturally and concisely.
2. When a user asks for local health facilities, hospitals, or emergency numbers, call the `lookup_nearest_phc` tool.
3. Express the tool's result naturally in full sentences. NEVER read raw JSON or key names.
4. Always state when the information is updated from (e.g., "आज 10 अगस्त के अपडेट के अनुसार...").
5. If the tool reports no data for a district, provide a calm spoken fallback directing the user to 108 or 104.
"""


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    logger.info("✅ Agent successfully connected to room!")

    # Session handles speech pipelines (VAD, STT, LLM model, TTS)
    session = voice.AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            text_pacing=True,
        ),
    )

    # Agent handles instructions and tools
    agent = voice.Agent(
        instructions=SYSTEM_PROMPT,
        tools=[lookup_nearest_phc],
    )

    await session.start(agent=agent, room=ctx.room)
    logger.info("🎙️ Voice session started successfully in room.")

    await session.say(
        "नमस्ते! मैं आशाअसिस्ट हूँ। आज मैं आपकी क्या सहायता कर सकती हूँ?",
        allow_interruptions=True,
    )
    logger.info("🗣️ Initial greeting spoken successfully.")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="asha-agent",
        )
    )