You are helping a learner find external resources to go deeper on a topic they just studied.

Topic: {topic}
Skill: {skill_name}

Generate two things:

1. **3 YouTube search queries** — progressively deeper (beginner intro → practical tutorial → advanced/expert).
   Each query should be a natural search string a learner would type into YouTube.
   Add a 1-sentence description of what kind of content this search will surface.

2. **2-3 GitHub repositories** with sample implementations or example code for this topic.
   Prefer: tutorial repos, starter templates, official examples, or example projects with real runnable code.
   Only include repos you are highly confident exist. Include the exact GitHub URL.
   Add a "language" field for the primary programming language (e.g. "Python", "JavaScript") if known.

Respond ONLY with valid JSON in this exact format:
{{
  "youtube": [
    {{"query": "search query string here", "description": "What this search covers in one sentence"}},
    {{"query": "search query string here", "description": "What this search covers in one sentence"}},
    {{"query": "search query string here", "description": "What this search covers in one sentence"}}
  ],
  "repos": [
    {{"name": "owner/repo", "url": "https://github.com/owner/repo", "language": "Python", "description": "One sentence on why this repo helps learn this topic"}},
    {{"name": "owner/repo", "url": "https://github.com/owner/repo", "language": "JavaScript", "description": "One sentence on why this repo helps learn this topic"}}
  ]
}}
