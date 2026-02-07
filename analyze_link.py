#pip install dedalus_labs, 
#pip install python-dotenv and add api key to .env. add .env to gitignore
#imports 
import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from dotenv import load_dotenv

#variables
load_dotenv()
dedalus_api_key = os.getenv('DEDALUS_API_KEY')

async def analyze_agent(client, url) -> str:
    """Agent to analyze a URL and return structured analysis"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""Analyze the following URL: {url}
        
        1. Summarize the main content and purpose of the webpage.
        2. Identify any key entities (people, organizations, products) mentioned.
        3. Extract any relevant data or statistics provided on the page.
        4. Assess the credibility of the information based on sources cited.
        5. Provide a concise summary of your findings.
        
        Format your response in markdown with clear sections.
        
        IMPORTANT: Provide ONLY the analysis content. Do not include any 
        conversational elements like "Is there anything else you need?" or 
        "Let me know if you have questions." Just provide the pure analysis.""",
        model="openai/gpt-4o",
        mcp_servers=["firecrawl"],
    )
    return result
async def main():
    url = input("Provide url to analyze: ")
    client = AsyncDedalus()
    analysis_res = await analyze_agent(client, url)  # ✅ Fixed: Added 'await'
    
    filename = "summary.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(analysis_res.final_output)  # ✅ Fixed: Added .final_output
    
    print(f"✅ Summary saved to {filename}")
    print("\nPreview:")
    print(analysis_res.final_output[:500] + "...")
    return analysis_res

if __name__ == "__main__":
    print("Running analyze_link.py")
    asyncio.run(main())