"""Generate the copyright-safe demo PDF from sample_course.md content."""

from __future__ import annotations

import textwrap
from pathlib import Path

import fitz

PAGES = [
    (
        "Page 1 · Probability and conditional probability",
        """
Probability describes uncertainty about an event. A conditional probability asks how likely event A
is after observing event B.

P(A | B) = P(A and B) / P(B) when P(B) > 0.

In machine learning, conditional probability is useful because an observation changes our belief
about a class or hypothesis.
""",
    ),
    (
        "Page 2 · Bayes Rule and MAP classification",
        """
Bayes Rule rewrites a posterior probability:

P(H | D) = P(D | H) P(H) / P(D).

The posterior combines a likelihood, a prior belief, and a normalizing evidence term. Maximum a
posteriori, or MAP, classification chooses the class with the highest posterior probability:

h_MAP = argmax_h P(h | D).

MAP includes a prior. If all class priors are equal, MAP can reduce to maximum likelihood.
""",
    ),
    (
        "Page 3 · Maximum likelihood estimation",
        """
Maximum likelihood estimation chooses the parameter value that makes the observed data most likely:

theta_ML = argmax_theta P(D | theta).

The likelihood is a function of the parameter after the data has been observed.
It is not, by itself, a probability distribution over parameter values.
""",
    ),
    (
        "Page 4 · A worked comparison",
        """
Suppose two classes have different priors but the same likelihood for one observation.
MAP may prefer the class with the larger prior, while maximum likelihood treats the priors as
irrelevant.
This is why MAP is useful when prior knowledge is meaningful.
""",
    ),
]


def _draw_wrapped(page: fitz.Page, text: str, top: float, fontsize: float = 13) -> None:
    y = top
    for paragraph in text.split("\n"):
        lines = textwrap.wrap(paragraph, width=82) or [""]
        for line in lines:
            page.insert_text((64, y), line, fontsize=fontsize, fontname="helv")
            y += fontsize * 1.55
        y += fontsize * 0.55


def main() -> None:
    output = Path(__file__).resolve().parent / "sample_course.pdf"
    document = fitz.open()
    for title, body in PAGES:
        page = document.new_page(width=595, height=842)
        page.insert_text((64, 72), title, fontsize=20, fontname="hebo")
        _draw_wrapped(page, body, top=120)
        page.insert_text(
            (64, 790),
            "EduAgent self-authored demo material",
            fontsize=9,
            fontname="hebo",
        )
    document.save(output)
    document.close()
    print(f"Created {output}")


if __name__ == "__main__":
    main()
