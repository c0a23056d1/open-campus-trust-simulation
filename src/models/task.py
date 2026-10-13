from dataclasses import dataclass, field

@dataclass
class Task:
    """Communityで発生するミッション"""

    task_id: str
    name: str
    required_action: str

    start_step: int
    end_step: int

    # このTaskを達成したAgent
    completed_agents: set[str] = field(
        default_factory=set
    )

    def is_active(self, current_step: int) -> bool:
        """現在のStepでTaskが有効か判断する。"""

        return (
            self.start_step
            <= current_step
            <= self.end_step
        )
    
    def can_complete(
        self,
        agent_id: str,
        action: str,
        current_step: int,
    ) -> bool:
        """Taskを達成できるか判断する"""

        return (
            self.is_active(current_step)
            and action == self.required_action
            and agent_id not in self.completed_agents
        )