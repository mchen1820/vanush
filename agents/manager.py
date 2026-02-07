from pydantic import BaseModel, Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from dotenv import load_dotenv, find_dotenv
from claim_check import claim_agent, claim_result
from bias import bias_check_agent, BiasCheckResult
from citation_check import citation_check_agent, CitationResult
from base_res_class import BaseAgentResult

# Variables
load_dotenv(find_dotenv())
dedalus_api_key = os.getenv('DEDALUS_API_KEY')

async def manager_agent(client, url: str) -> List[BaseAgentResult]:
    """Manager agent to coordinate multiple analysis agents"""
    # Run claim check agent
    claim_res, citation_res, bias_res = await asyncio.gather(
        claim_agent(client, url),
        citation_check_agent(client, url),
        bias_check_agent(client, url)
    )
    
    # Compile results into a list
    results = [claim_result, bias_res, citation_res]
    
    return results


async def main():
    url = input("Provide URL to analyze: ")
    client = AsyncDedalus(api_key=dedalus_api_key)
    
    # Run the manager agent
    results = await manager_agent(client, url)  
    
    # Print results in clean format
    print(f"Claim: {results[0].central_claim}")
    print(f"Citations: {results[1].total_citations_found} citations found, {results[1].verified_citations} verified")
    print(f"Accuracy: {results[2].bias_level} bias level, dominant tone: {results[2].dominant_tone}, {results[2].summary} summary")


if __name__ == "__main__":
    print("Running manager.py")
    asyncio.run(main())
   