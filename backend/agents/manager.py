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
from date_check import date_check_agent, DateResult
from usefullness_check import usefulness_check_agent, UsefulnessResult

load_dotenv(find_dotenv())
dedalus_api_key = os.getenv('DEDALUS_API_KEY')

class ManagerSynthesisResult(BaseAgentResult):
    """Manager's final synthesis of all agent results"""
    overall_credibility_score: int = Field(..., description="Overall credibility 0-100")
    key_findings: List[str] = Field(..., description="3-5 most important findings")
    red_flags: List[str] = Field(..., description="Major concerns or warnings")
    strengths: List[str] = Field(..., description="What the article does well")
    final_verdict: str = Field(..., description="Final assessment in 2-3 sentences")
    recommendation: str = Field(..., description="Should reader trust this? Use with caution? Ignore?")

async def manager_synthesis_agent(
    client,
    url: str,
    claim_res: claim_result,
    citation_res: CitationResult,
    bias_res: BiasCheckResult,
    author_res: AuthorResult,
    ev_res: EvidenceResult,
    usefulness_res: UsefulnessResult,
    date_res: DateResult
) -> ManagerSynthesisResult:
    """
    Manager agent that reviews all sub-agent outputs and creates a synthesis
    """
    runner = DedalusRunner(client)
    
    # Build comprehensive context from all agents
    synthesis_prompt = f"""You are a senior fact-checker reviewing analyses from multiple junior analysts about this article: {url}

Your team has completed the following analyses. Review them carefully and provide a final synthesis:

CLAIM ANALYSIS:
Summary: {claim_res.summary}
Central Claim: {claim_res.central_claim}
Confidence Score: {claim_res.confidence_score}/100
Overall Score: {claim_res.overall_score}/100

CITATION ANALYSIS:
Summary: {citation_res.summary}
Confidence Score: {citation_res.confidence_score}/100
Overall Score: {citation_res.overall_score}/100

BIAS ANALYSIS:
Summary: {bias_res.summary}
Confidence Score: {bias_res.confidence_score}/100
Overall Score: {bias_res.overall_score}/100

AUTHOR/ORGANIZATION ANALYSIS:
Summary: {author_res.summary}
Confidence Score: {author_res.confidence_score}/100
Overall Score: {author_res.overall_score}/100

EVIDENCE ANALYSIS:
Summary: {ev_res.summary}
Confidence Score: {ev_res.confidence_score}/100
Overall Score: {ev_res.overall_score}/100

USEFULNESS ANALYSIS:
Summary: {usefulness_res.summary}
Confidence Score: {usefulness_res.confidence_score}/100
Overall Score: {usefulness_res.overall_score}/100

DATE ANALYSIS:
Summary: {date_res.summary}
Confidence Score: {date_res.confidence_score}/100
Overall Score: {date_res.overall_score}/100

---

Based on ALL these analyses, provide your final synthesis:

1. overall_credibility_score: Weighted overall score (0-100) considering all factors
2. summary: Executive summary of your findings (3-4 sentences)
3. key_findings: List 3-5 most important discoveries across all analyses
4. red_flags: List any major concerns or warnings (empty list if none)
5. strengths: List what the article does well (empty list if nothing notable)
6. final_verdict: Your final assessment in 2-3 sentences
7. recommendation: One of: "Trustworthy", "Use with caution", "Questionable", "Do not trust"
8. confidence_score: How confident you are in this synthesis (0-100)
9. overall_score: Same as overall_credibility_score

Think critically: Do the analyses agree or contradict? Are there patterns? What's the overall picture?
"""

    result = await runner.run(
        input=synthesis_prompt,
        model="openai/gpt-4o",
        temperature=0.2,  # Slightly creative for synthesis
        response_format=ManagerSynthesisResult
    )
    
    return ManagerSynthesisResult.model_validate_json(result.final_output)


async def manager_agent(client:str, input_text: str, topic: str) -> Dict[str, BaseAgentResult]:
    """
    Manager agent to coordinate multiple analysis agents and synthesize results
    """
    
    # Phase 1: Run independent agents in parallel
    claim_res = await claim_agent(client, input_text)
    central_claim = claim_res.central_claim

    citation_res, bias_res, date_res = await asyncio.gather(
        citation_check_agent(client, input_text),
        bias_check_agent(client,input_text),
        date_check_agent(client, input_text, topic)
    )

    
    # Phase 2: Run dependent agents
    print("\n🔍 Phase 2: Running dependent analysis...")
    ev_res, usefulness_res, author_res = await asyncio.gather(
        evidence_check_agent(client, input_text, central_claim),
        usefulness_check_agent(client, input_text, topic),
        author_check_agent(client, input_text, central_claim, topic),
    )
    
    # Phase 3: Manager synthesizes all results
    print("\nPhase 3: Manager synthesizing results...")
    synthesis = await manager_synthesis_agent(
        client,
        input_text,
        claim_res,
        citation_res,
        bias_res,
        author_res,
        ev_res,
        usefulness_res,
        date_res
    )
    print("Phase 3 complete")
    
    return {
        "claim": claim_res,
        "citations": citation_res,
        "bias": bias_res,
        "author": author_res,
        "evidence": ev_res,
        "usefulness": usefulness_res,
        "date": date_res,
        "synthesis": synthesis  # Manager's final output
    }


