from words import ALLOWED_CATEGORIES, STARTER_WORDS, validate_words


def main() -> None:
    validate_words(STARTER_WORDS)
    categories = sorted({word["category"] for word in STARTER_WORDS})
    print(f"OK: {len(STARTER_WORDS)} words")
    print("Categories:", ", ".join(categories))
    print("Allowed:", ", ".join(ALLOWED_CATEGORIES))


if __name__ == "__main__":
    main()
