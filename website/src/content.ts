/**
 * Centralized content for cogency.dev
 * 
 * Single source of truth for all website copy, messaging, and configuration.
 * Beautiful, type-safe, and easy to maintain.
 */

export const site = {
  name: "Cogency",
  tagline: "Smart AI agents that think as hard as they need to",
  url: "https://cogency.dev",
  version: "0.9.0",
  status: "Production Beta",
  
  social: {
    github: "https://github.com/iteebz/cogency",
    pypi: "https://pypi.org/project/cogency/",
  }
} as const;

export const hero = {
  badge: {
    text: "Production-ready from day one",
    emoji: "⚡",
    variant: "success" as const
  },
  
  headline: {
    primary: "Conversational AI agents",
    secondary: "that actually work",
    gradient: true
  },
  
  subheader: [
    "True multi-step reasoning with intelligent tool orchestration.",
    "Zero ceremony setup.", 
    "Built-in resilience.",
    'Agent("name").run("query") — that\'s it.'
  ],
  
  ctas: [
    { text: "Get Started", href: "#quickstart", variant: "primary" as const },
    { text: "⭐ GitHub", href: site.social.github, variant: "secondary" as const },
    { text: "📦 PyPI", href: site.social.pypi, variant: "secondary" as const },
    { text: "📚 Docs", href: "/docs", variant: "secondary" as const }
  ]
} as const;

export const quickstart = {
  title: "Get started in seconds",
  subtitle: "Install Cogency and build your first agent",
  
  install: {
    command: "pip install cogency",
    description: "Single command installation"
  },
  
  example: {
    title: "example.py",
    code: `from cogency import Agent

agent = Agent("demo")
await agent.run("What's the weather in Tokyo and time there?")

# Automatically:
# 🌤️ weather(Tokyo) → 25°C sunny
# 🕐 time(Tokyo) → 3:47 PM JST
# 🤖 "It's currently 25°C and sunny in Tokyo, 3:47 PM local time"`
  },
  
  features: [
    "🚀 Zero configuration required",
    "🛠️ 15+ built-in tools auto-discovered", 
    "🧠 Adaptive reasoning (fast ↔ deep)",
    "🌊 Streaming execution with full transparency"
  ]
} as const;

export const painPoints = {
  title: "The AI agent problem",
  subtitle: "Most frameworks make simple things complex",
  
  problems: [
    {
      emoji: "🔧",
      title: "Configuration Hell",
      description: "Hours of setup before your first \"Hello World\""
    },
    {
      emoji: "🤖", 
      title: "Brittle Reasoning",
      description: "Agents that break on anything beyond trivial tasks"
    },
    {
      emoji: "🔍",
      title: "No Visibility", 
      description: "Black box execution with zero insight into agent thinking"
    }
  ],
  
  solution: {
    title: "Cogency fixes this",
    description: "Production-ready agents from a single import",
    benefits: [
      "Auto-detects everything from your environment",
      "Scales reasoning complexity automatically", 
      "Stream every thought process in real-time"
    ]
  }
} as const;

export const features = {
  title: "Why developers choose Cogency",
  subtitle: "Developer experience meets powerful AI agents",
  
  grid: [
    {
      title: "Zero Config",
      description: "Auto-detects LLMs, tools, memory from environment",
      emoji: "⚡",
      href: "/features/zero-config",
      icon: "zap"
    },
    {
      title: "Adaptive Reasoning", 
      description: "Thinks fast or deep as needed, switches seamlessly",
      emoji: "🧠",
      href: "/features/multi-step-reasoning", 
      icon: "brain"
    },
    {
      title: "Streaming First",
      description: "Watch agents think in real-time with full transparency", 
      emoji: "🌊",
      href: "/features/streaming",
      icon: "activity"
    },
    {
      title: "Tool Discovery",
      description: "Drop tools in, they auto-register and route intelligently",
      emoji: "🛠️", 
      href: "/features/auto-discovery",
      icon: "tool"
    },
    {
      title: "Production Ready",
      description: "Resilience, rate limiting, metrics, tracing included",
      emoji: "🏗️",
      href: "/features/production-ready",
      icon: "shield"
    },
    {
      title: "Extensible",
      description: "Add tools, memory backends, embedders with zero friction", 
      emoji: "🧩",
      href: "/features/extensibility",
      icon: "puzzle"
    }
  ]
} as const;

export const builtinTools = [
  { name: "Calculator", emoji: "🧮", description: "Mathematical expressions and calculations" },
  { name: "Search", emoji: "🔍", description: "Web search for current information" },
  { name: "Weather", emoji: "🌤️", description: "Current conditions and forecasts" },
  { name: "Files", emoji: "📁", description: "Create, read, edit, list, delete files" },
  { name: "Shell", emoji: "💻", description: "Execute system commands safely" },
  { name: "Code", emoji: "🐍", description: "Python code execution in sandboxed environment" },
  { name: "CSV", emoji: "📊", description: "Data processing and analysis" },
  { name: "SQL", emoji: "🗄️", description: "Database querying and management" },
  { name: "HTTP", emoji: "🌐", description: "Make HTTP requests with JSON parsing" },
  { name: "Time", emoji: "🕒", description: "Date/time operations and timezone conversions" },
  { name: "Scrape", emoji: "🔗", description: "Web scraping with content extraction" },
  { name: "Recall", emoji: "🧠", description: "Memory search and retrieval" }
] as const;

export const meta = {
  defaultTitle: `${site.name} - ${site.tagline}`,
  defaultDescription: "True multi-step reasoning with intelligent tool orchestration. Zero ceremony setup, built-in resilience, production-ready from day one.",
  keywords: "AI agents, ReAct, multi-step reasoning, LLM framework, developer tools",
  ogImage: "/og-image.png"
} as const;

// Type exports for component consumption
export type CTAVariant = typeof hero.ctas[0]['variant'];
export type BadgeVariant = typeof hero.badge.variant;
export type FeatureItem = typeof features.grid[0];
export type ToolItem = typeof builtinTools[0];