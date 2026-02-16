Based on this lesson content, generate a quiz with 4 questions to test the learner's understanding.

Lesson content:
{lesson_json}

Difficulty: {difficulty}/5

Generate a mix of question types: multiple_choice, true_false, and short_answer.

Respond ONLY with valid JSON in this exact format:
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "The question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Brief explanation of why this is correct"
    }},
    {{
      "type": "true_false",
      "question": "A true or false statement",
      "correct_answer": "True",
      "explanation": "Brief explanation"
    }},
    {{
      "type": "short_answer",
      "question": "A question requiring a brief text answer",
      "correct_answer": "The expected answer or key concept",
      "explanation": "What a good answer should include"
    }}
  ]
}}

Make questions that test understanding, not just memorization. Include questions of varying difficulty.