"""Reporting: data first, figures second.

Contract (not yet implemented): two entry points, because plotting is used at
two moments.

- The **data layer** takes run directories or a bundle plus a signal selection
  and returns series and tables. It does not import matplotlib, so it works in a
  notebook or a debugging session before any bundle exists.
- The **render layer** is a separate adapter behind the ``report`` extra. It
  turns the same view into figures and a plot manifest recording the input
  digests and renderer version.

A comparison figure draws the tolerance band or acceptance criterion on the same
axes as the data. Figures are derived artifacts: regenerable, never hashed into
an evidence bundle, and never an acceptance criterion.
"""
