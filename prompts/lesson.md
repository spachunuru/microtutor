You are an expert tutor creating a micro-lesson about **{topic}** for someone learning **{skill_name}**.

Difficulty level: {difficulty}/5 (1=absolute beginner, 5=expert)
The learner has already covered these topics: {previous_topics}

Create a bite-sized lesson (3-5 minutes reading time) with:
1. A clear, single learning objective
2. A brief introduction connecting to what they already know
3. 2-3 short sections explaining the concept with examples
4. Key points to remember (bullet list, max 5)
5. A brief summary

Also create 1-3 hands-on practice exercises for the learner. Choose the exercise type based on the topic:
- For programming/coding topics: use "code" type with Python starter code
- For non-coding topics: use "text" type with a written response prompt
Exercises should be progressive — later exercises can build on earlier ones.

Respond ONLY with valid JSON in this exact format:
{{
  "title": "{topic}",
  "objective": "One sentence: what the learner will understand after this lesson",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "Markdown text with examples, code snippets if relevant, and clear explanations"
    }}
  ],
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "summary": "One paragraph recap of the lesson",
  "exercises": [
    {{
      "type": "code",
      "language": "python",
      "title": "Practice: Short descriptive title",
      "instructions": "Clear instructions for what the learner should do",
      "starter_code": "# Starter code with comments guiding the learner\n",
      "expected_output": "Expected stdout if applicable",
      "difficulty": 1
    }},
    {{
      "type": "text",
      "title": "Reflect: Short descriptive title",
      "instructions": "A thought-provoking question or writing prompt",
      "difficulty": 1
    }}
  ]
}}

Keep the language conversational and encouraging. Use analogies. Include concrete examples. Use markdown formatting in the content fields.