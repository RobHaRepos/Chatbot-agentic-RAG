import os


def test_precommit_hook_exists():
    """Check that the pre-commit hook exists in scripts/hooks."""
    assert os.path.exists("scripts/hooks/pre-commit")


def test_precommit_generates_badge():
    content = open("scripts/hooks/pre-commit", "r", encoding="utf-8").read()
    assert 'genbadge' in content
