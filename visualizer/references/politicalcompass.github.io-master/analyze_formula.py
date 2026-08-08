#!/usr/bin/env python3

# From script.js
econv = [
    [7, 5, 0, -2],    # 0: Q1
    [0, 0, 0, 0],     # 1: Q2
    [0, 0, 0, 0],     # 2: Q3
    [0, 0, 0, 0],     # 3: Q4
    [0, 0, 0, 0],     # 4: Q5
    [0, 0, 0, 0],     # 5: Q6
    [0, 0, 0, 0],     # 6: Q7
    [7, 5, 0, -2],    # 7: Q8
    [-7, -5, 0, 2],   # 8: Q9
    [6, 4, 0, -2],    # 9: Q10
    [7, 5, 0, -2],    # 10: Q11
    [-8, -6, 0, 2],   # 11: Q12
    [8, 6, 0, -2],    # 12: Q13
    [8, 6, 0, -1],    # 13: Q14
    [7, 5, 0, -3],    # 14: Q15
    [8, 6, 0, -1],    # 15: Q16
    [-7, -5, 0, 2],   # 16: Q17
    [-7, -5, 0, 1],   # 17: Q18
    [-6, -4, 0, 2],   # 18: Q19
    [6, 4, 0, -1],    # 19: Q20
    [0, 0, 0, 0],     # 20: Q21
    [0, 0, 0, 0],     # 21: Q22
    [0, 0, 0, 0],     # 22: Q23
    [0, 0, 0, 0],     # 23: Q24
    [-8, -6, 0, 1],   # 24: Q25
    [0, 0, 0, 0],     # 25: Q26
    [0, 0, 0, 0],     # 26: Q27
    [0, 0, 0, 0],     # 27: Q28
    [0, 0, 0, 0],     # 28: Q29
    [0, 0, 0, 0],     # 29: Q30
    [0, 0, 0, 0],     # 30: Q31
    [0, 0, 0, 0],     # 31: Q32
    [0, 0, 0, 0],     # 32: Q33
    [0, 0, 0, 0],     # 33: Q34
    [0, 0, 0, 0],     # 34: Q35
    [0, 0, 0, 0],     # 35: Q36
    [0, 0, 0, 0],     # 36: Q37
    [-10, -8, 0, 1],  # 37: Q38
    [-5, -4, 0, 1],   # 38: Q39
    [0, 0, 0, 0],     # 39: Q40
    [0, 0, 0, 0],     # 40: Q41
    [0, 0, 0, 0],     # 41: Q42
    [0, 0, 0, 0],     # 42: Q43
    [0, 0, 0, 0],     # 43: Q44
    [0, 0, 0, 0],     # 44: Q45
    [0, 0, 0, 0],     # 45: Q46
    [0, 0, 0, 0],     # 46: Q47
    [0, 0, 0, 0],     # 47: Q48
    [0, 0, 0, 0],     # 48: Q49
    [0, 0, 0, 0],     # 49: Q50
    [0, 0, 0, 0],     # 50: Q51
    [0, 0, 0, 0],     # 51: Q52
    [0, 0, 0, 0],     # 52: Q53
    [0, 0, 0, 0],     # 53: Q54
    [0, 0, 0, 0],     # 54: Q55
    [0, 0, 0, 0],     # 55: Q56
    [0, 0, 0, 0],     # 56: Q57
    [0, 0, 0, 0],     # 57: Q58
    [0, 0, 0, 0],     # 58: Q59
    [0, 0, 0, 0],     # 59: Q60
    [0, 0, 0, 0],     # 60: Q61
    [0, 0, 0, 0],     # 61: Q62
]

