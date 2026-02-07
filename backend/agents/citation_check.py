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
    return CitationResult.model_validate_json(result.final_output)