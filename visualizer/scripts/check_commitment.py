import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[1] / "data.js"


def load_experiment_data():
    content = DATA_FILE.read_text(encoding="utf-8")
    start = content.find("{")
    end = content.rfind("}") + 1
    return json.loads(content[start:end])


def summarize_questions(questions):
    total_answers = 0
    total_committed = 0
    total_neutral = 0
    total_refusals = 0

    for question in questions:
        counts = question.get("answer_counts", {})
        neutral = question.get("neutral_count", 0)
        refusal = question.get("refusal_count", 0)
        committed = sum(counts.values())

        total_committed += committed
        total_neutral += neutral
        total_refusals += refusal
        total_answers += committed + neutral

    commitment_rate = (total_committed / total_answers * 100) if total_answers > 0 else 0
    return commitment_rate, total_neutral, total_refusals


def analyze_commitment():
    try:
        data = load_experiment_data()

        print(
            f"{'Model':<30} | {'Cond':<8} | {'Commit%':<7} | {'Neutral':<7} | "
            f"{'Refusals':<8} | {'Soc (Y)':<8} | {'Shift Y':<8}"
        )
        print("-" * 110)

        for model, conditions in data.items():
            t1 = conditions.get("T1")
            if not t1:
                continue

            t1_comm_rate, _, _ = summarize_questions(t1.get("per_question", []))
            t1_soc = t1.get("social_score", 0)

            for cond in ["T3-LEFT", "T3-RIGHT"]:
                if cond not in conditions:
                    continue

                c_data = conditions[cond]
                c_comm_rate, c_total_neutral, c_total_refusals = summarize_questions(
                    c_data.get("per_question", [])
                )
                c_soc = c_data.get("social_score", 0)
                shift_y = c_soc - t1_soc

                if shift_y > 1.0 or c_total_neutral > 50:
                    print(
                        f"{model:<30} | {cond:<8} | {c_comm_rate:<7.1f} | "
                        f"{c_total_neutral:<7} | {c_total_refusals:<8} | {c_soc:<8.2f} | "
                        f"{shift_y:<8.2f} (T1 Comm: {t1_comm_rate:.1f}%)"
                    )
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    analyze_commitment()
