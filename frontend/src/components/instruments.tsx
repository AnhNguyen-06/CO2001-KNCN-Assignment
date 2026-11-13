"use client";

import { memo, useId } from "react";
import { ScanFace } from "lucide-react";

export function BrandMark({ small = false }: { small?: boolean }) {
  return (
    <span
      className={`brand-mark ${small ? "brand-mark-small" : ""}`}
      aria-hidden="true"
    >
      <ScanFace strokeWidth={1.35} />
    </span>
  );
}

export const FaceMesh = memo(function FaceMesh({
  active = true,
  compact = false,
}: {
  active?: boolean;
  compact?: boolean;
}) {
  const id = useId().replaceAll(":", "");
  const points = [];
  for (let row = 0; row <= 41; row++) {
    const y = (row / 41) * 2 - 1;
    const width =
      Math.sqrt(Math.max(0, 1 - y * y)) * (y > 0.25 ? 1 - (y - 0.25) * 0.3 : 1);
    for (let col = -17; col <= 17; col++) {
      const x = (col / 17) * width;
      const eye =
        Math.pow((Math.abs(x) - 0.34) / 0.21, 2) +
          Math.pow((y + 0.17) / 0.1, 2) <
        1;
      if (Math.abs(x) > width || eye) continue;
      const depth = Math.sqrt(Math.max(0, 1 - x * x - y * y));
      const nose = Math.exp(-x * x * 35 - y * y * 10) * 15;
      const px = 160 + x * 86 + Math.sin(row * 5 + col) * 0.5;
      const py = 157 + y * 123 + nose;
      const opacity = 0.16 + depth * 0.6 + Math.sin(row * 9 + col * 7) * 0.13;
      points.push(
        <circle
          key={`${row}-${col}`}
          cx={px.toFixed(3)}
          cy={py.toFixed(3)}
          r={(compact ? 0.95 : 0.85 + depth * 0.45).toFixed(3)}
          opacity={opacity.toFixed(3)}
        />,
      );
    }
  }
  return (
    <div
      className={`face-mesh ${active ? "face-mesh-active" : ""}`}
      aria-hidden="true"
    >
      <svg viewBox="0 0 320 320" fill="none">
        <defs>
          <radialGradient id={`${id}-halo`}>
            <stop stopColor="#8cb8ef" stopOpacity=".12" />
            <stop offset="1" stopColor="#8cb8ef" stopOpacity="0" />
          </radialGradient>
          <linearGradient
            id={`${id}-face`}
            x1="80"
            y1="25"
            x2="225"
            y2="280"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#d8ecf8" />
            <stop offset="1" stopColor="#6484bf" />
          </linearGradient>
        </defs>
        <ellipse
          cx="160"
          cy="164"
          rx="155"
          ry="155"
          fill={`url(#${id}-halo)`}
        />
        <g fill={`url(#${id}-face)`}>{points}</g>
        <g stroke="#aecff2" strokeWidth=".8" opacity=".65">
          <path d="M115 137q15-9 28 0m35 0q15-9 28 0M159 144l-8 40q9 6 18 0m-29 28q20 10 40 0" />
          <path d="M99 119l26-9 20 8m30 0 20-8 26 9" opacity=".5" />
        </g>
        <g fill="#d8ecf8">
          {[
            [125, 137],
            [193, 137],
            [160, 185],
            [140, 212],
            [180, 212],
          ].map(([x, y], i) => (
            <circle cx={x} cy={y} r="2.4" key={i} />
          ))}
        </g>
        <g stroke="#8fb6ec" opacity=".25" strokeWidth=".6">
          <path d="M125 137l35 48 33-48M125 137l68 0M140 212l20-27 20 27M140 212h40" />
        </g>
      </svg>
    </div>
  );
});

export function CornerLights() {
  return (
    <>
      <i className="corner-light top-left" />
      <i className="corner-light top-right" />
      <i className="corner-light bottom-left" />
      <i className="corner-light bottom-right" />
    </>
  );
}

export function CircuitBoard() {
  return (
    <div className="circuit-board" aria-hidden="true">
      <div className="circuit-aura" />
      <svg viewBox="0 0 1040 400" preserveAspectRatio="xMidYMid meet">
        <g fill="none" stroke="rgba(186,207,247,.13)" strokeWidth="1">
          <path d="M0 120h235l40 40h130m-405 0h160l70 70h175M0 280h220l55-50h130M1040 120H805l-40 40H635m405 0H880l-70 70H635m405 50H820l-55-50H635M520 0v75m0 250v75M380 0v62l65 65M660 0v62l-65 65M380 400v-62l65-65m215 127v-62l-65-65" />
          <path
            d="M0 80h270l35 40h70M1040 80H770l-35 40h-70M0 320h270l35-40h70m665 40H770l-35-40h-70"
            opacity=".45"
          />
        </g>
        <g fill="#b2cdf2">
          {[
            [275, 160],
            [230, 230],
            [275, 230],
            [765, 160],
            [810, 230],
            [765, 230],
            [520, 75],
            [520, 325],
            [445, 127],
            [595, 273],
          ].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="2.5" opacity=".4" />
          ))}
        </g>
        <path
          className="circuit-flow"
          d="M140 160h20l70 70h175M635 160h130l40-40h95"
          fill="none"
          stroke="#a9bdeb"
          strokeWidth="1.5"
          strokeDasharray="7 240"
        />
      </svg>
      <div className="satellite satellite-camera">
        <span className="mini-status-dot" /> Camera input{" "}
        <small>Frame received</small>
      </div>
      <div className="satellite satellite-record">
        <span className="mini-status-dot" /> Attendance{" "}
        <small>One record per day</small>
      </div>
      <div className="central-chip">
        <div className="chip-rim">
          <BrandMark />
          <span>Presence</span>
          <small>Recognition engine</small>
        </div>
      </div>
      <div className="circuit-node node-one" />
      <div className="circuit-node node-two" />
    </div>
  );
}
