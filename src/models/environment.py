from dataclasses import dataclass, field

@dataclass
class Environment:
    """
    シミュレーション環境を表すクラス
    """

    # 現在のStep
    current_step: int = 0

    # 現在のフェーズ
    phase: str = "open_campus"

    # Communityフェーズで使用する状態
    vote_open: bool = False
    issue_available: bool = False
    task_available: bool = False