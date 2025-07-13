// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
	site: "https://cogency.dev",
	integrations: [tailwind(), sitemap()],
	build: {
		inlineStylesheets: "always"
	},
	compressHTML: true,
	prefetch: {
		prefetchAll: true,
		defaultStrategy: "viewport"
	}
});
