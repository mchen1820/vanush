import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class DateType(BaseModel):
    type_name: str
    count: int

class DateResult(BaseAgentResult):
	date: Optional[str] = Field(None)
	relevance: Optional[str] = Field(None)

async def date_check_agent(client: AsyncDedalus, article:str) -> DateResult:
	runner = DedalusRunner(client)
	result = await runner.run(
		input=f""" 

		The article can be found in:
        "{article}"

		Perform a date and relevancy analysis:

		1. Identify the date that the article was published, in the form of January 12, 2020, for example.
		2. Describe the article relevancy by considering the date that the article was published together with the
			subject of the article. For example, an article about an old news event may be highly relevant even if it's
			an old article if it covered the event soon after it happened. However, a scientific article likely needs
			to be newer to reflect scientific advancements/discoveries that have been made between the time of the article
			and present day. Describe the relevancy using one of the following: Very Low Relevance, Low Relevance,
			Moderate Relevance, High Relevance, Very High Relevance
		3. Compute an overall date/relevance score from 0 to 100, with 0 meaning that the the article is not at all
			relevant and outdated and 100 meaning that the article is super relevant and up to date.""",

		model="openai/gpt-4o",
		response_format=DateResult,
		temperature = 0.2
		)
	
	date_result = DateResult.model_validate_json(result.final_output)
	if date_result.date:
		date_result.confidence_score = 100
	else:
		date_result.confidence_score = 0

	return date_result


async def main():
	url = input("Provide URL of academic paper to check date/relevance: ")
	client = AsyncDedalus()
	result = await date_check_agent(client, url)
     
	print("\n Date Check Results")
	print(f"   Overall Score: {result.overall_score}/100")
	print(f"   Confidence: {result.confidence_score}/100")
	
	print(f"   Date: {result.date}")
	print(f"   Relevance: {result.relevance}")
	
	return result

if __name__ == "__main__":
    print("Running date_check.py")
    asyncio.run(main())