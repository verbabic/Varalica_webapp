from words import ALLOWED_CATEGORIES, STARTER_WORDS, duplicate_word_warnings, hint_repetition_warnings, validate_words


def main() -> None:
    result = validate_words(STARTER_WORDS)
    categories = sorted({word["category"] for word in STARTER_WORDS})
    print(f"STRUCTURE OK: {len(STARTER_WORDS)} words")
    print("Categories:", ", ".join(categories))
    print("Allowed:", ", ".join(ALLOWED_CATEGORIES))
    structural_errors = getattr(result, "structural_errors", [])
    if structural_errors:
        print(f"STRUCTURAL ERRORS: {len(structural_errors)}")
        for issue in structural_errors[:25]:
            print(f"- {issue.word_id} [{issue.field}]: {issue.message}")
    if result.quality_warnings:
        print(f"QUALITY WARNINGS: {len(result.quality_warnings)}")
        for issue in result.quality_warnings[:25]:
            print(f"- {issue.word_id} [{issue.field}]: {issue.message}")
    else:
        print("QUALITY OK: no warnings")

    repetition_warnings = hint_repetition_warnings(STARTER_WORDS)
    if repetition_warnings:
        print(f"HINT REPETITION WARNINGS: {len(repetition_warnings)}")
        for warning in repetition_warnings[:25]:
            print(f"- {warning}")
    else:
        print("HINT REPETITION OK: no major repeated pools")

    duplicate_warnings = duplicate_word_warnings(STARTER_WORDS)
    if duplicate_warnings:
        print(f"DUPLICATE WORD WARNINGS: {len(duplicate_warnings)}")
        for warning in duplicate_warnings[:25]:
            print(f"- {warning}")
    else:
        print("DUPLICATE WORD OK: no duplicate SR/HR words or pairs")


if __name__ == "__main__":
    main()
