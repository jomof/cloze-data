# unify.py
from functools import lru_cache
from typing import List, Tuple

# A "triple" is (str, str, str) where each field might be a concrete string or '*'.
# We'll also allow the special triple wildcard indicated by ('*','*','*') to match
# multiple adjacent tuples.
Triple = Tuple[str, str, str]
Pattern = List[Triple]

def matches_pattern(sentence: List[Triple], pattern: Pattern) -> bool:
    """
    Returns True if 'sentence' matches the 'pattern'.
    A triple of ('*','*','*') in the pattern can match zero or more
    consecutive tuples in the sentence.
    A triple of (x,y,z) with possible '*' fields matches exactly 1 tuple.
    """
    i_s = 0
    i_p = 0
    len_s = len(sentence)
    len_p = len(pattern)

    while i_p < len_p:
        t_p = pattern[i_p]

        # Case 1: triple wildcard -> can match 0 or more adjacent sentence tuples
        if t_p == ('*', '*', '*'):
            i_p += 1
            if i_p == len_p:
                # This star soaks up all remaining sentence tuples
                return True
            # Otherwise, we have a next pattern element to match eventually
            for skip in range(len_s - i_s + 1):
                if matches_pattern(sentence[i_s+skip:], pattern[i_p:]):
                    return True
            return False

        # Case 2: normal triple => must match exactly 1 tuple
        if i_s >= len_s:
            return False
        t_s = sentence[i_s]
        # field-by-field check
        for a, b in zip(t_p, t_s):
            if a != '*' and a != b:
                return False

        i_s += 1
        i_p += 1

    # Must also have exhausted the sentence
    return (i_s == len_s)

def anti_unify_group(group: List[List[Triple]]) -> Pattern:
    """
    Given a list of sentences (each a list of 3-tuples),
    produce a 'least general generalization' pattern covering them all.
    Includes a post-processing step that collapses adjacent ('*','*','*').
    """

    # Edge case: if group is empty, return empty pattern
    if not group:
        return []

    n = len(group)
    lengths = [len(s) for s in group]

    @lru_cache(None)
    def all_done(positions):
        """Return True if for every k, positions[k] == lengths[k]."""
        return all(positions[k] == lengths[k] for k in range(n))

    def unify_next_tuples(positions):
        """
        If *all* sentences have a next tuple, unify them field-by-field.
        Returns that triple or None if any sentence is at end.
        """
        triples = []
        for k in range(n):
            i = positions[k]
            if i >= lengths[k]:
                return None
            triples.append(group[k][i])
        # unify field by field
        f0 = unify_field([t[0] for t in triples])
        f1 = unify_field([t[1] for t in triples])
        f2 = unify_field([t[2] for t in triples])
        return (f0, f1, f2)

    def unify_field(values):
        """
        If all values are the same, return that value.
        Else return '*'.
        """
        first = values[0]
        for v in values[1:]:
            if v != first:
                return '*'
        return first

    @lru_cache(None)
    def dp(positions: Tuple[int, ...], last_star: bool) -> Tuple[Pattern, ...]:
        """
        dp(positions, last_star) -> tuple of possible "best" patterns.
        positions: a tuple (i1, ..., in) for each sentence's cursor.
        last_star: True if the last pattern element is ('*','*','*').
        """
        if all_done(positions):
            return ([],)  # single solution => empty pattern

        solutions = []

        # Option 1: unify the next actual 3-tuples (if possible).
        ut = unify_next_tuples(positions)
        if ut is not None:
            new_positions = tuple(positions[k] + 1 for k in range(n))
            sub_pats = dp(new_positions, False)
            for sp in sub_pats:
                solutions.append([ut] + sp)

        # Option 2: try triple-wildcard, provided we didn't just add a star
        if not last_star:
            from itertools import product
            skip_ranges = []
            for k in range(n):
                remain = lengths[k] - positions[k]
                skip_ranges.append(range(remain + 1))

            for combo in product(*skip_ranges):
                # Must skip > 0 for at least one sentence if not all are done
                if all(c == 0 for c in combo):
                    continue

                new_pos = []
                for k in range(n):
                    skip_count = combo[k]
                    new_pos.append(positions[k] + skip_count)
                new_positions = tuple(min(new_pos[k], lengths[k]) for k in range(n))

                sub_pats = dp(new_positions, True)
                for sp in sub_pats:
                    # If sp starts with a star, skip to avoid consecutive stars
                    if sp and sp[0] == ('*','*','*'):
                        continue
                    solutions.append([('*','*','*')] + sp)

        if not solutions:
            return ()

        # Among solutions, pick all minimal under our "least general" ordering
        bests = min_solutions(solutions)
        return tuple(bests)

    def pattern_compare(p1: Pattern, p2: Pattern) -> int:
        """
        Return -1 if p1 < p2, 0 if equal, +1 if p1 > p2
        under 'least general' ordering:
          1) A pattern with *more* (non-*) content is "less general" => so bigger in "length" => smaller in ordering
          2) Ties => compare lexicographically, where concrete < '*'.
        """
        # Compare length first: longer => less general => so it should come first.
        if len(p1) > len(p2):
            return -1
        elif len(p1) < len(p2):
            return +1

        # same length => compare field-by-field
        for t1, t2 in zip(p1, p2):
            for f1, f2 in zip(t1, t2):
                if f1 == f2:
                    continue
                if f1 == '*' and f2 != '*':
                    return +1
                if f2 == '*' and f1 != '*':
                    return -1
        return 0

    def min_solutions(solutions: List[Pattern]) -> List[Pattern]:
        """
        Among 'solutions', return all that are minimal
        under 'pattern_compare' (the 'least general' ordering).
        """
        bests = []
        for pat in solutions:
            if not bests:
                bests = [pat]
                continue
            cmp_val = pattern_compare(pat, bests[0])
            if cmp_val < 0:
                # found strictly "less general" => new best
                bests = [pat]
            elif cmp_val == 0:
                # tie => keep it, unless it's the same in all fields
                if all(pattern_compare(pat, x) == 0 for x in bests):
                    bests.append(pat)
            # else pat is more general => ignore
        return bests

    def collapse_stars(pattern: Pattern) -> Pattern:
        """
        Post-process the pattern to collapse adjacent ('*','*','*')
        into a single ('*','*','*').
        """
        if not pattern:
            return pattern
        collapsed = []
        for triple in pattern:
            if triple == ('*','*','*'):
                # Only add it if the last one wasn't also a star triple
                if not collapsed or collapsed[-1] != ('*','*','*'):
                    collapsed.append(triple)
            else:
                collapsed.append(triple)
        return collapsed

    # Start DP from positions = all zero
    init_positions = tuple([0]*n)
    patterns = dp(init_positions, False)

    if not patterns:
        return []

    # Return the first minimal solution, then collapse adjacent star triples
    best_pattern = patterns[0]
    return collapse_stars(best_pattern)

