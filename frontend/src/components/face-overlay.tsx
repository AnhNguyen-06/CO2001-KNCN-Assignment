import { RecognitionResult } from "@/lib/api";

export function FaceOverlay({
  result,
  mirror,
}: {
  result: RecognitionResult;
  mirror: boolean;
}) {
  const width = result.image_width;
  return (
    <svg
      className="face-overlay"
      viewBox={`0 0 ${width} ${result.image_height}`}
      preserveAspectRatio="xMidYMid meet"
      aria-label="Face recognition results"
    >
      {result.faces.map((face, index) => {
        const [rawX, y, w, h] = face.bbox;
        const x = mirror ? width - rawX - w : rawX;
        const confirmed = ["created", "already_exists", "confirmed"].includes(
          face.state,
        );
        const color = confirmed ? "#9bcbbd" : "#b9d4f5";
        const label =
          face.name ??
          (face.quality.accepted ? "Unknown" : "Adjust your position");
        return (
          <g key={face.track_id ?? index} data-state={face.state}>
            <rect
              x={x}
              y={y}
              width={w}
              height={h}
              rx="8"
              fill="none"
              stroke={color}
              strokeWidth="2"
            />
            {face.landmarks.map(([px, py], point) => (
              <circle
                key={point}
                cx={mirror ? width - px : px}
                cy={py}
                r="2"
                fill={color}
              />
            ))}
            <rect
              x={Math.max(0, x)}
              y={Math.max(0, y - 30)}
              width={Math.min(
                width - Math.max(0, x),
                Math.max(120, label.length * 10 + 20),
              )}
              height="26"
              rx="4"
              fill="#090f1ee8"
            />
            <text
              x={Math.max(0, x) + 8}
              y={Math.max(0, y - 30) + 18}
              fill={color}
              fontFamily="Inter, sans-serif"
              fontSize="16"
            >
              {label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
