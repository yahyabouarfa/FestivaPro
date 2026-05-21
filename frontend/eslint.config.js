import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

export default [
  { ignores: ["dist"] },
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh
    },
    languageOptions: {
      parserOptions: { ecmaVersion: "latest", sourceType: "module" },
      globals: {
        window: "readonly",
        document: "readonly",
        localStorage: "readonly",
        HTMLCanvasElement: "readonly",
        Image: "readonly"
      }
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }]
    }
  }
];
