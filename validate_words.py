from words import ALLOWED_CATEGORIES, STARTER_WORDS, hint_repetition_warnings, validate_words


def main() -> None:
    result = validate_words(STARTER_WORDS)
    categories = sorted({word["category"] for word in STARTER_WORDS})
    print(f"STRUCTURE OK: {len(STARTER_WORDS)} words")
    print("Categories:", ", ".join(categories))
    print("Allowed:", ", ".join(ALLOWED_CATEGORIES))
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


if __name__ == "__main__":
    main()
