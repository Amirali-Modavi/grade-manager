from backend.names import normalize_student_name, student_name_key


def test_name_key_is_case_insensitive_for_unicode_letters():
    assert student_name_key("Élise") == student_name_key("élise")


def test_name_key_normalizes_persian_and_arabic_yeh_and_kaf():
    assert student_name_key("علي") == student_name_key("علی")
    assert student_name_key("كاظم") == student_name_key("کاظم")


def test_name_normalization_collapses_whitespace_and_diacritics():
    assert normalize_student_name("  علي   \u0654  ") == "علی"
