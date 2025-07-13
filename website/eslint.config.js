import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import astro from "eslint-plugin-astro";

export default [
	js.configs.recommended,
	{
		files: ["**/*.{js,mjs,cjs,ts,tsx,astro}"],
		ignores: ["dist/**", ".astro/**", "node_modules/**"],
		languageOptions: {
			parser: tsparser,
			parserOptions: {
				ecmaVersion: "latest",
				sourceType: "module"
			}
		},
		plugins: {
			"@typescript-eslint": tseslint,
			astro: astro
		},
		rules: {
			"@typescript-eslint/no-unused-vars": "warn",
			"@typescript-eslint/no-explicit-any": "warn",
			"no-console": "warn",
			"no-unused-vars": "off" // Disable base rule in favor of TS rule
		}
	},
	...astro.configs.recommended,
	{
		files: ["**/*.astro"],
		ignores: ["dist/**", ".astro/**"],
		rules: {
			"astro/no-conflict-set-directives": "error",
			"astro/no-unused-define-vars-in-style": "error"
		}
	},
	{
		ignores: ["dist/**", ".astro/**", "node_modules/**"]
	}
];
