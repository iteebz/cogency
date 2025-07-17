# Cogency Examples - Target Trace Format

This document shows the EXACT trace format all examples should match.

## Simple Query (no tools needed)
```
👤 HUMAN: Hello! Tell me about yourself.

🛠️ TOOLING: No tools needed for self-description

🧠 REASON: Direct identity question - can answer from training data
⚡️ ACT: Composing self-description

🤖 AGENT: Hello! I am Claude Sonnet 4, an AI assistant...
```

## Tool Query (single step)
```
👤 HUMAN: What's the weather in Tokyo?

🛠️ TOOLING: web_search

🧠 REASON: Need current weather - no cached data available
⚡️ ACT: web_search("Tokyo weather current temperature")
👀 OBSERVE: 23°C, partly cloudy, humidity 65%

🧠 REASON: Have complete weather data for Tokyo
⚡️ ACT: Formatting weather response

🤖 AGENT: The weather in Tokyo is currently 23°C and partly cloudy...
```

## Multistep Query (complex)
```
👤 HUMAN: Plan a 3-day Tokyo itinerary with weather considerations.

🛠️ TOOLING: web_search, travel_info, weather_forecast

🧠 REASON: Need weather forecast to plan outdoor vs indoor activities
⚡️ ACT: weather_forecast("Tokyo 3 days")
👀 OBSERVE: Day 1: sunny 25°C, Day 2: rain 18°C, Day 3: cloudy 22°C

🧠 REASON: Day 2 rain affects outdoor plans - need indoor alternatives
⚡️ ACT: travel_info("Tokyo indoor attractions museums")
👀 OBSERVE: TeamLab, Tokyo National Museum, Senso-ji Temple (covered)

🧠 REASON: Have weather + indoor options - can create complete itinerary
⚡️ ACT: Composing 3-day plan with weather-appropriate activities

🤖 AGENT: Here's your 3-day Tokyo itinerary:
Day 1 (Sunny): Shibuya, Harajuku, Meiji Shrine...
```

## KEY PRINCIPLES
1. **Specific content** - "23°C, partly cloudy" not "Successfully gathered data"
2. **Actionable reasoning** - "Day 2 rain affects outdoor plans" not "Analyzing available information"
3. **Collapse trivial steps** - If no meaningful intermediate work, skip REASON/ACT cycles
4. **Tool calls show actual parameters** - `web_search("Tokyo weather current temperature")` not "Executing tools"
5. **Observations contain real data** - What the tool actually returned
6. **Concise tooling** - `🛠️ TOOLING: web_search` not "Selected web_search"
7. **Skip redundant memorize** - Only show `💾 MEMORIZE:` when actually memorizing something