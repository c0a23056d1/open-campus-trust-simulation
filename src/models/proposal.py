from dataclasses import dataclass, field

@dataclass
class Proposal:
    proposal_id: str
    agent_id: str
    created_step: int

    relevance: float
    feasibility: float
    benefit: float
    quality: float

    votes: dict[str, bool] = field(default_factory=dict)
    perceived_qualities: dict[str, float] = field(
        default_factory=dict
    )

    status: str = "open"
    rejection_reason: str | None = None

    @property
    def total_votes(self) -> int:
        return len(self.votes)

    @property
    def yes_votes(self) -> int:
        return sum(self.votes.values())

    @property
    def no_votes(self) -> int:
        return self.total_votes - self.yes_votes

    @property
    def approval_rate(self) -> float | None:
        if self.total_votes == 0:
            return None
        return self.yes_votes / self.total_votes

    def is_voting_open(
        self,
        current_step: int,
        duration: int,
    ) -> bool:
        return (
            self.status == "open"
            and self.created_step < current_step
            <= self.created_step + duration
        )

    def add_vote(
        self,
        agent_id: str,
        support: bool,
        perceived_quality: float,
        current_step: int,
        duration: int,
    ) -> bool:

        if not self.is_voting_open(current_step, duration):
            return False

        if agent_id in self.votes:
            return False

        self.votes[agent_id] = support
        self.perceived_qualities[agent_id] = perceived_quality
        return True