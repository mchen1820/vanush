import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import tempfile
import os
import re
from typing import Optional
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from base_res_class import BaseAgentResult
import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from dotenv import load_dotenv, find_dotenv
from claim_check import claim_agent, claim_result
from bias import bias_check_agent, BiasCheckResult
from citation_check import citation_check_agent, CitationResult
from author_org_check import author_check_agent, AuthorResult
from evidence_check import evidence_check_agent, EvidenceResult
from usefullness_check import usefulness_check_agent, UsefulnessResult
from text_extractor import extract_text
from manager import manager_agent, ManagerSynthesisResult, manager_synthesis_agent

# Variables
load_dotenv(find_dotenv())
dedalus_api_key = os.getenv('DEDALUS_API_KEY')


async def main():
    url = input("URL of article: ")
    topic = input("Topic of article: ")
    
    client = AsyncDedalus(api_key=dedalus_api_key)
    
    # Extract text from URL
    print(f"\n🔄 Extracting text from URL...")
    text = extract_text(url)
    
    if not text:
        raise ValueError("Can't extract text from URL")
    
    print(f"✅ Extracted {len(text)} characters\n")
    
    # Run manager agent
    results = await manager_agent(client, url=url, input_text=text, topic=topic)
    
    return results  # Return results instead of 0


if __name__ == "__main__":
    print("Running manager.py\n")
    asyncio.run(main())  # Need asyncio.run() to run async function