async def main():
    input_text = '''
    The relationship between reading proficiency and educational attainment has been frequently documented (Ogle, Sen, Pahlke, Kastberg, & Roey, 2003). Tightly operationalized measures of reading proficiency and literacy abilities have been shown to predict high school completion, degrees earned, adult income and occupational status (Raudenbush & Kasim, 1998; Wigfield & Guthrie, 1997). A high level of literacy proficiency is frequently assumed and is indeed central to participation in many social and educational institutions (Wagner, 1999). In Westernized countries education is one of the most important social and cultural institutions providing a formalized structure marking out childhood, as well as transitions through adolescence and adulthood (Côté, 2000). Schools are increasingly charged with many responsibilities, not least of all ensuring that children learn to read well so that they can engage with the types of reading and writing that are essential for academic achievement throughout their school careers.
    A further, although often less explicitly identified outcome of reading instruction is the enjoyment of reading as a social, cultural and recreational activity. That is, the development of reading as a pleasurable activity in its own right. The reading that children and adolescents engage in for its own sake may also provide ‘self-generated learning opportunities’ (Wigfield & Guthrie, 1997, p. 404), that in turn serve to nurture and support educational aspirations, achievement motivation, occupational choices, as well as ways of understanding one-self and others. More recently, researchers have also turned their attention to a variety of out-of-school and unstructured literacy practices of adolescents (Alvermann, Young, Green, & Wisenbaker, 1999; Chandler-Olcott & Mahar, 2003; Black, 2005; Moje, 2000), noting individuals’ motivations for engagement and persistence, even when the task complexity of the literacy practices appears to challenge their skill level (Moje, Dillon, & O’Brien, 2000). How these new forms of literacy practices influence and impact on school-based achievement is an enduring and unresolved question for literacy researchers. The present study focuses on individual reading of print books among youth, an activity which in children has been demonstrated to have an impact on school achievement.
    Individuals engage with different literacy practices as they navigate social environments even when they occur in a single location such as a doctor’s waiting room. For instance, we may be asked to sign our name on a registration form, fill out our personal medical history on a checklist, take part in a medical survey, read complex documents that indemnify the medical practitioner, and as we sit waiting to be called, peruse the covers and contents of magazines and newspapers, while the overhead television is reporting the latest news and weather or the latest sporting news. Depending on time, we may settle on an article that captures our interest and is informative, or we may simply pass the time skimming through various stories and viewing the almost compromising exploits of the stars of stage and screen captured by the telephoto lenses of the paparazzi photographers. The point is that this type of reading involves our own interest, as fleeting as that may be. We choose what we will read and there is no one there to check on our comprehension except ourselves. At the same time, to engage in social and cultural activities we increasingly need to deal with an array of literate demands that involve everything from highly complex, specialized texts through to less involved and ephemeral texts such as catalogues, pictorially rich magazines, and the increasingly ever-present assortment of other digital media that insinuate themselves into our lives.



    '''
    topic = input("Provide topic to analyze: ")
    
    client = AsyncDedalus(api_key=dedalus_api_key)
    
    # Run manager agent
    results = await manager_agent(client, input_text=input_text, topic=topic)
    
    # Print individual agent results
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
    
    print(f"\nEvidence Analysis: {results['evidence'].summary}")
    print(f"   Score: {results['evidence'].overall_score}/100")
    
    print(f"\nUsefulness Analysis: {results['usefulness'].summary}")
    print(f"   Score: {results['usefulness'].overall_score}/100")
    
    synthesis = results['synthesis']
    print("\n" + "="*60)
    print("MANAGER'S FINAL SYNTHESIS")
    print("="*60)
    
    print(f"\nOverall Credibility Score: {synthesis.overall_credibility_score}/100")
    print(f"   Recommendation: {synthesis.recommendation}")
    
    print(f"\nFinal Verdict:")
    print(f"   {synthesis.final_verdict}")
    
    print(f"\nKey Findings:")
    for i, finding in enumerate(synthesis.key_findings, 1):
        print(f"   {i}. {finding}")
    
    if synthesis.red_flags:
        print(f"\nRed Flags:")
        for i, flag in enumerate(synthesis.red_flags, 1):
            print(f"   {i}. {flag}")
    
    if synthesis.strengths:
        print(f"\nStrengths:")
        for i, strength in enumerate(synthesis.strengths, 1):
            print(f"   {i}. {strength}")
    
    print(f"\nExecutive Summary:")
    print(f"   {synthesis.summary}")
    
    return results


if __name__ == "__main__":
    print("Running manager.py")
    asyncio.run(main())