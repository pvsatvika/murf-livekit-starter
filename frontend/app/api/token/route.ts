import { AccessToken, RoomConfiguration, RoomAgentDispatch } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const room = request.nextUrl.searchParams.get("room") || "asha-room";
  const username = request.nextUrl.searchParams.get("username") || "asha-worker";

  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const wsUrl = process.env.LIVEKIT_URL || process.env.NEXT_PUBLIC_LIVEKIT_URL;

  if (!apiKey || !apiSecret || !wsUrl) {
    return NextResponse.json(
      { error: "Missing LiveKit keys in environment variables" },
      { status: 500 }
    );
  }

  try {
    const at = new AccessToken(apiKey, apiSecret, { identity: username });

    // Grant room permissions
    at.addGrant({
      roomJoin: true,
      room: room,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    // Dispatch to 'asha-agent' using the RoomConfiguration class
    at.roomConfig = new RoomConfiguration({
      agents: [
        new RoomAgentDispatch({
          agentName: "asha-agent",
          metadata: "",
        }),
      ],
    });

    const token = await at.toJwt();
    return NextResponse.json({ token, url: wsUrl });
  } catch (error) {
    return NextResponse.json({ error: "Failed to create token" }, { status: 500 });
  }
}