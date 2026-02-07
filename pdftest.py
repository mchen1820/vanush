#pip install dedalus_labs, 
#pip install dotenv and add api key to .env. add .env to gitignore
#pip install pypdf

import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from dotenv import load_dotenv
from pypdf import PdfReader


load_dotenv()
dedalus_api_key = os.getenv('DEDALUS_API_KEY')

#local file, for testing; input your own local file path to test this out
testfile = r"INSERT-LOCAL-PATH"

def extract_file_text(file):
	reader = PdfReader(file)
	file_text = ""
	for page in reader.pages:
		file_text += page.extract_text()
	return file_text
            
text = extract_file_text(testfile)

async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)
    result = await runner.run(
        input="""Given the following article text, produce a concise summary
            that includes a brief core summary and mentions aspects like the
            author/source credibility, bias and perspective, use of evidence,
            citations and sources, and overall assessment. Here's the article
            text: """ + text,
        model="openai/gpt-4o",  
        mcp_servers=["firecrawl"],  
    )
    print(f"Article Summary:\n{result.final_output}")

if __name__ == "__main__":
    print("Running test.py")
    asyncio.run(main())