from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional

class ClauseSchema(BaseModel):
    clause_type: str = Field(description="Category of the clause e.g. Confidentiality, Liability, Termination, Governing Law, Payment, Indemnity")
    title: str = Field(description="Title or section name of the clause")
    text: str = Field(description="Original or substantive text of the clause from the document")
    source_page: Optional[int] = Field(default=None, description="Page number where the clause appears, if identifiable")

class LegalAnalysisResult(BaseModel):
    executive_summary: str = Field(default="", description="Concise executive summary of the legal document")
    important_points: List[str] = Field(default_factory=list, description="Key points, covenants, or risks identified in the document")
    parties: List[str] = Field(default_factory=list, description="Named parties entering or bound by the agreement")
    organizations: List[str] = Field(default_factory=list, description="Organizations, corporate entities, or institutions explicitly named")
    dates: List[str] = Field(default_factory=list, description="Dates, execution dates, effective periods, or deadlines")
    legal_acts: List[str] = Field(default_factory=list, description="Legal acts, statutes, or codes explicitly cited")
    legal_sections: List[str] = Field(default_factory=list, description="Specific statutory or contract sections explicitly referenced")
    payment_terms: List[str] = Field(default_factory=list, description="Payment schedule, compensation, invoicing, or fee terms")
    penalties: List[str] = Field(default_factory=list, description="Penalties, late interest, liquidated damages, or breach remedies")
    termination_conditions: List[str] = Field(default_factory=list, description="Termination for cause, convenience, notice periods, or survival")
    liability_and_indemnity: List[str] = Field(default_factory=list, description="Liability caps, indemnities, waivers, or exclusions")
    confidentiality: List[str] = Field(default_factory=list, description="Confidentiality covenants, non-disclosure restrictions, duration")
    dispute_resolution: List[str] = Field(default_factory=list, description="Dispute resolution methods such as arbitration, mediation, or court litigation")
    jurisdiction: List[str] = Field(default_factory=list, description="Governing law, forum jurisdiction, or applicable territory")
    obligations: List[str] = Field(default_factory=list, description="Specific duties, affirmative or negative obligations")
    clauses: List[ClauseSchema] = Field(default_factory=list, description="Extracted distinct legal clauses with original text")
    risk_score: Optional[float] = Field(default=75.0, description="Estimated legal risk / favorability score between 0 and 100")

class AnalysisResponse(BaseModel):
    id: str
    document_id: str
    summary: Optional[str] = None
    risk_score: Optional[float] = None
    extracted_entities: Optional[Dict[str, Any]] = None
    clauses: Optional[List[ClauseSchema]] = None
    model_config = ConfigDict(from_attributes=True)
