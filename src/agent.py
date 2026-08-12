import asyncio
import datetime
import json
import logging
import os
import uuid
import requests
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

# Webhook URL configured from .env file with fallback
DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1536799774257324133/1536799774764830862"
)

OUTBOUND_SYSTEM_PROMPT = """
You are AshaAssist (आशाअसिस्ट), an AI healthcare assistant calling on behalf of the local Primary Health Centre (PHC).

OUTBOUND CALL OPENING RULE:
When the call starts, your opening statement must identify yourself as AshaAssist from the PHC, explain that you are calling for routine health updates, and mention that the user can say "stop" or "बंद करो" to opt out.

LANGUAGE & SCRIPT INSTRUCTION (COMPULSORY):
- Always write every language in its own native script.
- Hindi → Devanagari (e.g., नमस्ते, दवा, स्वास्थ्य), NEVER romanized (never "namaste", "dawa").
- Respond concisely and politely in warm, empathetic spoken conversational Hindi or English based on user preference.

FUNCTION TOOL USAGE:
- If the user asks for health centre locations or emergency numbers, call the `lookup_nearest_phc` tool.

ESCALATION & HUMAN HELP PROTOCOL (STRICT ORDER OF OPERATIONS):
You are an AI assistant, NOT a medical doctor. You must recognize when a situation requires human escalation.

ESCULATION TRIGGERS:
1. Red-Flag Symptoms: Severe chest pain, extreme shortness of breath, heavy bleeding, or infant emergency.
2. Medical Diagnosis or Prescription Advice: When the user asks for a specific diagnosis or doctor prescription.

CRITICAL WORKFLOW (MUST FOLLOW IN TWO SEPARATE STEPS):
STEP 1: WHEN RED-FLAG SYMPTOMS OR DIAGNOSIS REQUESTS OCCUR:
   - DO NOT EXECUTE `create_escalation` YET. DO NOT CALL ANY TOOLS.
   - IMMEDIATELY ask for clear permission using these exact words (or native Devanagari equivalent):
     "I am an AI assistant. For this issue, I should connect you with a human medical supervisor. May I have your permission to share your details and log an escalation request?"

STEP 2: WAIT FOR THE USER'S RESPONSE TO YOUR CONSENT QUESTION:
   - IF THE USER SAYS YES / हाँ / PLEASE / SURES / OK:
     * NOW execute the `create_escalation` tool.
     * Read out the generated Reference ID clearly to the user once the tool finishes.
     * Reassure them that a human medical supervisor will review their case shortly.
   - IF THE USER SAYS NO / नहीं / CANCEL / STOP:
     * DO NOT call the `create_escalation` tool.
     * Direct the caller immediately to national emergency helplines: 108 (Ambulance) or 104 (Medical Advice).
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


def _save_local_backup(record: dict):
    """Synchronous file writing helper to run inside asyncio.to_thread."""
    with open("escalations.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@llm.function_tool(
    description="Creates a human escalation request when a user reports red-flag symptoms or asks for medical diagnoses. MUST ONLY BE EXECUTED AFTER USER EXPRESSES EXPLICIT CONSENT (YES/PLEASE)."
)
async def create_escalation(
    patient_name: str = "Unknown",
    district: str = "Unknown",
    issue_summary: str = "",
    urgency_level: str = "HIGH",
    language_preferred: str = "Hindi",
) -> str:
    logger.info(f"🚨 [TOOL CALLED] create_escalation triggered for {patient_name}")
    
    ref_id = f"REF-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "content": f"🚨 **NEW HEALTHCARE ESCALATION - {ref_id}**",
        "embeds": [
            {
                "title": f"Urgency Level: {urgency_level.upper()}",
                "color": 15158332 if urgency_level.upper() in ["EMERGENCY", "HIGH"] else 3447003,
                "fields": [
                    {"name": "Reference ID", "value": ref_id, "inline": True},
                    {"name": "Patient / District", "value": f"{patient_name or 'Caller'} ({district or 'Unknown'})", "inline": True},
                    {"name": "Language", "value": language_preferred or "Hindi", "inline": True},
                    {"name": "Issue Summary", "value": issue_summary or "No summary provided.", "inline": False},
                    {"name": "Status", "value": "OPEN - Awaiting Medical Supervisor Review", "inline": False},
                ],
                "footer": {"text": f"Logged at {timestamp} | AshaAssist Human-in-the-Loop"}
            }
        ]
    }

    # Dispatch to Discord asynchronously to prevent blocking the event loop
    if DISCORD_WEBHOOK_URL and DISCORD_WEBHOOK_URL.startswith("http"):
        try:
            await asyncio.to_thread(requests.post, DISCORD_WEBHOOK_URL, json=payload, timeout=5)
            logger.info("✅ Escalation alert successfully dispatched to Discord!")
        except Exception as e:
            logger.error(f"❌ Failed to dispatch Discord Webhook: {e}")

    # Local Backup JSON (Offloaded to worker thread)
    escalation_record = {
        "reference_id": ref_id,
        "timestamp": timestamp,
        "patient": patient_name,
        "district": district,
        "summary": issue_summary,
        "urgency": urgency_level,
        "language": language_preferred
    }
    try:
        await asyncio.to_thread(_save_local_backup, escalation_record)
    except Exception as e:
        logger.error(f"Failed to write local backup: {e}")

    return f"Escalation successfully created. The unique Reference ID is {ref_id}."


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
        tools=[lookup_nearest_phc, create_escalation],
    )

    await session.start(agent=agent, room=ctx.room)
    logger.info("🎙️ Voice session started.")

    outbound_greeting = (
        "नमस्ते! मैं प्राथमिक स्वास्थ्य केंद्र से आशाअसिस्ट बोल रही हूँ। "
        "मैं आपको आपकी नियमित स्वास्थ्य जानकारी के लिए कॉल कर रही हूँ। "
        "यदि आप यह कॉल बंद करना चाहते हैं, तो 'बंद करो' कहें।"
    )

    await session.say(outbound_greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))