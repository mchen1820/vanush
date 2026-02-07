from pydantic import BaseModel, Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from dotenv import load_dotenv, find_dotenv

# Variables
load_dotenv(find_dotenv())
dedalus_api_key = os.getenv('DEDALUS_API_KEY')

class claim_result(BaseAgentResult):
    central_claim: str = Field(..., description="One sentence claim that captures the main point of the article")

async def claim_agent(client, url: str) -> claim_result:
    """Agent to analyze a URL and return the central claim"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""Analyze the following URL for the following information: {url}
        Pretend that you are a journalist who has just read the article. What is the central claim of the article?
        1. Extract the central claim of the webpage in one two to sentences. 
            Store this information in the central claim field of the result object.
            Format your response in markdown with clear sections.
            IMPORTANT: Provide ONLY the central claim. Do not include any 
            conversational elements like "Is there anything else you need?" or 
            "Let me know if you have questions." Just provide the pure central claim.
        2. Also summarize the main content and purpose of the webpage in a short succinct summary. 
           Store this information in the summary field of the result object.
        3. Based on this, also generate a confidence score and overall score for the central claim. 
           For confidence, rate how confident you are that the central claim 
           is accurate based on the information in the article.
           If the central claim was easy to understand, rate it higher. 
           If the central claim was muddled and you didn't really understand it, it hard to read, understand, etc. 
           Or can't access it, rate it lower.
           For overall score, just rate it None. it is not necessary.
        """,
        model="openai/gpt-4o",
        mcp_servers=["firecrawl", "tsion/sequential-thinking"],
        response_format=claim_result
    )
    
    # Parse the JSON output into your Pydantic model
    return claim_result.model_validate_json(result.final_output)

# async def main():
#     url = input("Provide URL to analyze: ")
#     client = AsyncDedalus()
    
#     # Run the agent
#     result = await claim_agent(client, url)  
    
#     # Print results in clean format
#     print("Claim Analysis Results")
#     print(f"\n📍 Central Claim:")
#     print(f"   {result.central_claim}")
#     print(f" Summary:")
#     print(f"   {result.summary}")
#     print(f" Scores:")
#     print(f"   Overall Score: {result.overall_score}/100")
#     print(f"   Confidence Score: {result.confidence_score}/100")
    
#     return result

# if __name__ == "__main__":
#     print("Running claim_check.py")
#     asyncio.run(main())