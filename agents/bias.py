import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from typing import List, Optional
from pydantic import BaseModel, Field
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv


load_dotenv()

class BiasIndicator(BaseModel):
    """Specific wording or framing indicators contributing to bias"""
    example_text: str
    indicator_type: str  # e.g. "emotionally loaded", "persuasive framing", "selective emphasis"

class BiasCheckResult(BaseAgentResult):
    """Result model for the Bias Check Agent"""
    dominant_tone: str = Field(..., description="Dominant tone of the article")
    bias_level: str = Field(..., description="Human-readable bias level (Low, Moderate, High)")
    key_indicators: List[BiasIndicator] = Field(default_factory=list)
    affected_topics: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

async def bias_check_agent(client: AsyncDedalus, url: str) -> BiasCheckResult:
    """Agent that analyzes linguistic bias in an article"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""
Analyze the article at the following URL for linguistic bias:
{url}


Perform a structured bias analysis using ONLY the article text.
Do NOT fact-check.
Do NOT assess factual accuracy.
Do NOT speculate beyond what is written.

Follow these steps exactly:

1. Identify emotionally loaded or value-laden language.
   - Count distinct instances where wording implies judgment, approval, fear, or moral positioning.

2. Identify persuasive or opinionated framing.
   - Look for rhetorical devices such as contrastive framing, selective emphasis, or implied conclusions.

3. Identify indicators of author preference or alignment.
   - Note language that favors or disfavors specific groups, ideologies, or outcomes.

4. Assess balance of presentation.
   - Determine whether multiple perspectives are presented neutrally, selectively, or not at all.

5. Determine the dominant tone of the article.
   - Choose the most fitting tone (e.g., neutral, persuasive, critical, alarmist, dismissive).

6. Compute an overall bias score from 0 to 100 using this logic:
   - Start from a baseline of 0
   - Increase the score based on:
     • Frequency of biased wording
     • Strength of emotionally loaded language
     • Degree of persuasive framing
     • Lack of balance or counterpoints
   - Higher scores indicate stronger linguistic bias

7. Assign a bias level label based on the score:
   - 0–20: Very Low Bias
   - 21–40: Low Bias
   - 41–60: Moderate Bias
   - 61–80: High Bias
   - 81–100: Very High Bias

8. Calculate a confidence score (0–100) using the following process:

   a. Start from a baseline confidence of 50.

   b. Add confidence points based on evidence clarity:
      - +10 if the article contains clear, repeated examples of biased wording
      - +10 if bias indicators are consistent throughout the article
      - +10 if the article is long enough to allow robust analysis

   c. Subtract confidence points for uncertainty:
      - −10 if the article is very short or lacks sufficient text
      - −10 if bias indicators are subtle, ambiguous, or isolated
      - −10 if tone varies significantly across sections
      - −10 if language is largely neutral with only minor indicators

   d. Clamp the final confidence score between 0 and 100.

   IMPORTANT:
   - Confidence should be LOW when evidence is sparse or ambiguous
   - Confidence should be HIGH only when indicators are frequent and clear

9. Provide brief, practical recommendations for improving neutrality, if applicable.

Output requirements:
- Provide ONLY the analysis content
- No conversational language
- No questions or follow-ups
- Be concise, clear, and readable for a general audience
- Ensure internal consistency between the bias score, bias level, and explanation
""",
        model="openai/gpt-4o",
        mcp_servers=["firecrawl"],
        response_format=BiasCheckResult,
    )

    return BiasCheckResult.model_validate_json(result.final_output)

# async def main():
#     url = input("Provide URL to analyze for bias: ")
#     client = AsyncDedalus()
#     result = await bias_check_agent(client, url)

#     print("\n🧭 Bias Check Results")
#     print(f"   Overall Bias Score: {result.overall_score}/100")
#     print(f"   Bias Level: {result.bias_level}")
#     print(f"   Dominant Tone: {result.dominant_tone}")
#     print(f"   Confidence: {result.confidence_score}/100")
#     print(f"\n   Summary: {result.summary}")

#     if result.key_indicators:
#         print("\n   Key Bias Indicators:")
#         for ind in result.key_indicators:
#             print(f"     • [{ind.indicator_type}] {ind.example_text}")

#     if result.affected_topics:
#         print("\n   Affected Topics:")
#         for topic in result.affected_topics:
#             print(f"     • {topic}")

#     if result.recommendations:
#         print("\n   Recommendations:")
#         for rec in result.recommendations:
#             print(f"     • {rec}")

#     return result

# if __name__ == "__main__":
#     print("Running bias_check.py")
#     asyncio.run(main())
