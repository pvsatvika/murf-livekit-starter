import datetime
import logging
from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    voice,
)
from livekit.plugins import deepgram, groq, murf, silero

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asha-agent")

OUTBOUND_SYSTEM_PROMPT = """
You are AshaAssist (आशाअसिस्ट), an outbound AI healthcare assistant calling on behalf of the local Primary Health Centre (PHC).

OUTBOUND CALL OPENING RULE (COMPULSORY):
When the call starts, your first statement MUST include these three elements:
1. WHO IS CALLING: Identify yourself as AshaAssist from the local Primary Health Centre.
2. WHY YOU ARE CALLING: State that you are calling for a routine medication and vaccination reminder.
3. HOW TO OPT OUT: Inform the user that they can say "stop" or "बंद करो" to opt out of future calls.

LANGUAGE & SCRIPT INSTRUCTION (COMPULSORY):
- Always write every language in its own native script.
- Hindi → Devanagari (e.g., नमस्ते, दवा, स्वास्थ्य), NEVER romanized (never "namaste", "dawa").
- Respond concisely and politely in warm, empathetic spoken conversational Hindi.

FUNCTION TOOL USAGE:
- If the user asks for health centre locations or emergency numbers, call the `lookup_nearest_phc` tool.
"""


@llm.function_tool(
    description="Look up the nearest Primary Health Centre (PHC), hospital, or emergency helpline for a given district or city in India."
)
async def lookup_nearest_phc(district: str) -> str:
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
        },
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


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    logger.info("✅ Outbound Agent connected to room!")

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            text_pacing=True,
        ),
    )

    agent = voice.Agent(
        instructions=OUTBOUND_SYSTEM_PROMPT,
        tools=[lookup_nearest_phc],
    )

    await session.start(agent=agent, room=ctx.room)
    logger.info("🎙️ Voice session started for outbound call.")

    outbound_greeting = (
        "नमस्ते! मैं प्राथमिक स्वास्थ्य केंद्र से आशाअसिस्ट बोल रही हूँ। "
        "मैं आपको आपकी नियमित टीकाकरण और दवा की याद दिलाने के लिए कॉल कर रही हूँ। "
        "यदि आप यह कॉल बंद करना चाहते हैं, तो 'बंद करो' कहें।"
    )

    await session.say(outbound_greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))