import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";

import { authOptions } from "@/lib/authOptions";
import { mintBridgeToken } from "@/lib/bridgeToken";

export const dynamic = "force-dynamic";

/** A ten-minute token for the signed-in visitor, to call the API's saved-report routes. */
export async function GET() {
  const secret = process.env.AUTH_BRIDGE_SECRET;
  if (!secret) return NextResponse.json({ detail: "Accounts are not set up" }, { status: 503 });
  const user = (await getServerSession(authOptions))?.user;
  if (!user?.id || !user.email) return NextResponse.json({ detail: "Not signed in" }, { status: 401 });
  const token = mintBridgeToken({ sub: user.id, email: user.email }, secret, Date.now());
  return NextResponse.json({ token }, { headers: { "Cache-Control": "no-store" } });
}
