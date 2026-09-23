from dataclasses import dataclass
from typing import Any
import csv
import os

@dataclass
class ActivityLog:
    """
    Agentの行動履歴を表すデータ
    """

    # ログ固有ID
    log_id: str

    # 行動したAgent
    agent_id: str

    # 行動したStep
    step: int

    # open_campus / commyunity
    phase: str

    # 行動の種類
    action: str

    # 行動対象
    target: str | None = None

    # 必要に応じて追加情報を保存
    value: Any = None


def create_activity_log(
        logs: list[ActivityLog],
        agent_id: str,
        step: int,
        phase: str,
        action: str,
        target: str | None = None,
        value: Any = None,
) -> ActivityLog:
    """
    新しいActivity Logを生成してlogsに追加する
    """

    log_number = len(logs) + 1
    log_id = f"LOG_{log_number:06d}"

    log = ActivityLog(
        log_id=log_id,
        agent_id=agent_id,
        step=step,
        phase=phase,
        action=action,
        target=target,
        value=value,
    )

    logs.append(log)

    return log

def save_activity_logs(
        logs: list[ActivityLog],
        file_path: str,
) -> None:
    """
    Activity LogをCSVファイルとして保存する
    """

    # 保存先フォルダが存在しない場合は作成
    directory = os.path.dirname(file_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    # CSVを書き込む
    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        # ヘッダー
        writer.writerow([
            "log_id",
            "agent_id",
            "step",
            "phase",
            "action",
            "target",
            "value",
        ])

        # 各ログを書き込む
        for log in logs:
            writer.writerow([
                log.log_id,
                log.agent_id,
                log.step,
                log.phase,
                log.action,
                log.target,
                log.value,
            ])