# -------------- If run directly, do a quick unittest --------------
if __name__ == "__main__":
    import unittest

    def pretty(p: Pattern) -> str:
        return "[" + ", ".join(str(x) for x in p) + "]"

    class TestUnify(unittest.TestCase):

        def test_identity(self):
            sA = [("A","B","C"), ("D","E","F")]
            sB = [("A","B","C"), ("D","E","F")]
            pat1 = anti_unify_group([sA, sB])
            self.assertEqual(pat1, [("A","B","C"), ("D","E","F")])
            self.assertTrue(matches_pattern(sA, pat1))
            self.assertTrue(matches_pattern(sB, pat1))

        def test_single_field_difference(self):
            sA = [("A","B","C"), ("D","E","F")]
            sC = [("X","B","C"), ("D","E","F")]
            pat = anti_unify_group([sA, sC])
            self.assertEqual(pat, [('*','B','C'), ('D','E','F')])
            self.assertTrue(matches_pattern(sA, pat))
            self.assertTrue(matches_pattern(sC, pat))

        def test_different_length(self):
            sA = [("A","B","C"), ("D","E","F")]
            sD = [("A","B","C"), ("D","E","F"), ("G","H","I")]
            pat = anti_unify_group([sA, sD])
            self.assertEqual(pat, [("A","B","C"), ("D","E","F"), ("*","*","*")])
            self.assertTrue(matches_pattern(sA, pat))
            self.assertTrue(matches_pattern(sD, pat))

        def test_multiple_differences(self):
            sE = [("Q","W","E"), ("R","T","Y")]
            sF = [("Q","X","Z")]
            pat = anti_unify_group([sE, sF])
            self.assertEqual(pat, [("Q","*","*"), ("*","*","*")])
            self.assertTrue(matches_pattern(sE, pat))
            self.assertTrue(matches_pattern(sF, pat))

        def test_group(self):
            group = [
                [("s1","p1","b1"), ("s2","p2","b2")],
                [("s1","p1","bX")],
                [("s1","p1","b1"), ("s3","p3","b3"), ("s4","p4","b4")]
            ]
            pat = anti_unify_group(group)
            self.assertEqual(pretty(pat), "[('s1', 'p1', '*'), ('*', '*', '*')]")
            for i, sen in enumerate(group):
                self.assertTrue(matches_pattern(sen, pat))

        def test_middle_match(self):
            group = [
                [("s0","p0","b0"), ("s1","p1","b1")],
                [("s1","p1","b1"), ("s2","p2","b2")]
            ]
            pat = anti_unify_group(group)
            self.assertEqual(pretty(pat), "[('*', '*', '*'), ('s1', 'p1', 'b1'), ('*', '*', '*')]")
            for i, sen in enumerate(group):
                self.assertTrue(matches_pattern(sen, pat), f"Group sentence {i} does not match!")

        def test_empty(self):
            group = []
            pat = anti_unify_group(group)
            self.assertEqual(pretty(pat), "[]")

        def test_single(self):
            group = [
                [("s0","p0","b0"), ("s1","p1","b1")]
            ]
            pat = anti_unify_group(group)
            self.assertEqual(pretty(pat), "[('s0', 'p0', 'b0'), ('s1', 'p1', 'b1')]")

        def test_adjacent_wild_3tuples_collapse(self):
            group = [
                [("s0","p0","b0"), ("s1","p1","b1"), ("s2","p2","b2"), ("s3","p3","b3")],
                [("s0","p0","b0"), ("S1","P1","B1"), ("S2","P2","B2"), ("s3","p3","b3")],
            ]
            pat = anti_unify_group(group)
            # Because of the post-processing collapse, we should only see one ('*','*','*') in the middle
            self.assertEqual(pretty(pat), "[('s0', 'p0', 'b0'), ('*', '*', '*'), ('s3', 'p3', 'b3')]")

    unittest.main(argv=['ignored'], exit=False)
