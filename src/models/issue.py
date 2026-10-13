from dataclasses import dataclass, field


@dataclass
class Issue:
    issue_id: str
    title: str
    options: list[str]
    start_step: int

    # Agent IDと投票内容を保存
    votes: dict[str, str] = field(default_factory=dict)

    def can_vote(self, agent_id: str) -> bool:
        """
        指定したAgentが未投票か確認する。
        """
        return agent_id not in self.votes

    def add_vote(self, agent_id: str, choice: str) -> bool:
        """
        Issueに投票を登録する。
        重複投票や存在しない選択肢は拒否する。
        """

        if not self.can_vote(agent_id):
            return False

        if choice not in self.options:
            return False

        self.votes[agent_id] = choice

        return True