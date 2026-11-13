# Presence frontend

Next.js App Router, React and TypeScript attendance workspace, integrated with the Python CV backend. The English interface follows [the supplied design guide](../docs/authkit.com-DESIGN.md) and self-hosts Inter/Manrope.

## Run

Requires Node.js 20.9+ and npm. From this directory:

```powershell
npm ci
npm run dev
```

Start the Python backend on port 8000 using [its README](../backend/README.md), then open http://127.0.0.1:3000. Camera access requires localhost or HTTPS.

Optional configuration: copy `.env.example` to `.env.local`, then restart Next.js. All backend variables are server-only; never prefix the shared secret with NEXT_PUBLIC.

## Pages

| Route                  | Experience                                                                          |
| ---------------------- | ----------------------------------------------------------------------------------- |
| /                      | Product introduction and generic workflow illustration                              |
| /attendance            | Actual CV recognition, daily arrivals, camera control and export state              |
| /members               | Database-backed profiles and enrollment                                             |
| /members?register=true | Open registration directly                                                          |
| /records               | Database attendance, search/date/member filters, pagination and real Excel download |
| /settings              | Browser display preferences; resetting preserves backend data                       |

Register a unique ID, full name and three actual camera photos. Every photo is checked by YuNet/SFace; saving revalidates all three and commits the profile atomically. Open Attendance and turn on the camera for automatic recognition and check-in. [Vietnamese walkthrough](../docs/WEB_DEMO.md).

## Integration

- `src/app/api/[...path]/route.ts`: bounded same-origin HTTP proxy to FastAPI.
- `src/components/provider.tsx`: reads actual profiles/records/export state; refreshes after writes and polls while visible.
- `src/lib/use-camera.ts`: owns getUserMedia, captures unmirrored JPEGs and stops media tracks.
- `src/lib/use-recognition.ts`: backend session lifecycle; one frame request at a time, no growing queue.
- `src/components/face-overlay.tsx`: actual returned boxes/landmarks/names, mapped to video dimensions and mirror setting.
- `src/lib/api.ts`: structured backend errors and server-generated workbook download.

The only localStorage payload is display preferences under presence.preferences.v1. Legacy mock profiles are discarded. The app contains no seeded identities or simulated attendance controls. Registration photos remain in dialog memory until completion/cancellation.

## Verify

Prepare real-model fixtures once from the repository root:

```powershell
cd backend
.venv/Scripts/python.exe -m tools.verification_data
.venv/Scripts/python.exe -m tools.prepare_web_fixtures
cd ../frontend
npm run typecheck
npm run build
npm run test:e2e
```

Playwright uses installed Chrome, portrait-based Y4M test cameras, the actual ONNX models and isolated SQLite. It starts a Python service on 8001 and a production Next.js service on 3100; leave these ports free. The test suite does not reuse the application database on port 8000. Tests cover enrollment, real CV, unknown/no-face rejection, duplicate prevention, database persistence, workbook contents, permission/service errors, media cleanup and responsive pages. Test order intentionally exercises one shared test-only enrollment journey.

Screenshots are in ignored test-results/. These controlled tests do not establish field accuracy or physical camera quality.

## Production

```powershell
npm run build
npm run start
```

For Vercel, choose frontend as Root Directory and configure PRESENCE_BACKEND_URL to a reachable HTTPS Python backend with persistent data storage. See [deployment instructions](../docs/DEPLOYMENT.md).
