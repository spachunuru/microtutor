Create a structured learning curriculum for someone who wants to learn **{skill_name}**.

Difficulty level: {difficulty}

Generate a curriculum with 8-12 topics that progress from foundational to more advanced concepts. Each topic should be a single, focused micro-lesson that can be completed in 3-5 minutes.

Respond ONLY with valid JSON in this exact format:
{{
  "name": "{skill_name}",
  "description": "A one-sentence description of what the learner will achieve",
  "topics": [
    {{
      "title": "Topic title",
      "objective": "One sentence: what the learner will understand after this lesson"
    }}
  ]
}}

Make the topics practical and engaging. Start with the basics and build up. Include hands-on examples where possible.