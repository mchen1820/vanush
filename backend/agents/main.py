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
from date_check import date_check_agent, DateResult
from text_extractor import extract_text
from manager import manager_agent, ManagerSynthesisResult, manager_synthesis_agent


dedalus_api_key = os.getenv('DEDALUS_API_KEY')

async def main():
    url = input("URL of article: ")
    topic = input("Topic of article: ")
    
    client = AsyncDedalus(api_key=dedalus_api_key)
    
    print(f"\nExtracting text from URL...")
    text = extract_text(url)
    
    if not text:
        print("\nCould not extract article text from this URL.")
        print("Try one of these and run again:")
        print("1. Use a different version of the paper URL (pdf/pdfdirect/full page).")
        print("2. Open the link in your browser and copy the final redirected URL.")
        print("3. Download the PDF in browser, then pass the local PDF path as the URL input.")
        print("4. Test a known-open URL (for example arXiv or Wikipedia) to confirm your setup.")
        return None
    
    print(f"Extracted {len(text)} characters\n")
    
    results = await manager_agent(client, input_text=text, topic=topic)

    print("\n" + "="*60)
    print("DETAILED AGENT RESULTS")
    print("="*60)
    
    print(f"\nCentral Claim: {results['claim'].central_claim}")
    print(f"   Summary: {results['claim'].summary}")
    
    print(f"\nCitation Analysis: {results['citations'].summary}")
    print(f"   Score: {results['citations'].overall_score}/100")
    
    print(f"\nBias Analysis: {results['bias'].summary}")
    print(f"   Score: {results['bias'].overall_score}/100")
    
    print(f"\nAuthor/Org Analysis: {results['author'].summary}")
    print(f"   Score: {results['author'].overall_score}/100")
    print(f"\n Related Links : {results['author'].related_links}")
    
    print(f"\nEvidence Analysis: {results['evidence'].summary}")
    print(f"   Score: {results['evidence'].overall_score}/100")
    
    print(f"\nUsefulness Analysis: {results['usefulness'].summary}")
    print(f"   Score: {results['usefulness'].overall_score}/100")

    print(f"\nDate and Relevance Analysis: {results['date'].summary}")
    print(f" Relevance: {results['date'].relevance}")
    print(f" Score: {results['date'].overall_score}")
    

    
    synthesis = results['synthesis']
    print("\n" + "="*60)
    print(" MANAGER'S FINAL SYNTHESIS")
    print("="*60)
    
    print(f"\n Overall Credibility Score: {synthesis.overall_credibility_score}/100")
    print(f"   Recommendation: {synthesis.recommendation}")
    
    print(f"\n Final Verdict:")
    print(f"   {synthesis.final_verdict}")
    
    print(f"\n Key Findings:")
    for i, finding in enumerate(synthesis.key_findings, 1):
        print(f"   {i}. {finding}")
    
    if synthesis.red_flags:
        print(f"\n Red Flags:")
        for i, flag in enumerate(synthesis.red_flags, 1):
            print(f"   {i}. {flag}")
    
    if synthesis.strengths:
        print(f"\n Strengths:")
        for i, strength in enumerate(synthesis.strengths, 1):
            print(f"   {i}. {strength}")
    
    print(f"\n Executive Summary:")
    print(f"   {synthesis.summary}")
    

    
    return results  # Return results instead of 0


if __name__ == "__main__":
    print("Running manager.py\n")
    asyncio.run(main())  # Need asyncio.run() to run async function




