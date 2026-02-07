import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from typing import List, Optional
from pydantic import BaseModel, Field
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv


load_dotenv()

class BiasCheckResult(BaseAgentResult):
    """Result model for the Bias Check Agent"""
    dominant_tone: str = Field(..., description="Dominant tone of the article")
    key_indicators: List[str] = Field(default_factory=list)
    affected_topics: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    bias_level: str = Field(..., description="Human-readable bias level (Low, Moderate, High)")

async def bias_check_agent(client: AsyncDedalus, article:str) -> BiasCheckResult:
    """Agent that analyzes linguistic bias in an article"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f""" 

      The article can be found in:
        "{article}"

Perform a structured bias analysis using ONLY the article text.
Do NOT fact-check.
Do NOT assess factual accuracy.
Do NOT speculate beyond what is written.

Follow these steps exactly:

1. Identify the dominant tone of the article, taking into account any emotionally loaded language.
   - Choose the most fitting tone (e.g., neutral, persuasive, critical, alarmist, dismissive).

2. Identify any key bias indicators in the form of quotes from the article that demonstrate bias by implying judgment, approval, moral positioning, etc.

3. Identify affected topics that the article may demonstrate bias towards. For example, if the author is biased towards
      favoring a particular political party, team, etc.

4. Compute an overall bias score from 0 to 100 using this logic:
   - Start from a baseline of 100
   - Decrease the score based on:
     • Frequency of biased wording
     • Strength of emotionally loaded language
     • Degree of persuasive framing
     • Lack of balance or counterpoints
   - Lower scores indicate stronger linguistic bias

5. Assign a bias level label based on the score:
   - 0–20: Very High Bias
   - 21–40: High Bias
   - 41–60: Moderate Bias
   - 61–80: Low Bias
   - 81–100: Very Low Bias

6. Calculate a confidence score (0–100) using the following process:

   a. Start from a baseline confidence of 50.

   b. Add confidence points based on evidence clarity:
      - +10 if the article contains clear, repeated examples of biased wording
      - +10 if bias indicators are consistent throughout the article
      - +10 if the article is long enough to allow robust analysis

   c. Subtract confidence points for uncertainty:
      - -10 if the article is very short or lacks sufficient text
      - -10 if bias indicators are subtle, ambiguous, or isolated
      - -10 if tone varies significantly across sections
      - -10 if language is largely neutral with only minor indicators

   d. Clamp the final confidence score between 0 and 100.

   IMPORTANT:
   - Confidence should be LOW when evidence is sparse or ambiguous
   - Confidence should be HIGH only when indicators are frequent and clear

7. Provide brief, practical recommendations for improving neutrality, if applicable.

Output requirements:
- Provide ONLY the analysis content
- No conversational language
- No questions or follow-ups
- Be concise, clear, and readable for a general audience
- Ensure internal consistency between the bias score, bias level, and explanation

In your summary, act like you are a professor reviewing this article for bias and credibility.
Act like its part of a grade review with your student. """,

        model="openai/gpt-4o",
        response_format=BiasCheckResult,
        temperature = 0.2
    )

    return BiasCheckResult.model_validate_json(result.final_output)
