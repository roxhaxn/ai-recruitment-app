from resume_parser import parse_all_resumes
import pprint

input_folder = "resumes"
output_folder = "parsed_resumes"

print("🔍 Parsing all resumes...")
parsed = parse_all_resumes(input_folder, output_folder)

print("\n✅ Parsing complete! Parsed data:")
pprint.pprint(parsed)
