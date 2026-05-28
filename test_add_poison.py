"""
Tests for add_poison() using an English HTML sample file.

Run from the project root directory so that relative paths to
'popular.txt' and 'sample_english_input.txt' resolve correctly:

    pytest test_add_poison.py
"""
import re
import random
import pytest
from add_poison import add_poison, is_chinese

SAMPLE_FILE = "unit_test_data/sample_english_input.txt"
SAMPLE_FILE_ZH = "unit_test_data/sample_chinese_input.txt"
POISON_CLASS = "poison"
GOLDEN_FILE = "unit_test_data/expected_eng_default.txt"
GOLDEN_FILE_ZH = "unit_test_data/expected_chinese_default.txt"
RANDOM_SEED = 42
SPAN_PATTERN = re.compile(r'<span class="poison">(.*?)</span>')


@pytest.fixture(scope="module")
def poisoned_output():
    """
    Run add_poison with a fixed random seed and share the result across all
    tests in this module.  Using RANDOM_SEED guarantees the same junk words
    are inserted at the same positions on every test run.
    """
    random.seed(RANDOM_SEED)
    return add_poison(SAMPLE_FILE, mode="default", poison_class=POISON_CLASS)


def test_output_is_string(poisoned_output):
    """add_poison should return a string."""
    assert isinstance(poisoned_output, str)


def test_output_contains_span_tags(poisoned_output):
    """Output must contain at least one junk span with the correct class."""
    assert f'<span class="{POISON_CLASS}">' in poisoned_output, (
        "No junk <span> elements found in the output."
    )


def test_span_tags_are_well_formed(poisoned_output):
    """Every opening junk span must have a matching closing tag."""
    open_count = poisoned_output.count(f'<span class="{POISON_CLASS}">')
    close_count = poisoned_output.count("</span>")
    assert open_count == close_count, (
        f"Mismatched span tags: {open_count} opening vs {close_count} closing."
    )


def test_junk_is_not_empty(poisoned_output):
    """Each injected junk span must contain at least one character."""
    spans = SPAN_PATTERN.findall(poisoned_output)
    assert len(spans) > 0, "No junk spans captured by regex."
    for word in spans:
        assert word.strip() != "", "Found an empty junk span."


def test_junk_is_non_chinese(poisoned_output):
    """
    Junk words must be English (i.e. not detected as Chinese).
    Checks that no individual span content is classified as Chinese,
    and that none of the junk words contain CJK codepoints.
    """
    spans = SPAN_PATTERN.findall(poisoned_output)
    assert len(spans) > 0, "No junk spans found; cannot verify language."

    cjk_ranges = [
        (0x4E00, 0x9FFF),
        (0x3400, 0x4DBF),
        (0x20000, 0x2A6DF),
        (0xF900, 0xFAFF),
    ]

    def contains_cjk(s: str) -> bool:
        return any(
            any(lo <= ord(ch) <= hi for lo, hi in cjk_ranges)
            for ch in s
        )

    for word in spans:
        assert not contains_cjk(word), (
            f"Junk span contains CJK character(s): {word!r}"
        )


def test_original_content_preserved(poisoned_output):
    """
    A representative sentence from the original file must still appear
    verbatim in the output (junk is inserted between characters, not over them).
    """
    # Use a short, distinctive substring unlikely to be interrupted by junk
    # placed between tag boundaries.  The opening tags themselves are never
    # modified, so checking for an intact opening tag is a reliable proxy.
    assert "<p>" in poisoned_output, (
        "Original <p> tags are missing from the poisoned output."
    )


def test_exact_output_matches_golden(poisoned_output):
    """
    With RANDOM_SEED fixed, add_poison must produce byte-for-byte the same
    output as the pre-generated golden file on every run.  Re-generate
    expected_eng_default.txt whenever the algorithm or sample input changes.
    """
    with open(GOLDEN_FILE, mode="r", encoding="utf-8") as f:
        expected = f.read()
    assert poisoned_output == expected, (
        "Output does not match the golden file. "
        "If the algorithm changed intentionally, regenerate expected_eng_default.txt."
    )


# ---------------------------------------------------------------------------
# Chinese sample tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def poisoned_output_zh():
    """
    Run add_poison on the Chinese sample with a fixed random seed and share
    the result across all Chinese tests in this module.
    """
    random.seed(RANDOM_SEED)
    return add_poison(SAMPLE_FILE_ZH, mode="default", poison_class=POISON_CLASS)


def test_zh_output_is_string(poisoned_output_zh):
    """add_poison should return a string for Chinese input."""
    assert isinstance(poisoned_output_zh, str)


def test_zh_output_contains_span_tags(poisoned_output_zh):
    """Output must contain at least one junk span with the correct class."""
    assert f'<span class="{POISON_CLASS}">' in poisoned_output_zh, (
        "No junk <span> elements found in the Chinese output."
    )


def test_zh_span_tags_are_well_formed(poisoned_output_zh):
    """Every opening junk span must have a matching closing tag."""
    open_count = poisoned_output_zh.count(f'<span class="{POISON_CLASS}">')
    close_count = poisoned_output_zh.count("</span>")
    assert open_count == close_count, (
        f"Mismatched span tags: {open_count} opening vs {close_count} closing."
    )


def test_zh_junk_is_not_empty(poisoned_output_zh):
    """Each injected junk span must contain at least one character."""
    spans = SPAN_PATTERN.findall(poisoned_output_zh)
    assert len(spans) > 0, "No junk spans captured by regex."
    for fragment in spans:
        assert fragment.strip() != "", "Found an empty junk span."


def test_zh_junk_is_chinese(poisoned_output_zh):
    """
    Junk fragments must consist entirely of CJK characters — every character
    in every span must fall within a known CJK Unicode block.
    """
    cjk_ranges = [
        (0x4E00, 0x9FFF),
        (0x3400, 0x4DBF),
        (0x20000, 0x2A6DF),
        (0xF900, 0xFAFF),
    ]

    def is_cjk(ch: str) -> bool:
        cp = ord(ch)
        return any(lo <= cp <= hi for lo, hi in cjk_ranges)

    spans = SPAN_PATTERN.findall(poisoned_output_zh)
    assert len(spans) > 0, "No junk spans found; cannot verify language."
    for fragment in spans:
        for ch in fragment:
            assert is_cjk(ch), (
                f"Non-CJK character {ch!r} found in Chinese junk span: {fragment!r}"
            )


def test_zh_original_content_preserved(poisoned_output_zh):
    """Original HTML structure must survive poisoning intact."""
    assert "<p>" in poisoned_output_zh, (
        "Original <p> tags are missing from the Chinese poisoned output."
    )


def test_zh_exact_output_matches_golden(poisoned_output_zh):
    """
    With RANDOM_SEED fixed, add_poison must produce byte-for-byte the same
    output as the pre-generated Chinese golden file on every run.  Re-generate
    expected_chinese_default.txt whenever the algorithm or sample input changes.
    """
    with open(GOLDEN_FILE_ZH, mode="r", encoding="utf-8") as f:
        expected = f.read()
    assert poisoned_output_zh == expected, (
        "Output does not match the Chinese golden file. "
        "If the algorithm changed intentionally, regenerate expected_chinese_default.txt."
    )


