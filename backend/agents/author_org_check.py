import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class AuthorType(BaseModel):
    type_name: str
    count: int

class AuthorResult(BaseAgentResult):
    author_name: Optional[str] = Field(None)
    organization: Optional[str] = Field(None)
    related_links: List[str] = Field(
        default_factory=list,  # Add this!
        description="URLs of 2-3 highly related articles found via web search"
    )
    total_articles_found: int = Field(...)
    publication_types: List[AuthorType] = Field(
        default_factory=list,
        description="Breakdown of publication types and counts"
    )
    notable_publications: List[str] = Field(default_factory=list)
    expertise_alignment_score: int = Field(
        None, 
        description="Estimated score on a 0-100 scale of how well the author's background matches the article topic"
    )
    reliability_score_estimate: Optional[int] = Field(
        None, 
        description="Estimated reliability on a 0-100 scale"
    )
    bias_indicators: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


async def author_check_agent(client: AsyncDedalus, article:str, central_claim, topic) -> AuthorResult:
	runner = DedalusRunner(client)
	result = await runner.run(
    input=f""" 
        The article can be found in:
        "{article}"


        
        Perform a thorough author credibility analysis:
        1. Identify the author(s) of the article.
        2. Identify any affiliated organization, publication, or institution.
        3. Estimate how many articles or publications the author has written.
        4. Categorize the types of publications (news articles, academic papers, opinion pieces, reports, etc.).
        5. List some of the author's notable publications.
        6. Evaluate the author's relevant expertise and background with respect to the article topic.
        7. Evaluate the reliability of the author and organization based on reputation, past work, and transparency.
        8. Identify potential bias indicators, advocacy positions, or ideological framing.
        9. Provide recommendations for reliable articles with similar topics
        10. Compute an overall author/organization score from 0 to 100.
        
        **IMPORTANT**: Use  "tsion/exa to find 3 highly related articles to {central_claim}
		and {topic}

        Store the complete URLs in the 'related_links' field. CHECK TO ENSURE THAT You are not returning 
		links for the same article. DO NOT return links to sources that are by the same author.
		
        
        In your summary, act like you are a professor reviewing this article for author credibility.
        """,
    model="openai/gpt-4o",
    response_format=AuthorResult,
	mcp_servers=["tsion/exa", ],  # Privacy-focused web search]
    temperature=0.2
)
		
	
	
	author_result = AuthorResult.model_validate_json(result.final_output)
	author_result.confidence_score = author_result.expertise_alignment_score - 10 * len(author_result.bias_indicators)

	return author_result


async def main():
	url = input("Provide URL of academic paper to check citations: ")
	client = AsyncDedalus()
	result = await author_check_agent(client, url)
     
	print("\n Author Check Results")
	print(f"   Overall Score: {result.overall_score}/100")
	print(f"   Confidence: {result.confidence_score}/100")
	
	if result.expertise_alignment_score:
		print(f"	Expertise Alignment: {result.expertise_alignment_score}")

	if result.author_name:
		print(f"   Author: {result.author_name}")
	if result.organization:
		print(f"   Organization: {result.organization}")

	if result.related_links:
		print(f" related_links:{result.related_links} ")

	print(f"   Total Articles Found: {result.total_articles_found}")

	if result.reliability_score_estimate is not None:
		print(f"   Estimated Reliability: {result.reliability_score_estimate}/100")

	if result.bias_indicators:
		print(f"   Bias Indicators: {len(result.bias_indicators)}")

	print(f"\n   Summary: {result.summary}")

	if result.recommendations:
		print("\n   Recommendations:")
		for rec in result.recommendations:
			print(f"     • {rec}")

	return result

if __name__ == "__main__":
    print("Running author_org_check.py")
    asyncio.run(main())