import json
import math
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[1] / "data.js"


def get_region_label(x, y):
    if abs(x) < 1.5 and abs(y) < 1.5:
        return "Center"

    vertical = "Authoritarian" if y >= 0 else "Libertarian"
    horizontal = "Right" if x >= 0 else "Left"

    if abs(x) < 1.5:
        return f"Leaning {vertical}"
    if abs(y) < 1.5:
        return f"Leaning {horizontal}"

    return f"{vertical}-{horizontal}"


def load_experiment_data():
    content = DATA_FILE.read_text(encoding="utf-8")
    start = content.find("{")
    end = content.rfind("}") + 1
    return json.loads(content[start:end]), content


def main():
    try:
        data, content = load_experiment_data()
        print(f"File size: {len(content)}")
        print(f"Extracted JSON length: {len(content[content.find('{'):content.rfind('}') + 1])}")
        print(f"Keys in data: {list(data.keys())}")

        print(f"{'Model':<40} | {'Condition':<10} | {'Econ (X)':<8} | {'Soc (Y)':<8} | {'Region':<20}")
        print("-" * 100)

        for model, conditions in data.items():
            t1 = conditions.get("T1")
            if t1:
                x = t1.get("economic_score", 0)
                y = t1.get("social_score", 0)
                print(f"{model:<40} | {'T1':<10} | {x:<8.2f} | {y:<8.2f} | {get_region_label(x, y)}")

            for cond, details in conditions.items():
                if cond == "T1":
                    continue

                x = details.get("economic_score", 0)
                y = details.get("social_score", 0)

                if t1:
                    dx = x - t1.get("economic_score", 0)
                    dy = y - t1.get("social_score", 0)
                    dist = math.sqrt(dx * dx + dy * dy)
                    print(
                        f"{'':<40} | {cond:<10} | {x:<8.2f} | {y:<8.2f} | "
                        f"{get_region_label(x, y)} (Drift: {dist:.2f})"
                    )
                else:
                    print(f"{'':<40} | {cond:<10} | {x:<8.2f} | {y:<8.2f} | {get_region_label(x, y)}")

            print("-" * 100)
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
