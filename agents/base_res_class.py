from pydantic import BaseModel, Field
from typing import List, Optional

class BaseAgentResult(BaseModel):
    agent_name: str
    overall_score: float = Field(..., description="A score from 0 to 100")
    summary: str = Field(..., description="A brief overview of findings")
    confidence_score: float = Field(..., description="A score from 0 to 100 indicating confidence in the results")

