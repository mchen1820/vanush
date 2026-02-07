import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import BaseModel, Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv

load_dotenv()


class UsefulQuote(BaseModel):
    quote: str = Field(..., description="A direct quote from the article that is relevant to the topic")
    relevance: str = Field(..., description="Brief explanation of how this quote relates to the topic")
    suggested_use: str = Field(..., description="How the user could use this quote, e.g. 'supporting evidence', 'counterargument', 'background context'")


class UsefulSection(BaseModel):
    section_name: str = Field(..., description="Name or heading of the relevant section")
    relevance_summary: str = Field(..., description="How this section relates to the research topic")
    strength: str = Field(..., description="How useful this section is: highly relevant, moderately relevant, or tangentially relevant")


class UsefulnessResult(BaseAgentResult):
    """Result model for the Usefulness Check Agent"""
    research_topic: str = Field(..., description="The research or essay topic being evaluated against")
    alignment_score: float = Field(..., description="0-100 score for how well the article aligns with the topic")
    useful_quotes: List[UsefulQuote] = Field(default_factory=list, description="Key quotes from the article relevant to the topic")
    useful_sections: List[UsefulSection] = Field(default_factory=list, description="Sections of the article most relevant to the topic")
    key_arguments: List[str] = Field(default_factory=list, description="Key arguments from the article that relate to the topic")
    counterarguments: List[str] = Field(default_factory=list, description="Arguments in the article that could serve as counterpoints")
    gaps: List[str] = Field(default_factory=list, description="Aspects of the research topic NOT covered by this article")
    suggested_role: str = Field(..., description="How this article best fits into the research, e.g. 'primary source', 'background reading', 'counterargument', 'methodological reference', 'not useful'")
    related_topics: List[str] = Field(default_factory=list, description="Related topics or keywords from the article that could help find more sources")
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for how to use this article in the research")


async def usefulness_check_agent(client: AsyncDedalus, url: str, research_topic: str) -> UsefulnessResult:
    """Agent that evaluates how useful an article is for a given research topic"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""Analyze the article at: {url}

        The user is researching the following topic:
        "{research_topic}"

        Evaluate how useful this article is for their research:
        1. Assess overall alignment between the article content and the research topic.
        2. Extract the most useful direct quotes that relate to the topic. For each quote,
           explain its relevance and how it could be used (supporting evidence, counterargument,
           background context, etc.).
        3. Identify the most relevant sections of the article and summarize their usefulness.
        4. Extract key arguments from the article that relate to the research topic.
        5. Identify any counterarguments or opposing viewpoints that could be valuable.
        6. Identify gaps — what aspects of the research topic does this article NOT cover?
        7. Determine the best role for this article in the research (primary source, background
           reading, counterargument, methodological reference, or not useful).
        8. Suggest related topics or keywords from the article that could help find additional sources.
        9. Provide practical recommendations for how to use this article in their research.
        
        Be honest. If the article is only tangentially related or not useful, say so clearly.
        Focus on actionable insights the researcher can use.""",
        model="openai/gpt-4o",
        mcp_servers=["firecrawl"],
        response_format=UsefulnessResult,
    )

    usefulness_result = UsefulnessResult.model_validate_json(result.final_output)

    # Confidence based on how much useful content was actually found
    total_useful = len(usefulness_result.useful_quotes) + len(usefulness_result.useful_sections) + len(usefulness_result.key_arguments)
    if total_useful > 0:
        usefulness_result.confidence_score = min(total_useful * 8, 100)
    else:
        usefulness_result.confidence_score = 10.0

    return usefulness_result


async def main():
    url = input("Provide URL of article to evaluate: ")
    research_topic = input("What is your research/essay topic? ")
    client = AsyncDedalus()
    result = await usefulness_check_agent(client, url, research_topic)

    print("\n📖 Usefulness Check Results")
    print("=" * 60)
    print(f"\n🎯 Research Topic: {result.research_topic}")
    print(f"   Alignment Score: {result.alignment_score}/100")
    print(f"   Overall Score: {result.overall_score}/100")
    print(f"   Confidence: {result.confidence_score}/100")
    print(f"   Suggested Role: {result.suggested_role}")

    if result.useful_quotes:
        print(f"\n💬 Useful Quotes ({len(result.useful_quotes)}):")
        for i, q in enumerate(result.useful_quotes, 1):
            print(f"   {i}. \"{q.quote}\"")
            print(f"      Relevance: {q.relevance}")
            print(f"      Use as: {q.suggested_use}")

    if result.useful_sections:
        print(f"\n📑 Relevant Sections ({len(result.useful_sections)}):")
        for sec in result.useful_sections:
            print(f"   [{sec.strength.upper()}] {sec.section_name}")
            print(f"      {sec.relevance_summary}")

    if result.key_arguments:
        print(f"\n🗂️  Key Arguments:")
        for arg in result.key_arguments:
            print(f"     • {arg}")

    if result.counterarguments:
        print(f"\n⚖️  Counterarguments:")
        for ca in result.counterarguments:
            print(f"     • {ca}")

    if result.gaps:
        print(f"\n⚠️  Gaps (not covered by this article):")
        for gap in result.gaps:
            print(f"     • {gap}")

    if result.related_topics:
        print(f"\n🔗 Related Topics to Search:")
        print(f"     {', '.join(result.related_topics)}")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"     • {rec}")

    print(f"\n📝 Summary: {result.summary}")
    return result


if __name__ == "__main__":
    print("Running usefulness_check.py")
    asyncio.run(main())