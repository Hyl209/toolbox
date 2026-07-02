import { DEFAULT_THEME_COLORS, THEME_ZONE_LABELS, THEME_ZONES, type ThemeName, type ThemeZone } from "..";

type ThemePaletteSectionProps = {
  theme: ThemeName;
  themeColors: Record<ThemeName, Record<ThemeZone, string>>;
  onChange: (zone: ThemeZone, value: string) => void;
};

const GLASS_MIN_ALPHA = 10;
const GLASS_MAX_ALPHA = 70;
const GLASS_MIN_BLUR = 4;
const GLASS_MAX_BLUR = 24;

function clampGlassAlpha(value: number): number {
  return Math.max(GLASS_MIN_ALPHA, Math.min(GLASS_MAX_ALPHA, Math.round(value)));
}

function clampColorPart(value: string): number {
  return Math.max(0, Math.min(255, Math.round(Number(value) || 0)));
}

function hexColor(value: string): string {
  const hex = value.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i)?.[1];
  if (hex) {
    const fullHex = hex.length === 3 ? hex.split("").map((part) => part + part).join("") : hex.slice(0, 6);
    return `#${fullHex.toLowerCase()}`;
  }

  const rgb = value.match(/^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i);
  if (!rgb) {
    return "#000000";
  }
  return `#${[rgb[1], rgb[2], rgb[3]].map((part) => clampColorPart(part).toString(16).padStart(2, "0")).join("")}`;
}

function colorAlpha(value: string): number {
  const hex = value.trim().match(/^#[0-9a-f]{8}$/i)?.[0];
  if (hex) {
    return clampGlassAlpha((parseInt(hex.slice(7, 9), 16) / 255) * 100);
  }

  const alpha = value.match(/^rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\s*\)$/i)?.[1];
  if (!alpha) {
    return GLASS_MAX_ALPHA;
  }
  return clampGlassAlpha(Number(alpha) * 100);
}

function glassBlur(alphaPercent: number): number {
  const progress = (clampGlassAlpha(alphaPercent) - GLASS_MIN_ALPHA) / (GLASS_MAX_ALPHA - GLASS_MIN_ALPHA);
  return Math.ceil(GLASS_MIN_BLUR + (GLASS_MAX_BLUR - GLASS_MIN_BLUR) * progress);
}

function rgbaWithAlpha(value: string, alphaPercent: number): string {
  const color = hexColor(value);
  const red = parseInt(color.slice(1, 3), 16);
  const green = parseInt(color.slice(3, 5), 16);
  const blue = parseInt(color.slice(5, 7), 16);
  return `rgba(${red}, ${green}, ${blue}, ${(clampGlassAlpha(alphaPercent) / 100).toFixed(2)})`;
}

export default function ThemePaletteSection({ theme, themeColors, onChange }: ThemePaletteSectionProps) {
  const cardValue = themeColors[theme]?.card_bg ?? DEFAULT_THEME_COLORS[theme].card_bg;
  const cardAlpha = colorAlpha(cardValue);

  return (
    <section className="settings-card settings-wide-card">
      <span>主题配色</span>
      <p>当前主题的颜色草稿会持续保留；开启自定义主题后才会真正应用到界面。</p>
      <div className="theme-swatch-row">
        {THEME_ZONES.map((zone) => {
          const value = themeColors[theme]?.[zone] ?? DEFAULT_THEME_COLORS[theme][zone];
          const label = THEME_ZONE_LABELS[zone];
          return (
            <label className="theme-swatch" key={zone}>
              <span className="theme-color-dot" style={{ background: value }}>
                <input
                  aria-label={`${label.title} 取色`}
                  className="theme-color-picker"
                  onChange={(event) => onChange(zone, zone === "card_bg" ? rgbaWithAlpha(event.target.value, cardAlpha) : event.target.value)}
                  type="color"
                  value={hexColor(value)}
                />
              </span>
              <b>{label.title}</b>
              <small>{label.description}</small>
              <input
                aria-label={`${label.title} color`}
                onChange={(event) => onChange(zone, event.target.value)}
                type="text"
                value={value}
              />
            </label>
          );
        })}
        <label className="theme-opacity-control">
          <span className="theme-color-dot" style={{ background: cardValue }} />
          <b>玻璃强度</b>
          <small>Alpha {cardAlpha}% / Blur {glassBlur(cardAlpha)}px</small>
          <input
            aria-label="玻璃强度"
            max="70"
            min="10"
            onChange={(event) => onChange("card_bg", rgbaWithAlpha(cardValue, Number(event.target.value)))}
            step="1"
            type="range"
            value={cardAlpha}
          />
        </label>
      </div>
    </section>
  );
}
