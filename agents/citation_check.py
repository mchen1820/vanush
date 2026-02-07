import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class CitationType(BaseModel):
    type_name: str
    count: int

class CitationResult(BaseAgentResult):
    """Result model for the Citation Check Agent"""
    total_citations_found: int = Field(...)
    verified_citations: int = Field(...)
    unverified_citations: int = Field(...)
    broken_links: List[str] = Field(default_factory=list)
    citation_types: List[CitationType] = Field(default_factory=list, description="Breakdown of citation types and their counts")
    flagged_citations: List[str] = Field(default_factory=list)
    peer_reviewed_count: int = Field(0)
    self_citation_count: int = Field(0)
    avg_citation_age_years: Optional[float] = Field(None)
    recommendations: List[str] = Field(default_factory=list)


async def citation_check_agent(client: AsyncDedalus, url: str) -> CitationResult:
    """Agent that analyzes citations/references in an academic paper"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""Analyze the citations and references in the academic paper at: {url}

        Perform a thorough citation check:
        1. Count all citations/references in the paper.
        2. Attempt to verify each citation — check if the cited source exists and is accessible.
        3. Identify any broken links or inaccessible sources.
        4. Categorize citations by type (journal article, book, conference paper, web source, etc.).
        5. Flag any citations that appear unreliable, predatory, or questionable.
        6. Count how many citations come from peer-reviewed sources.
        7. Identify any self-citations by the author(s).
        8. Estimate the average age of cited sources.
        9. Provide recommendations for improving the citation quality.""",
        model="openai/gpt-4o",
        mcp_servers=["firecrawl"],
        response_format=CitationResult,
    )
    citation_result = CitationResult.model_validate_json(result.final_output)
    if citation_result.total_citations_found > 0:
        citation_result.confidence_score = citation_result.verified_citations / citation_result.total_citations_found * 100
    else:
        citation_result.confidence_score = 0.0
    return citation_result


# async def main():
#     url = input("Provide URL of academic paper to check citations: ")
#     client = AsyncDedalus()
#     result = await citation_check_agent(client, url)

#     print("\n📚 Citation Check Results")
#     print(f"   Overall Score: {result.overall_score}/100")
#     print(f"   Confidence: {result.confidence_score}/100")
#     print(f"   Total Citations: {result.total_citations_found}")
#     print(f"   Verified: {result.verified_citations} | Unverified: {result.unverified_citations}")
#     print(f"   Peer-Reviewed: {result.peer_reviewed_count}")
#     print(f"   Self-Citations: {result.self_citation_count}")
#     if result.avg_citation_age_years is not None:
#         print(f"   Avg Citation Age: {result.avg_citation_age_years:.1f} years")
#     if result.broken_links:
#         print(f"   ⚠️  Broken Links: {len(result.broken_links)}")
#     if result.flagged_citations:
#         print(f"   🚩 Flagged Citations: {len(result.flagged_citations)}")
#     print(f"\n   Summary: {result.summary}")
#     if result.recommendations:
#         print("\n   Recommendations:")
#         for rec in result.recommendations:
#             print(f"     • {rec}")

#     return result


# if __name__ == "__main__":
#     print("Running citation_check.py")
#     asyncio.run(main())