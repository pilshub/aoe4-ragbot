"use client";

import { useState } from "react";
import { useLang } from "../lib/LangContext";

interface RatingData {
  label: string;
  value: number;
}

interface Props {
  ratings: RatingData[];
}

const RATING_FULL_NAMES: Record<string, { es: string; en: string }> = {
  AGR: { es: "Agresión", en: "Aggression" },
  DEF: { es: "Defensa", en: "Defense" },
  INF: { es: "Infantería", en: "Infantry" },
  RNG: { es: "A distancia", en: "Ranged" },
  CAV: { es: "Caballería", en: "Cavalry" },
  SIE: { es: "Asedio", en: "Siege" },
  MON: { es: "Monjes", en: "Monks" },
  NAV: { es: "Naval", en: "Naval" },
  TRD: { es: "Comercio", en: "Trade" },
  ECO: { es: "Economía", en: "Economy" },
};

const SIZE = 200;
const CENTER = SIZE / 2;
const MAX_VAL = 5;
const LEVELS = [1, 2, 3, 4, 5];

function polarToXY(angle: number, radius: number): [number, number] {
  const rad = (angle - 90) * (Math.PI / 180);
  return [CENTER + radius * Math.cos(rad), CENTER + radius * Math.sin(rad)];
}

export default function VortixRating({ ratings }: Props) {
  const [hovered, setHovered] = useState<number | null>(null);
  const { lang } = useLang();
  const n = ratings.length;
  if (n < 3) return null;

  const angleStep = 360 / n;
  const maxRadius = CENTER - 30;

  const gridPaths = LEVELS.map((level) => {
    const r = (level / MAX_VAL) * maxRadius;
    const points = Array.from({ length: n }, (_, i) => polarToXY(i * angleStep, r));
    return points.map((p) => `${p[0]},${p[1]}`).join(" ");
  });

  const dataPoints = ratings.map((d, i) => {
    const r = (Math.min(d.value, MAX_VAL) / MAX_VAL) * maxRadius;
    return polarToXY(i * angleStep, r);
  });
  const dataPath = dataPoints.map((p) => `${p[0]},${p[1]}`).join(" ");

  const axisEnds = Array.from({ length: n }, (_, i) =>
    polarToXY(i * angleStep, maxRadius)
  );

  const labelRadius = maxRadius + 18;
  const labelPositions = Array.from({ length: n }, (_, i) =>
    polarToXY(i * angleStep, labelRadius)
  );

  return (
    <div className="mt-3 pt-2 border-t border-border">
      <p className="text-xs text-text-dim mb-2 font-[family-name:var(--font-heading)] uppercase tracking-wider">
        Vortix Rating
      </p>
      <div className="flex justify-center">
        <div className="relative" style={{ width: SIZE, height: SIZE }}>
          <svg
            viewBox={`0 0 ${SIZE} ${SIZE}`}
            width={SIZE}
            height={SIZE}
            className="overflow-visible"
          >
            {/* Grid polygons */}
            {gridPaths.map((points, i) => (
              <polygon
                key={`grid-${i}`}
                points={points}
                fill="none"
                stroke="rgba(201,168,76,0.12)"
                strokeWidth={i === LEVELS.length - 1 ? 1 : 0.5}
              />
            ))}

            {/* Axis lines */}
            {axisEnds.map((end, i) => (
              <line
                key={`axis-${i}`}
                x1={CENTER}
                y1={CENTER}
                x2={end[0]}
                y2={end[1]}
                stroke="rgba(201,168,76,0.08)"
                strokeWidth={0.5}
              />
            ))}

            {/* Data polygon fill */}
            <polygon
              points={dataPath}
              fill="rgba(201,168,76,0.15)"
              stroke="rgba(201,168,76,0.7)"
              strokeWidth={1.5}
              className="radar-appear"
            />

            {/* Data points + invisible hit areas */}
            {dataPoints.map((p, i) => (
              <g key={`dot-${i}`}>
                <circle
                  cx={p[0]}
                  cy={p[1]}
                  r={hovered === i ? 4 : 2.5}
                  fill="#c9a84c"
                  style={{
                    transition: "r 0.15s",
                    filter: hovered === i ? "drop-shadow(0 0 4px rgba(201,168,76,0.7))" : "none",
                  }}
                />
                <circle
                  cx={p[0]}
                  cy={p[1]}
                  r={14}
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                />
              </g>
            ))}

            {/* Labels */}
            {labelPositions.map((pos, i) => {
              const angle = i * angleStep;
              let anchor: "start" | "middle" | "end" = "middle";
              if (angle > 20 && angle < 160) anchor = "start";
              if (angle > 200 && angle < 340) anchor = "end";

              let dy = "0.35em";
              if (angle > 340 || angle < 20) dy = "0em";
              if (angle > 160 && angle < 200) dy = "0.7em";

              return (
                <text
                  key={`label-${i}`}
                  x={pos[0]}
                  y={pos[1]}
                  textAnchor={anchor}
                  dy={dy}
                  fontSize={8}
                  fontFamily="var(--font-heading)"
                  fill={hovered === i ? "#c9a84c" : "#9a9284"}
                  style={{ transition: "fill 0.15s" }}
                >
                  {ratings[i].label}
                  <tspan fill="#c9a84c" fontWeight="600" dx="3">
                    {ratings[i].value}
                  </tspan>
                </text>
              );
            })}
          </svg>

          {/* Tooltip overlay (HTML, not SVG — easier to style) */}
          {hovered !== null && (() => {
            const pt = dataPoints[hovered];
            const fullName = RATING_FULL_NAMES[ratings[hovered].label];
            const name = fullName ? fullName[lang] : ratings[hovered].label;
            return (
              <div
                className="absolute pointer-events-none z-10 px-2.5 py-1.5 rounded
                           bg-bg-card border border-border-gold shadow-gold text-xs whitespace-nowrap"
                style={{
                  left: pt[0],
                  top: pt[1] - 32,
                  transform: "translateX(-50%)",
                }}
              >
                <span className="text-text-secondary">{name}</span>
                <span className="text-gold font-bold ml-1.5">{ratings[hovered].value}/5</span>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
