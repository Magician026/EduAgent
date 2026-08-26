# Probabilistic Machine Learning Basics

This self-authored mini-course is included only to make EduAgent easy to demo.

## Page 1 — Probability and conditional probability

Probability describes uncertainty about an event. A conditional probability asks how likely an event A is after observing event B:

`P(A | B) = P(A and B) / P(B)` when `P(B) > 0`.

In machine learning, conditional probability is useful because an observation changes our belief about a class or hypothesis.

## Page 2 — Bayes Rule and MAP classification

Bayes Rule rewrites a posterior probability:

`P(H | D) = P(D | H) P(H) / P(D)`.

Here H is a hypothesis or class and D is observed data. The posterior combines a likelihood, a prior belief, and a normalizing evidence term.

Maximum a posteriori, or MAP, classification chooses the class with the highest posterior probability:

`h_MAP = argmax_h P(h | D)`.

MAP differs from maximum likelihood because MAP includes a prior. If all class priors are equal, the MAP decision can reduce to a maximum-likelihood decision.

## Page 3 — Maximum likelihood estimation

Maximum likelihood estimation chooses the parameter value that makes the observed data most likely:

`theta_ML = argmax_theta P(D | theta)`.

The likelihood is a function of the parameter after the data has been observed. It is not, by itself, a probability distribution over parameter values.

## Page 4 — A worked comparison

Suppose two classes have different priors but the same likelihood for one observation. MAP may prefer the class with the larger prior, while maximum likelihood treats the priors as irrelevant. This is why MAP is useful when prior knowledge is meaningful.
