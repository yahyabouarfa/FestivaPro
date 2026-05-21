import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootLogo = resolve(__dirname, "../../FestivaPro.png");
const publicLogo = resolve(__dirname, "../public/FestivaPro.png");

if (!existsSync(rootLogo)) {
  throw new Error("FestivaPro.png was not found in the project root.");
}

mkdirSync(dirname(publicLogo), { recursive: true });
copyFileSync(rootLogo, publicLogo);
console.log("Synced official FestivaPro logo into frontend/public.");
