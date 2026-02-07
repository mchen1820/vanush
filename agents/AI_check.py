import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import BaseModel, Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv

load_dotenv()


class AIIndicator(BaseModel):
    indicator: str = Field(..., description="Description of the AI-usage indicator found")
    location: str = Field(..., description="Where in the article this was found, e.g. 'introduction', 'methodology', 'throughout'")
    severity: str = Field(..., description="How strongly this suggests AI usage: strong, moderate, or weak")


class AIDetectionResult(BaseAgentResult):
    """Result model for the AI Detection Agent"""
    ai_likelihood_score: float = Field(..., description="0-100 score estimating likelihood the article was AI-generated or AI-assisted")
    classification: str = Field(..., description="One of: likely_human, likely_ai_assisted, likely_ai_generated, uncertain")
    indicators_found: List[AIIndicator] = Field(default_factory=list, description="Specific indicators of AI usage detected")
    stylistic_flags: List[str] = Field(default_factory=list, description="Stylistic patterns typical of AI writing, e.g. repetitive structure, generic hedging")
    human_signals: List[str] = Field(default_factory=list, description="Signals suggesting human authorship, e.g. personal anecdotes, domain-specific jargon, unique voice")
    repetitive_phrases: List[str] = Field(default_factory=list, description="Phrases or patterns that appear suspiciously often")
    vocabulary_diversity: str = Field(..., description="Assessment of vocabulary diversity: high, moderate, or low")
    structural_analysis: str = Field(..., description="Assessment of whether the article structure follows typical AI patterns")
    disclosed_ai_usage: bool = Field(..., description="Whether the article explicitly discloses use of AI tools")
    recommendations: List[str] = Field(default_factory=list, description="Suggestions or observations about AI usage in the article")


async def ai_detection_agent(client: AsyncDedalus, url: str) -> AIDetectionResult:
    """Agent that analyzes an article for signs of AI-generated content"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""Analyze the article at: {url}

        Perform a thorough AI-usage detection analysis:
        1. Assess the overall likelihood that this article was written by AI, assisted by AI, or written entirely by a human.
        2. Look for common AI writing indicators:
           - Overly generic or hedging language ("It's important to note that...", "In conclusion...")
           - Repetitive sentence structures or paragraph patterns
           - Lack of personal voice, anecdotes, or unique perspective
           - Unusually uniform paragraph lengths
           - Perfect grammar with no stylistic quirks
           - Lists and bullet points used excessively
           - Vague or surface-level analysis without deep domain expertise
           - Common AI filler phrases ("delve", "landscape", "multifaceted", "it's worth noting")
        3. Also look for signals of human authorship:
           - Personal experiences or anecdotes
           - Domain-specific jargon used naturally
           - Unique writing voice or style
           - Specific examples from personal knowledge
           - Imperfect but natural sentence structures
           - Cultural or contextual references
        4. Check if the article explicitly discloses AI tool usage.
        5. Analyze vocabulary diversity — is the word choice varied or repetitive?
        6. Analyze the structure — does it follow a formulaic AI pattern?
        7. Identify any repetitive phrases or patterns.
        8. Provide an overall classification and recommendations.
        
        Be balanced and fair. Not all polished writing is AI-generated, and not all
        rough writing is human. Focus on patterns rather than individual sentences.""",
        model="openai/gpt-4o",
        mcp_servers=["firecrawl"],
        response_format=AIDetectionResult,
    )

    ai_result = AIDetectionResult.model_validate_json(result.final_output)

    # Confidence based on how many indicators were found
    total_signals = len(ai_result.indicators_found) + len(ai_result.human_signals)
    if total_signals > 0:
        ai_result.confidence_score = min(total_signals * 10, 100)
    else:
        ai_result.confidence_score = 10.0

    return ai_result


async def main():
    url = input("Provide URL of article to check for AI usage: ")
    client = AsyncDedalus()
    result = await ai_detection_agent(client, url)

    print("\n🤖 AI Detection Results")
    print("=" * 60)
    print(f"\n📊 AI Likelihood: {result.ai_likelihood_score}/100")
    print(f"   Classification: {result.classification}")
    print(f"   Overall Score: {result.overall_score}/100")
    print(f"   Confidence: {result.confidence_score}/100")
    print(f"   AI Disclosed: {'Yes' if result.disclosed_ai_usage else 'No'}")

    print(f"\n🔍 Writing Analysis:")
    print(f"   Vocabulary Diversity: {result.vocabulary_diversity}")
    print(f"   Structure: {result.structural_analysis}")

    if result.indicators_found:
        print(f"\n🚩 AI Indicators Found ({len(result.indicators_found)}):")
        for ind in result.indicators_found:
            print(f"   [{ind.severity.upper()}] {ind.indicator}")
            print(f"      Location: {ind.location}")

    if result.stylistic_flags:
        print(f"\n✍️  Stylistic Flags:")
        for flag in result.stylistic_flags:
            print(f"     • {flag}")

    if result.repetitive_phrases:
        print(f"\n🔁 Repetitive Phrases:")
        for phrase in result.repetitive_phrases:
            print(f"     • \"{phrase}\"")

    if result.human_signals:
        print(f"\n👤 Human Signals ({len(result.human_signals)}):")
        for signal in result.human_signals:
            print(f"     • {signal}")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"     • {rec}")

    print(f"\n📝 Summary: {result.summary}")
    return result


if __name__ == "__main__":
    print("Running ai_detection.py")
    asyncio.run(main())