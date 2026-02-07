"""
Test script for text_extractor.py
Run: python test_extractor.py
"""

from text_extractor import extract_text

# Test URLs - mix of different types
test_urls = [
    # arXiv abstract page (should convert to PDF automatically)
    "https://arxiv.org/abs/2301.00001",

    # Direct PDF link
    "https://arxiv.org/pdf/2301.00001.pdf",

    # Regular HTML article (Wikipedia - always accessible)
    "https://en.wikipedia.org/wiki/Machine_learning",

    # News article
    "https://www.bbc.com/news/technology-65855333",
]

def main():
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print(f"{'='*60}")

        text = extract_text(url)

        if text:
            print(f"✅ Success! Extracted {len(text)} characters")
            print(f"First 300 chars:\n{text[:300]}...")
        else:
            print(f"❌ Failed to extract text")

        print()

if __name__ == "__main__":
    main()