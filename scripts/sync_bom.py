import csv
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "docs", "BOM.csv")
MD_PATH = os.path.join(BASE_DIR, "docs", "readme.md")
def generate_markdown_table(csv_path):
    table = []
    try:
        with open(csv_path, mode="r", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if not any(row):
                    continue
                cleaned_row = [str(cell).strip() for cell in row if cell.strip() != ""]
                if len(cleaned_row) == 0:
                    continue
                for j in range(len(cleaned_row)):
                    if cleaned_row[j].startswith("http"):
                        cleaned_row[j] = f"[Link]({cleaned_row[j]})"
                row_str = "| " + " | ".join(cleaned_row) + " |"
                table.append(row_str)
                if i == 0:
                    separator = "| " + " | ".join(["---"] * len(cleaned_row)) + " |"
                    table.append(separator)
        return "\n".join(table)
    except Exception as e:
        return ""
def update_readme(md_path, markdown_table):
    if not markdown_table:
        return
    with open(md_path, "r", encoding="utf-8") as file:
        content = file.read()
    start_marker = "<!-- BOM_START -->"
    end_marker = "<!-- BOM_END -->"
    if start_marker in content and end_marker in content:
        before = content.split(start_marker)[0]
        after = content.split(end_marker)[1]
        new_content = before + start_marker + "\n\n" + markdown_table + "\n\n" + end_marker + after
        with open(md_path, "w", encoding="utf-8") as file:
            file.write(new_content)
if __name__ == "__main__":
    table = generate_markdown_table(CSV_PATH)
    update_readme(MD_PATH, table)
