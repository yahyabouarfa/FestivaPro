type RGB = [number, number, number];

const fallback = {
  night: [7, 17, 31] as RGB,
  surface: [16, 27, 47] as RGB,
  primary: [168, 85, 247] as RGB,
  secondary: [236, 72, 153] as RGB,
  accent: [249, 115, 22] as RGB
};

const brightness = ([r, g, b]: RGB) => (r * 299 + g * 587 + b * 114) / 1000;
const saturation = ([r, g, b]: RGB) => {
  const max = Math.max(r, g, b) / 255;
  const min = Math.min(r, g, b) / 255;
  return max === 0 ? 0 : (max - min) / max;
};

function setColor(name: string, rgb: RGB) {
  document.documentElement.style.setProperty(`--color-${name}`, rgb.join(" "));
}

function applyPalette(colors: typeof fallback) {
  Object.entries(colors).forEach(([name, rgb]) => setColor(name, rgb));
  document.documentElement.style.setProperty(
    "--gradient-neon",
    `linear-gradient(135deg, rgb(${colors.primary.join(" ")}), rgb(${colors.secondary.join(" ")}), rgb(${colors.accent.join(" ")}))`
  );
  document.documentElement.style.setProperty(
    "--shadow-glow",
    `0 0 32px rgb(${colors.primary.join(" ")} / 0.30), 0 0 58px rgb(${colors.secondary.join(" ")} / 0.18)`
  );
}

function sampleImage(image: HTMLImageElement): RGB[] {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) return [];
  canvas.width = 96;
  canvas.height = 96;
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
  const buckets = new Map<string, { rgb: RGB; count: number }>();

  for (let index = 0; index < data.length; index += 16) {
    const alpha = data[index + 3];
    if (alpha < 140) continue;
    const rgb: RGB = [data[index], data[index + 1], data[index + 2]];
    if (brightness(rgb) < 22 || brightness(rgb) > 242) continue;
    const key = rgb.map((channel) => Math.round(channel / 24) * 24).join("-");
    const existing = buckets.get(key);
    if (existing) existing.count += 1;
    else buckets.set(key, { rgb, count: 1 });
  }

  return [...buckets.values()]
    .sort((a, b) => b.count * saturation(b.rgb) - a.count * saturation(a.rgb))
    .map((bucket) => bucket.rgb);
}

export function initializeThemeFromLogo() {
  applyPalette(fallback);

  const image = new Image();
  image.crossOrigin = "anonymous";
  image.onload = () => {
    const colors = sampleImage(image);
    if (colors.length < 3) return;
    const vibrant = colors.filter((color) => saturation(color) > 0.22);
    applyPalette({
      night: fallback.night,
      surface: fallback.surface,
      primary: vibrant[0] ?? fallback.primary,
      secondary: vibrant[1] ?? fallback.secondary,
      accent: vibrant[2] ?? fallback.accent
    });
  };
  image.src = "/FestivaPro.png";
}

export const chartColors = [
  "rgb(var(--color-primary))",
  "rgb(var(--color-secondary))",
  "rgb(var(--color-accent))",
  "#22c55e",
  "#38bdf8"
];
