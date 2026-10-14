from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Kubernetes troubleshooting question",
    )

    resource_type: str | None = Field(
        default=None,
        description="Kubernetes resource type, for example Deployment or Pod",
    )

    resource_name: str | None = Field(
        default=None,
        description="Name of the Kubernetes resource",
    )

    namespace: str | None = Field(
        default=None,
        description="Kubernetes namespace",
    )


class ResourceReference(BaseModel):
    type: str
    name: str
    namespace: str | None = None


class Assessment(BaseModel):
    status: str
    severity: str


class InvestigationMetadata(BaseModel):
    tools_used: list[str] = Field(
        default_factory=list
    )
    evidence_summary: list[str] = Field(
        default_factory=list
    )


class InvestigationResponse(BaseModel):
    resource: ResourceReference | None = None

    assessment: Assessment

    facts: list[str] = Field(
        default_factory=list
    )

    root_cause: str

    hypotheses: list[str] = Field(
        default_factory=list
    )

    recommended_next_steps: list[str] = Field(
        default_factory=list
    )

    investigation: InvestigationMetadata = Field(
        default_factory=InvestigationMetadata
    )