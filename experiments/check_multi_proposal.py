
import csv

PASSPORT_PATH = (
    "results/comparison/Multi/trust_passports.csv"
)

# Agentごとの最終Passport
latest_passports = {}

with open(PASSPORT_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        agent_id = row["agent_id"]
        step = int(row["step"])

        if (
            agent_id not in latest_passports
            or step > int(latest_passports[agent_id]["step"])
        ):
            latest_passports[agent_id] = row


passports = list(latest_passports.values())

ct_values = [
    float(p["contribution"])
    for p in passports
]

gt_values = [
    float(p["governance"])
    for p in passports
]

print("========== Multi Trust 分析 ==========")

print(f"Agent数: {len(passports)}")

print()
print("---- CT（Contribution Trust）----")
print(f"最大値: {max(ct_values):.3f}")
print(f"平均値: {sum(ct_values)/len(ct_values):.3f}")
print(
    "CT >= 0.7:",
    sum(v >= 0.7 for v in ct_values),
    "人"
)

print()
print("---- GT（Governance Trust）----")
print(f"最大値: {max(gt_values):.3f}")
print(f"平均値: {sum(gt_values)/len(gt_values):.3f}")
print(
    "GT >= 0.5:",
    sum(v >= 0.5 for v in gt_values),
    "人"
)

print()
print("---- Proposal条件 ----")
print(
    "CT >= 0.7 かつ GT >= 0.5:",
    sum(
        float(p["contribution"]) >= 0.7
        and float(p["governance"]) >= 0.5
        for p in passports
    ),
    "人"
)

print()
print("---- GT上位10人 ----")

for p in sorted(
    passports,
    key=lambda x: float(x["governance"]),
    reverse=True,
)[:10]:

    print(
        p["agent_id"],
        "CT=",
        round(float(p["contribution"]), 3),
        "GT=",
        round(float(p["governance"]), 3),
    )
