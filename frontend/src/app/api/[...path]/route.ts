import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const backend = process.env.PRESENCE_BACKEND_URL ?? "http://127.0.0.1:8000";
  const target = new URL(
    `/api/${path.map(encodeURIComponent).join("/")}`,
    backend,
  );
  target.search = request.nextUrl.search;
  try {
    let body: Uint8Array | undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      const chunks: Uint8Array[] = [];
      let size = 0;
      if (request.body) {
        for await (const chunk of request.body) {
          size += chunk.byteLength;
          if (size > 4 * 1024 * 1024)
            return Response.json(
              {
                code: "PAYLOAD_TOO_LARGE",
                message: "Please capture smaller photos.",
              },
              { status: 413 },
            );
          chunks.push(chunk);
        }
      }
      body = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) {
        body.set(chunk, offset);
        offset += chunk.byteLength;
      }
    }
    const response = await fetch(target, {
      method: request.method,
      headers: {
        "Content-Type":
          request.headers.get("content-type") ?? "application/json",
        ...(process.env.PRESENCE_BACKEND_KEY
          ? { "X-Presence-Key": process.env.PRESENCE_BACKEND_KEY }
          : {}),
      },
      body: body as BodyInit | undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(25000),
    });
    if (
      [502, 503, 504].includes(response.status) ||
      response.headers.get("content-type")?.includes("text/html")
    ) {
      await response.body?.cancel();
      return Response.json(
        {
          code: "BACKEND_WAKING_UP",
          message:
            "The recognition service is starting or temporarily unavailable. Retrying automatically.",
        },
        { status: 503, headers: { "Retry-After": "10" } },
      );
    }
    const headers = new Headers({ "Cache-Control": "no-store" });
    for (const key of ["content-type", "content-disposition"]) {
      const value = response.headers.get(key);
      if (value) headers.set(key, value);
    }
    return new Response(response.body, { status: response.status, headers });
  } catch {
    return Response.json(
      {
        code: "BACKEND_UNAVAILABLE",
        message:
          "The recognition service is starting or temporarily unavailable. Retrying automatically.",
      },
      { status: 503 },
    );
  }
}

export { proxy as GET, proxy as POST, proxy as DELETE };
