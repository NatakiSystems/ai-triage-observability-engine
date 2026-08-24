"""
Policy lookup: retrieves the policy text relevant to a ticket's category.

OWNER: Lance

This replaces the human step of "go find the right section of the shared
policy doc." Right now it's a simple section match on the category, which is
honest and defensible for a prototype.

YOUR JOB:
  1. Parse data/policy_kb.md into sections keyed by category.
  2. Return the right section for a given category.
  3. Return something sensible when there is no match.

Worth raising in the pitch: we deliberately did NOT use vector search here.
Our policy doc has four sections. Exact section lookup is more reliable than
embeddings at this scale, and it can't hallucinate a policy that doesn't
exist. That's a design choice, not a shortcut.
"""

import os

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "policy_kb.md")


def load_policy_sections():
    """
    Parse the policy markdown into {category: text}.

    Sections are marked with `## category-name` headers in policy_kb.md.

    Returns:
        dict[str, str]
    """
    sections = {}
    current = None
    buffer = []

    with open(KB_PATH, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                if current:
                    sections[current] = "".join(buffer).strip()
                current = line[3:].strip().lower()
                buffer = []
            elif current:
                buffer.append(line)

    if current:
        sections[current] = "".join(buffer).strip()

    return sections


def lookup_policy(category):
    """
    Get the policy text for one category.

    Args:
        category: "billing" | "technical" | "returns" | "other"

    Returns:
        str: the policy text, or a clear fallback message.
    """
    sections = load_policy_sections()

    # TODO (Lance): decide what should happen on a miss. Returning empty text
    # means the drafter writes from nothing, which is exactly the failure mode
    # the critic should catch. Talk to Julian about which of you handles it.
    return sections.get(
        category,
        "NO POLICY FOUND for this category. Escalate to a human agent.",
    )
def lookup_policy(category):
    sections = load_policy_sections()
    text = sections.get(category)
    if text is None:
        return None, False
    return text, True
