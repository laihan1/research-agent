from dataclasses import dataclass, field

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    query: str
    round: int

@dataclass
class Step:
    round: int
    action: str
    input: dict
    output: dict
    duration_ms: int

@dataclass
class Report:
    topic: str
    background: str = ""
    findings: list[dict] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    status: str = "ok"