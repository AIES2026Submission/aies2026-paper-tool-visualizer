#!/usr/bin/env python3

econv = [
    [7, 5, 0, -2], [-0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [7, 5, 0, -2], [-7, -5, 0, 2], [6, 4, 0, -2],
    [7, 5, 0, -2], [-8, -6, 0, 2], [8, 6, 0, -2], [8, 6, 0, -1], [7, 5, 0, -3],
    [8, 6, 0, -1], [-7, -5, 0, 2], [-7, -5, 0, 1], [-6, -4, 0, 2], [6, 4, 0, -1],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [-8, -6, 0, 1],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [-10, -8, 0, 1], [-5, -4, 0, 1], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0]
]

socv = [
    [0, 0, 0, 0], [-8, -6, 0, 2], [7, 5, 0, -2], [-7, -5, 0, 2], [-7, -5, 0, 2],
    [-6, -4, 0, 2], [7, 5, 0, -2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
    [0, 0, 0, 0], [-6, -4, 0, 2], [7, 6, 0, -2], [-5, -4, 0, 2], [0, 0, 0, 0],
    [8, 4, 0, -2], [-7, -5, 0, 2], [-7, -5, 0, 3], [6, 4, 0, -3], [6, 3, 0, -2],
    [-7, -5, 0, 3], [-9, -7, 0, 2], [-8, -6, 0, 2], [7, 6, 0, -2], [-7, -5, 0, 2],
    [-6, -4, 0, 2], [-7, -4, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0], [7, 5, 0, -3],
    [-9, -6, 0, 2], [-8, -6, 0, 2], [-8, -6, 0, 2], [-6, -4, 0, 2], [-8, -6, 0, 2],
    [-7, -5, 0, 2], [-8, -6, 0, 2], [-5, -3, 0, 2], [-7, -5, 0, 2], [7, 5, 0, -2],
    [-6, -4, 0, 2], [-7, -5, 0, 2], [-6, -4, 0, 2], [0, 0, 0, 0], [-7, -5, 0, 2],
    [-6, -4, 0, 2], [-7, -6, 0, 2], [7, 6, 0, -2], [7, 5, 0, -2], [8, 6, 0, -2],
    [-8, -6, 0, 2], [-6, -4, 0, 2]
]

questions = [
    "Q1: Globalization should serve humanity",
    "Q2: Support country right or wrong",
    "Q3: Foolish to be proud of birthplace",
    "Q4: Racial superiority",
    "Q5: Enemy of my enemy",
    "Q6: Military action vs international law",
    "Q7: Info-entertainment fusion",
    "Q8: Class vs nationality",
    "Q9: Inflation vs unemployment",
    "Q10: Corporate environmental regulation",
    "Q11: 'From each... to each...'",
    "Q12: Freer market = freer people",
    "Q13: Bottled water commodification",
    "Q14: Land as commodity",
    "Q15: Fortune from money manipulation",
    "Q16: Protectionism in trade",
    "Q17: Company's only duty is profit",
    "Q18: Rich too highly taxed",
    "Q19: Pay for better medical care",
    "Q20: Penalize misleading businesses",
    "Q21: Free market needs monopoly restrictions",
    "Q22: Abortion should be illegal",
    "Q23: Question all authority",
    "Q24: Eye for an eye",
    "Q25: No arts funding",
    "Q26: Compulsory school attendance",
    "Q27: People keep to their own kind",
    "Q28: Spanking children",
    "Q29: Children keep secrets",
    "Q30: Marijuana decriminalization",
    "Q31: School for jobs",
    "Q32: Eugenics",
    "Q33: Children learn discipline",
    "Q34: Cultural relativism",
    "Q35: No work, no support",
    "Q36: Don't think about troubles",
    "Q37: Immigrant integration",
    "Q38: Corporate success benefits all",
    "Q39: No public broadcasting funding",
    "Q40: Civil liberties vs terrorism",
    "Q41: One-party state advantage",
    "Q42: Surveillance",
    "Q43: Death penalty",
    "Q44: Social hierarchy",
    "Q45: Abstract art",
    "Q46: Punishment vs rehabilitation",
    "Q47: Rehabilitating criminals",
    "Q48: Business vs arts",
    "Q49: Mothers as homemakers",
    "Q50: Economic growth vs climate",
    "Q51: Peace with establishment",
    "Q52: Astrology",
    "Q53: Morality requires religion",
    "Q54: Charity vs social security",
    "Q55: Religious values in school",
    "Q56: Religious values in school (dup)",
    "Q57: Sex outside marriage",
    "Q58: Same-sex adoption",
    "Q59: Legal pornography",
    "Q60: Private bedroom privacy",
    "Q61: Homosexuality unnatural",
    "Q62: Openness about sex"
]

def calculate_score(answers):
    e_sum = sum(econv[i][answers[i]] for i in range(62) if answers[i] != -1)
    s_sum = sum(socv[i][answers[i]] for i in range(62) if answers[i] != -1)

    e_score = (e_sum / 8.0) + 0.38
    s_score = (s_sum / 19.5) + 2.41

    return round(e_score, 2), round(s_score, 2), e_sum, s_sum

def show_question_impact(q_num):
    idx = q_num - 1
    print(f"\n{questions[idx]}")
    print("=" * 70)

    options = ["Strongly Disagree", "Disagree", "Agree", "Strongly Agree"]

    print("\nEconomic Impact:")
    for i, opt in enumerate(options):
        val = econv[idx][i]
        if val > 0:
            direction = f"→ RIGHT (+{val})"
        elif val < 0:
            direction = f"← LEFT ({val})"
        else:
            direction = "○ NEUTRAL"
        print(f"  {opt:20s}: {direction}")

    print("\nSocial Impact:")
    for i, opt in enumerate(options):
        val = socv[idx][i]
        if val > 0:
            direction = f"↑ AUTHORITARIAN (+{val})"
        elif val < 0:
            direction = f"↓ LIBERTARIAN ({val})"
        else:
            direction = "○ NEUTRAL"
        print(f"  {opt:20s}: {direction}")

def main():
    print("Political Compass Formula Calculator")
    print("=" * 70)
    print()

    print("EXAMPLE 1: All 'Agree' (neutral) answers")
    print("-" * 70)
    neutral_answers = [2] * 62  # All "Agree"
    e, s, e_raw, s_raw = calculate_score(neutral_answers)
    print(f"Raw sums: Economic={e_raw}, Social={s_raw}")
    print(f"Final scores: Economic={e}, Social={s}")
    print(f"Position: {'Left' if e < 0 else 'Right'} {abs(e):.2f}, "
          f"{'Libertarian' if s < 0 else 'Authoritarian'} {abs(s):.2f}")

    print("\n\nEXAMPLE 2: Extreme Left-Libertarian")
    print("-" * 70)
    left_lib = []
    for i in range(62):
        e_vals = econv[i]
        s_vals = socv[i]

        best_answer = 0
        best_score = (e_vals[0], s_vals[0])

        for j in range(4):
            if e_vals[j] < best_score[0] or (e_vals[j] == best_score[0] and s_vals[j] < best_score[1]):
                best_answer = j
                best_score = (e_vals[j], s_vals[j])

        left_lib.append(best_answer)

    e, s, e_raw, s_raw = calculate_score(left_lib)
    print(f"Raw sums: Economic={e_raw}, Social={s_raw}")
    print(f"Final scores: Economic={e}, Social={s}")

    print("\n\nQUESTION IMPACT EXAMPLES")
    print("=" * 70)

    show_question_impact(1)
    show_question_impact(12)
    show_question_impact(38)
    show_question_impact(32)

    print("\n\nQUESTIONS WITH NO IMPACT")
    print("=" * 70)
    for i in range(62):
        if econv[i] == [0, 0, 0, 0] and socv[i] == [0, 0, 0, 0]:
            print(f"  {questions[i]}")

if __name__ == "__main__":
    main()
