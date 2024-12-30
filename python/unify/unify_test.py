import unittest
import string
import random
from unify import anti_unify_group, matches_pattern, Pattern

def pretty(p: Pattern) -> str:
    return "[" + ", ".join(str(x) for x in p) + "]"

def random_triple(field_size=3):
    """
    Returns a random Triple with each field being
    a short random string of length up to field_size.
    """
    def random_str():
        length = random.randint(1, field_size)
        return ''.join(random.choice(string.ascii_letters) for _ in range(length))

    return (random_str(), random_str(), random_str())

def random_sentence(max_len=5, field_size=3):
    """
    Returns a random sentence, i.e., a list of random triples.
    Length is chosen randomly up to max_len.
    """
    length = random.randint(1, max_len)
    return [random_triple(field_size=field_size) for _ in range(length)]

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
        self.assertEqual(pat, [("A","B","C"),("D","E","F"), ("*","*","*")])
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
            assert matches_pattern(sen, pat), f"Group sentence {i} does not match!"

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
        self.assertEqual(pretty(pat), "[('s0', 'p0', 'b0'), ('*', '*', '*'), ('s3', 'p3', 'b3')]")

    def test_adjacent_wild_3tuples_collaps_with_part(self):
        group = [
            [("s0","p0","b0"), ("s1","p1","b1"), ("s2","p2","b2"), ("s3","p3","X")],
            [("s0","p0","b0"), ("S1","P1","B1"), ("S2","P2","B2"), ("s3","p3","b3")],
        ]
        pat = anti_unify_group(group)
        self.assertEqual(pretty(pat), "[('s0', 'p0', 'b0'), ('*', '*', '*'), ('s3', 'p3', '*')]")

    def test_tricky_case(self):
        group = [
            # Sentence 1: Repeated segments and partial overlap
            [("X","1","Z"), ("A","B","C"), ("A","B","C"), ("G","H","I")],
            # Sentence 2: Slight variation in first triple, fewer triples overall
            [("X","2","Z"), ("A","B","C")],
            # Sentence 3: "A B C" at the start, then extra different triples in the middle
            [("A","B","C"), ("X","1","Z"), ("Y","2","Z"), ("A","B","C")],
            # Sentence 4: Longer, with matching segments interspersed
            [("X","1","Z"), ("A","B","C"), ("G","H","I"), ("X","2","Z"), ("A","B","C")]
        ]

        pat = anti_unify_group(group)

        # Check that every sentence in the group matches the pattern
        # We only verify correctness by matching, not by exact equality of pat.
        for i, sen in enumerate(group):
            self.assertTrue(matches_pattern(sen, pat), f"Group sentence {i} does not match!")

    def test_fuzz(self):
        """
        Generates random groups of sentences with progressively more
        complexity. Unifies them, then checks if each sentence still
        matches the unified pattern.
        """
        # We'll go up to complexity = 10; feel free to increase
        for complexity in range(1, 3):
            with self.subTest(complexity=complexity):
                # For each complexity level:
                # 1) We'll create some random number of sentences (e.g. up to 'complexity').
                # 2) Each sentence can have up to 'complexity' 3-tuples.
                # 3) Each triple’s fields can have up to 'complexity' characters.
                
                num_sentences = random.randint(1, complexity)
                group = []
                for _ in range(num_sentences):
                    sentence = random_sentence(max_len=complexity, field_size=complexity)
                    group.append(sentence)

                # Attempt to unify the group
                pattern = anti_unify_group(group)

                # Verify that each original sentence matches the pattern
                for i, sentence in enumerate(group):
                    self.assertTrue(
                        matches_pattern(sentence, pattern),
                        f"Sentence {i} at complexity {complexity} does not match the pattern!"
                    )

                # (Optional) You could print some details to watch how the pattern evolves
                # print(f"Complexity: {complexity}, #sentences: {num_sentences}, Pattern: {pattern}")

if __name__ == "__main__":
    unittest.main()