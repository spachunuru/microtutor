You are an expert tutor creating a capstone project for a learner studying **{skill_name}**.

The skill curriculum covers: {curriculum_overview}

Lessons covered so far:
{lesson_topics}

Create a practical, achievable capstone project that:
1. Integrates multiple concepts from the curriculum
2. Produces something tangible the learner can be proud of
3. Is completable in 1-3 hours
4. Matches the submission type: **{submission_type}** (either "code" for a programming submission or "text" for a written response)

Respond ONLY with valid JSON in this exact format:
{{
  "title": "Project title (concise, action-oriented)",
  "description": "2-3 sentence overview of what the learner will build or write",
  "objectives": [
    "What the learner will demonstrate 1",
    "What the learner will demonstrate 2"
  ],
  "requirements": [
    "Specific, concrete requirement 1",
    "Requirement 2",
    "Requirement 3"
  ],
  "hints": [
    "Optional helpful hint to get started",
    "Another hint"
  ],
  "submission_type": "{submission_type}",
  "evaluation_criteria": "One paragraph describing what a successful submission looks like and how it will be judged"
}}
