You are helping a learner find external resources to go deeper on a topic they just studied.

Topic: {topic}
Skill: {skill_name}

Generate two things:

1. **3 YouTube search queries** — progressively deeper (beginner intro → practical tutorial → advanced/expert).
   Each query should be a natural search string a learner would type into YouTube.
   Add a 1-sentence description of what kind of content this search will surface.

2. **2-3 GitHub repositories** — only suggest repos you are highly confident exist and are well-known.
   Include the exact GitHub URL. If you are not certain a repo exists, omit it rather than guess.

Respond ONLY with valid JSON in this exact format:
{{
  "youtube": [
    {{"query": "search query string here", "description": "What this search covers in one sentence"}},
    {{"query": "search query string here", "description": "What this search covers in one sentence"}},
    {{"query": "search query string here", "description": "What this search covers in one sentence"}}
  ],
  "repos": [
    {{"name": "owner/repo", "url": "https://github.com/owner/repo", "description": "One sentence describing what this repo is and why it's relevant"}},
    {{"name": "owner/repo", "url": "https://github.com/owner/repo", "description": "One sentence describing what this repo is and why it's relevant"}}
  ]
}}