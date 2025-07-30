/**
 * Feature page content
 * Clean Astro content management for feature pages
 */

export const features = {
  'zero-config': {
    badge: '⚡ Zero Configuration',
    badgeColor: 'border-blue-500/20 bg-blue-500/10 text-blue-400',
    title: 'AI Agents in',
    titleGradient: 'from-white via-blue-100 to-blue-200',
    subtitle: 'That Actually Work',
    description: 'No complex configurations. No verbose setup files. No learning curves. Just pure, productive AI agent development from line one.',
    ctaText: 'See the Code',
    ctaColor: 'bg-blue-600 hover:bg-blue-500 focus:ring-blue-500/50',
    theme: 'blue' as const
  },
  
  'multi-step-reasoning': {
    badge: '🧠 Multi-step Reasoning',
    badgeColor: 'border-orange-500/20 bg-orange-500/10 text-orange-400',
    title: 'Agents that',
    titleGradient: 'from-white via-orange-100 to-orange-200', 
    subtitle: 'think step-by-step',
    description: 'Built-in plan → reason → act → reflect → respond cognitive loop. Create AI agents that break down complex problems systematically.',
    ctaText: 'See the Loop',
    ctaColor: 'bg-orange-600 hover:bg-orange-500 focus:ring-orange-500/50',
    theme: 'orange' as const
  },
  
  'extensibility': {
    badge: '🔧 Highly Extensible',
    badgeColor: 'border-cyan-500/20 bg-cyan-500/10 text-cyan-400',
    title: 'Unlimited',
    titleGradient: 'from-white via-cyan-100 to-cyan-200',
    subtitle: 'customization', 
    description: 'Extend every aspect of Cogency. Build custom tools, override reasoning steps, create specialized agents—all with the same zero-config simplicity.',
    ctaText: 'See Extensions',
    ctaColor: 'bg-cyan-600 hover:bg-cyan-500 focus:ring-cyan-500/50',
    theme: 'cyan' as const
  },
  
  'streaming': {
    badge: '🌊 Streaming First',
    badgeColor: 'border-purple-500/20 bg-purple-500/10 text-purple-400',
    title: 'Watch agents',
    titleGradient: 'from-white via-purple-100 to-purple-200',
    subtitle: 'think in real-time',
    description: 'Full transparency into agent reasoning with real-time streaming. See every tool call, decision point, and thought process as it happens.',
    ctaText: 'See Streaming',
    ctaColor: 'bg-purple-600 hover:bg-purple-500 focus:ring-purple-500/50', 
    theme: 'purple' as const
  },
  
  'production-ready': {
    badge: '🏗️ Production Ready',
    badgeColor: 'border-green-500/20 bg-green-500/10 text-green-400',
    title: 'Enterprise-grade',
    titleGradient: 'from-white via-green-100 to-green-200',
    subtitle: 'reliability',
    description: 'Built-in resilience, rate limiting, metrics, and tracing. Scale from prototype to production without architectural changes.',
    ctaText: 'See Features',
    ctaColor: 'bg-green-600 hover:bg-green-500 focus:ring-green-500/50',
    theme: 'green' as const
  },
  
  'auto-discovery': {
    badge: '🛠️ Auto Discovery',
    badgeColor: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400',
    title: 'Tools that',
    titleGradient: 'from-white via-emerald-100 to-emerald-200',
    subtitle: 'just work',
    description: 'Drop tools in, they auto-register and route intelligently. No manifests, no configuration, no ceremony—just intelligent tool orchestration.',
    ctaText: 'See Tools',
    ctaColor: 'bg-emerald-600 hover:bg-emerald-500 focus:ring-emerald-500/50',
    theme: 'green' as const
  }
} as const;

export type FeatureName = keyof typeof features;
export type FeatureContent = typeof features[FeatureName];