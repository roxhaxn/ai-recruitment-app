from topsis_ranking import rank_candidates

# You can change job title below:
ranked = rank_candidates("parsed_resumes/parsed_output.csv", "Data Analyst")
print(ranked[["name", "Score", "Rank"]])
