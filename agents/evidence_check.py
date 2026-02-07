import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import BaseModel, Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv

load_dotenv()


class EvidenceItem(BaseModel):
    description: str = Field(..., description="Description of the piece of evidence")
    supports_claim: bool = Field(..., description="Whether this evidence supports the central claim")
    strength: str = Field(..., description="Strength of the evidence: strong, moderate, or weak")
    reasoning: str = Field(..., description="Why this evidence does or does not support the claim")


class EvidenceResult(BaseAgentResult):
    """Result model for the Evidence Check Agent"""
    central_claim_evaluated: str = Field(..., description="The central claim being evaluated")
    total_evidence_found: int = Field(..., description="Total pieces of evidence identified")
    supporting_evidence_count: int = Field(0, description="Number of pieces supporting the claim")
    contradicting_evidence_count: int = Field(0, description="Number of pieces contradicting the claim")
    neutral_evidence_count: int = Field(0, description="Number of pieces that are neutral or irrelevant")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="Detailed breakdown of each piece of evidence")
    methodology_quality: str = Field(..., description="Assessment of research methodology: strong, adequate, weak, or not applicable")
    data_quality: str = Field(..., description="Assessment of data quality: strong, adequate, weak, or not applicable")
    logical_consistency: bool = Field(..., description="Whether the argument from evidence to claim is logically consistent")
    gaps_identified: List[str] = Field(default_factory=list, description="Gaps in evidence or reasoning")
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for strengthening the evidence")


async def evidence_check_agent(client: AsyncDedalus, url: str, central_claim: str) -> EvidenceResult:
    """Agent that evaluates how well the evidence in a paper supports its central claim"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""Analyze the academic paper at: {url}

        The central claim of this paper has been identified as:
        "{central_claim}"

        Perform a thorough evidence evaluation:
        1. Identify all key pieces of evidence presented in the paper.
        2. For each piece of evidence, determine whether it supports, contradicts, or is neutral to the central claim.
        3. Rate the strength of each piece of evidence (strong, moderate, or weak).
        4. Explain why each piece of evidence does or does not support the claim.
        5. Assess the quality of the research methodology used.
        6. Assess the quality of the data presented.
        7. Determine whether the argument from evidence to claim is logically consistent.
        8. Identify any gaps in the evidence or reasoning.
        9. Provide recommendations for strengthening the evidence.
        
        Be critical and thorough. Look for unsupported assertions, cherry-picked data,
        logical fallacies, and missing counterarguments.""",
        model="openai/gpt-4o",
        mcp_servers=["firecrawl"],
        response_format=EvidenceResult,
    )

    evidence_result = EvidenceResult.model_validate_json(result.final_output)

    # Compute confidence based on how much evidence was actually found and evaluated
    if evidence_result.total_evidence_found > 0:
        evidence_result.confidence_score = (
            evidence_result.supporting_evidence_count / evidence_result.total_evidence_found * 100
        )
    else:
        evidence_result.confidence_score = 0.0

    return evidence_result


async def main():
    url = input("Provide URL of academic paper to check evidence: ")
    central_claim = input("Provide the central claim to evaluate against: ")
    client = AsyncDedalus()
    result = await evidence_check_agent(client, url, central_claim)

    print("\n🔬 Evidence Check Results")
    print("=" * 60)
    print(f"\n📍 Claim Evaluated:")
    print(f"   {result.central_claim_evaluated}")
    print(f"\n📊 Scores:")
    print(f"   Overall Score: {result.overall_score}/100")
    print(f"   Confidence: {result.confidence_score:.1f}/100")
    print(f"\n📈 Evidence Breakdown:")
    print(f"   Total Evidence Found: {result.total_evidence_found}")
    print(f"   Supporting: {result.supporting_evidence_count}")
    print(f"   Contradicting: {result.contradicting_evidence_count}")
    print(f"   Neutral: {result.neutral_evidence_count}")
    print(f"\n🔍 Quality Assessment:")
    print(f"   Methodology: {result.methodology_quality}")
    print(f"   Data Quality: {result.data_quality}")
    print(f"   Logically Consistent: {'Yes' if result.logical_consistency else 'No'}")

    if result.evidence_items:
        print(f"\n📋 Evidence Details:")
        for i, item in enumerate(result.evidence_items, 1):
            emoji = "✅" if item.supports_claim else "❌"
            print(f"   {emoji} [{item.strength.upper()}] {item.description}")
            print(f"      → {item.reasoning}")

    if result.gaps_identified:
        print(f"\n⚠️  Gaps Identified:")
        for gap in result.gaps_identified:
            print(f"     • {gap}")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"     • {rec}")

    print(f"\n📝 Summary: {result.summary}")
    return result


if __name__ == "__main__":
    print("Running evidence_check.py")
    asyncio.run(main())