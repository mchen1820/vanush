import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from pydantic import BaseModel, Field
from typing import List, Optional
from base_res_class import BaseAgentResult
import os
from dotenv import load_dotenv

load_dotenv()

class EvidenceResult(BaseAgentResult):
    """Result model for the Evidence Check Agent"""
    central_claim_evaluated: str = Field(..., description="The central claim being evaluated")
    total_evidence_found: int = Field(..., description="Total pieces of evidence identified")
    supporting_evidence_count: int = Field(0, description="Number of pieces supporting the claim")
    contradicting_evidence_count: int = Field(0, description="Number of pieces contradicting the claim")
    neutral_evidence_count: int = Field(0, description="Number of pieces that are neutral or irrelevant")
    evidence_items: List[str] = Field(default_factory=list, description="Direct, useful quotes from article")
    methodology_quality: str = Field(..., description="Assessment of research methodology: strong, adequate, weak, or not applicable")
    data_quality: str = Field(..., description="Assessment of data quality: strong, adequate, weak, or not applicable")
    logical_consistency: bool = Field(..., description="Whether the argument from evidence to claim is logically consistent")
    gaps_identified: List[str] = Field(default_factory=list, description="Gaps in evidence or reasoning")
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for strengthening the evidence")


async def evidence_check_agent(client: AsyncDedalus, article: str, central_claim:str) -> EvidenceResult:
    """Agent that evaluates how well the evidence in a paper supports its central claim"""
    runner = DedalusRunner(client)
    result = await runner.run(
        input=f"""

        The article can be found in:
        "{article}"
        The central_claim can be found in "{central_claim}


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
        10. Store 3-5 most important quotes (each no more than 1 sentence) in evidence items part of your return.
        Be critical and thorough. Look for unsupported assertions, cherry-picked data,
        logical fallacies, and missing counterarguments.

        In your summary, act like you are a professor reviewing this article for evidence and how it used
        Act like its part of a grade review with your student. """,
        model="openai/gpt-4o", 
        response_format=EvidenceResult,
        temperature = 0.2
    )
    return EvidenceResult.model_validate_json(result.final_output)