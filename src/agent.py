import asyncio
import os
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

# ==========================================
# MANDATORY PROMPT RULES & PROMPTS
# ==========================================
LANGUAGE_SCRIPT_RULE = """
LANGUAGE & SCRIPT:
Always write every language in its own native script.
Hindi → Devanagari (नमस्ते), never romanized (never "namaste").
English → English script.
If the user speaks English, respond in clear English.
If the user speaks Hindi, respond in Hindi (Devanagari script).
"""

MAIN_SYSTEM_PROMPT = f"""
You are AshaAssist (आशाअसिस्ट), the primary AI healthcare triage assistant for the local Primary Health Centre (PHC).

{LANGUAGE_SCRIPT_RULE}

OUTBOUND CALL OPENING RULE:
When the call starts, identify yourself as AshaAssist from PHC, explain routine checkups, and mention users can say "stop" or "बंद करो" to opt out.

HANDOFF RULE (IMPORTANT):
- If the user asks to book an appointment, check doctor timings, schedule a clinic visit, or asks for clinic timings, say clearly in their language:
  - Hindi: "मैं आपको हमारे अपॉइंटमेंट विशेषज्ञ से जोड़ रही हूँ।"
  - English: "I am connecting you to our appointment specialist."
- Then immediately call the `transfer_to_appointment_specialist` tool.

HEALTH DIRECTORY LOOKUP:
- For general health center locations or emergency numbers, call `lookup_nearest_phc`.
"""

SPECIALIST_SYSTEM_PROMPT = f"""
You are AshaAssist's Clinic & Appointment Specialist (अपॉइंटमेंट विशेषज्ञ).
Your job is ONLY to help patients schedule, reschedule, or check doctor clinic slots and timings at local Primary Health Centres (PHCs).

{LANGUAGE_SCRIPT_RULE}

Be concise and polite. Match the language spoken by the user.
"""

# ==========================================
# STANDALONE LLM FUNCTION TOOLS
# ==========================================
@llm.function_tool(
    description="Check available doctor appointment slots or clinic timings for a specified PHC and date."
)
async def check_clinic_slots(phc_name: str = "PHC", date: str = "today") -> str:
    logger.info(f"📅 [SPECIALIST TOOL CALLED] Checking slots for {phc_name} on {date}")
    return f"Clinic timing for {phc_name} is 9:00 AM to 4:00 PM Monday through Saturday. Available OPD slots for {date}: 10:00 AM and 2:00 PM."


@llm.function_tool(
    description="Look up nearest PHC facility numbers and location details."
)
async def lookup_nearest_phc(district: str = "Local") -> str:
    logger.info(f"🏥 [PHC LOOKUP CALLED] District: {district}")
    return f"Nearest PHC in {district} area is Osmania General Hospital (24x7 Emergency). Helpline: 108."


# ==========================================
# WORKER ENTRYPOINT
# ==========================================
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    logger.info("✅ Agent connected to LiveKit room!")

    logger.info("⏳ Waiting for user to join room...")
    participant = await ctx.wait_for_participant()
    logger.info(f"👤 User connected: {participant.identity}")

    # Use multi-language or English/Hindi dynamic STT configuration
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model="nova-2-general", language="multi"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
        ),
    )

    # 1. Specialist Agent Definition
    specialist_agent = voice.Agent(
        instructions=SPECIALIST_SYSTEM_PROMPT,
        tools=[check_clinic_slots],
    )

    # 2. Dynamic Handoff Tool (FIXED: Synchronous session.update_agent)
    @llm.function_tool(
        description="Transfer the caller to the Clinic & Appointment Specialist when they want to book, reschedule, or inquire about appointment slots and clinic timings."
    )
    async def transfer_to_appointment_specialist(reason: str = "Appointment/Clinic inquiry") -> str:
        logger.info(f"🔄 [HANDOFF EXECUTING] Reason: {reason}")
        
        # FIX: session.update_agent is non-async in livekit-agents 1.x
        session.update_agent(specialist_agent)
        
        specialist_greeting = (
            "Hello! I am the appointment specialist for the Primary Health Centre. "
            "How can I help you with your appointment or timing inquiry?"
        )
        try:
            await session.say(specialist_greeting, allow_interruptions=True)
        except RuntimeError:
            logger.warning("Session closed during handoff greeting.")
            
        return "Transferred successfully to Appointment Specialist."

    # 3. Main Agent Definition
    main_agent = voice.Agent(
        instructions=MAIN_SYSTEM_PROMPT,
        tools=[lookup_nearest_phc, transfer_to_appointment_specialist],
    )

    # 4. Start Session
    await session.start(agent=main_agent, room=ctx.room)

    await asyncio.sleep(1.0)

    greeting = (
        "नमस्ते! मैं प्राथमिक स्वास्थ्य केंद्र से आशाअसिस्ट बोल रही हूँ। "
        "How can I assist you with your health center visit today?"
    )
    logger.info("🗣️ Speaking initial greeting...")
    try:
        await session.say(greeting, allow_interruptions=True)
    except RuntimeError:
        logger.warning("Participant disconnected before greeting was spoken.")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )