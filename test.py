#pip install dedalus_labs, 
#pip install dotenv and add api key to .env. add .env to gitignore

import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from dotenv import load_dotenv

load_dotenv()
dedalus_api_key = os.getenv('DEDALUS_API_KEY')
print(dedalus_api_key)

async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)
    result = await runner.run(
        input="""I need to research the latest developments in AI agents for 2024.
        Please help me:
        1. Find recent news articles about AI agent breakthroughs
        2. Search for academic papers on multi-agent systems
        3. Look up startup companies working on AI agents
        4. Find GitHub repositories with popular agent frameworks
        5. Summarize the key trends and provide relevant links
        Focus on developments from the past 6 months.""",
        model="openai/gpt-4o",  
        mcp_servers=["firecrawl"],  
    )
    print(f"Web Search Results:\n{result.final_output}")

if __name__ == "__main__":
    print("Running test.py")
    asyncio.run(main())