socv = [
    [0, 0, 0, 0],     # 0: Q1
    [-8, -6, 0, 2],   # 1: Q2
    [7, 5, 0, -2],    # 2: Q3
    [-7, -5, 0, 2],   # 3: Q4
    [-7, -5, 0, 2],   # 4: Q5
    [-6, -4, 0, 2],   # 5: Q6
    [7, 5, 0, -2],    # 6: Q7
    [0, 0, 0, 0],     # 7: Q8
    [0, 0, 0, 0],     # 8: Q9
    [0, 0, 0, 0],     # 9: Q10
    [0, 0, 0, 0],     # 10: Q11
    [0, 0, 0, 0],     # 11: Q12
    [0, 0, 0, 0],     # 12: Q13
    [0, 0, 0, 0],     # 13: Q14
    [0, 0, 0, 0],     # 14: Q15
    [0, 0, 0, 0],     # 15: Q16
    [0, 0, 0, 0],     # 16: Q17
    [0, 0, 0, 0],     # 17: Q18
    [0, 0, 0, 0],     # 18: Q19
    [0, 0, 0, 0],     # 19: Q20
    [0, 0, 0, 0],     # 20: Q21
    [-6, -4, 0, 2],   # 21: Q22
    [7, 6, 0, -2],    # 22: Q23
    [-5, -4, 0, 2],   # 23: Q24
    [0, 0, 0, 0],     # 24: Q25
    [8, 4, 0, -2],    # 25: Q26
    [-7, -5, 0, 2],   # 26: Q27
    [-7, -5, 0, 3],   # 27: Q28
    [6, 4, 0, -3],    # 28: Q29
    [6, 3, 0, -2],    # 29: Q30
    [-7, -5, 0, 3],   # 30: Q31
    [-9, -7, 0, 2],   # 31: Q32
    [-8, -6, 0, 2],   # 32: Q33
    [7, 6, 0, -2],    # 33: Q34
    [-7, -5, 0, 2],   # 34: Q35
    [-6, -4, 0, 2],   # 35: Q36
    [-7, -4, 0, 2],   # 36: Q37
    [0, 0, 0, 0],     # 37: Q38
    [0, 0, 0, 0],     # 38: Q39
    [7, 5, 0, -3],    # 39: Q40
    [-9, -6, 0, 2],   # 40: Q41
    [-8, -6, 0, 2],   # 41: Q42
    [-8, -6, 0, 2],   # 42: Q43
    [-6, -4, 0, 2],   # 43: Q44
    [-8, -6, 0, 2],   # 44: Q45
    [-7, -5, 0, 2],   # 45: Q46
    [-8, -6, 0, 2],   # 46: Q47
    [-5, -3, 0, 2],   # 47: Q48
    [-7, -5, 0, 2],   # 48: Q49
    [7, 5, 0, -2],    # 49: Q50
    [-6, -4, 0, 2],   # 50: Q51
    [-7, -5, 0, 2],   # 51: Q52
    [-6, -4, 0, 2],   # 52: Q53
    [0, 0, 0, 0],     # 53: Q54
    [-7, -5, 0, 2],   # 54: Q55
    [-6, -4, 0, 2],   # 55: Q56
    [-7, -6, 0, 2],   # 56: Q57
    [7, 6, 0, -2],    # 57: Q58
    [7, 5, 0, -2],    # 58: Q59
    [8, 6, 0, -2],    # 59: Q60
    [-8, -6, 0, 2],   # 60: Q61
    [-6, -4, 0, 2],   # 61: Q62
]

print("Political Compass Scoring Summary")
print("=" * 80)
print(f"Total questions: {len(econv)}")
print()

econ_questions = sum(1 for e in econv if e != [0, 0, 0, 0])
social_questions = sum(1 for s in socv if s != [0, 0, 0, 0])

print(f"Questions affecting Economic axis: {econ_questions}")
print(f"Questions affecting Social axis: {social_questions}")
print()

neutral_questions = []
for i in range(len(econv)):
    if econv[i] == [0, 0, 0, 0] and socv[i] == [0, 0, 0, 0]:
        neutral_questions.append(i + 1)

print(f"Questions with NO scoring impact: {len(neutral_questions)}")
print(f"Question numbers: {neutral_questions}")
print()

max_econ = sum(max(e) for e in econv)
min_econ = sum(min(e) for e in econv)
max_social = sum(max(s) for s in socv)
min_social = sum(min(s) for s in socv)

print("Theoretical raw score ranges:")
print(f"Economic: {min_econ} to {max_econ}")
print(f"Social: {min_social} to {max_social}")
print()

e0, s0 = 0.38, 2.41
econ_div, social_div = 8.0, 19.5

final_max_econ = (max_econ / econ_div) + e0
final_min_econ = (min_econ / econ_div) + e0
final_max_social = (max_social / social_div) + s0
final_min_social = (min_social / social_div) + s0

print("Final score ranges (after normalization and offset):")
print(f"Economic: {final_min_econ:.2f} to {final_max_econ:.2f}")
print(f"Social: {final_min_social:.2f} to {final_max_social:.2f}")
