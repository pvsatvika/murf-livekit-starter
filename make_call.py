import asyncio
import os
import sys
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=".env.local")
load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

SIP_TRUNK_ID = os.getenv("SIP_TRUNK_ID", "ST_ZWQfEKg6vbib")

async def trigger_outbound_call(sip_user: str):
    lkapi = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    room_name = "outbound-asha-room"

    print(f"📞 Initiating outbound SIP call to '{sip_user}' using Trunk {SIP_TRUNK_ID}...")

    try:
        sip_participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=sip_user,  # Must be just username/number, NOT 'sip:user@domain'
                room_name=room_name,
                participant_identity="asha_patient",
                participant_name="Asha Patient",
            )
        )
        print(f"✅ Call initiated successfully! Participant ID: {sip_participant.participant_id}")
    except Exception as e:
        print(f"❌ Failed to place call: {e}")
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    # Updated default to your exact Linphone username "satvika_1208"
    target_user = sys.argv[1] if len(sys.argv) > 1 else "satvika_1208"
    asyncio.run(trigger_outbound_call(target_user))