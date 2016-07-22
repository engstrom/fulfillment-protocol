#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import pprint
import unittest
from resolver import Resolver, ResolverContainer


class TestResolver(unittest.TestCase):

    def setUp(self):
        pass

    def test_Contains(self):
        r = Resolver("stuff")
        self.assertTrue(r.contains_code("<(hello"))

    def test_Basic(self):
        r = Resolver("stuff")
        self.assertTrue(r.evaluated)

    def test_ExecSimple(self):
        r = Resolver("<(return [1, 2, 3]")
        self.assertFalse(r.evaluated)
        self.assertEqual(r.evaluate(), [1, 2, 3])

    def test_ExecMultiLine(self):
        r = Resolver(["<(",
            "def func(things):",
            "  return s2j('[1,2,{}]'.format(things))",
            "return func('3')"
        ]).evaluate()
        self.assertEqual(r, [1, 2, 3])

    def test_ExecBadBuiltins(self):
        r = Resolver(["<(",
            "with open('foo') as f:",
            "  f.write('bar')"
        ])
        self.assertEqual(r.evaluate(), None)
        self.assertEqual(r.first_msg(), "Error in script: global name 'open' is not defined")

    def test_ExecImport(self):
        r = Resolver("<(\nimport json")
        self.assertEqual(r.evaluate(), None)
        self.assertFalse(r.is_resolved())
        self.assertEqual(r.first_msg(), "Error in script: __import__ not found")

    def test_ExecGenerator(self):
        res = Resolver(["<(",
            "def fib(n):",
            "    a, b = 0, 1",
            "    for _ in xrange(n):",
            "        yield a",
            "        a, b = b, a + b",
            "return list(fib(10))"
        ]).evaluate()
        self.assertEqual(res, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])

    def test_ExecRecursion(self):
        res = Resolver(["<(",
            "def fib(n, a=0, b=1):",
            "  return fib(n-1, b, a+b) if n > 0 else a",
            "return fib(10)"
        ]).evaluate()
        self.assertEqual(res, 55)

    def test_InfiniteLoop(self):
        r = Resolver(["<(",
            "while True:",
            "  pass"
        ], timeout_sec=1)
        self.assertEqual(r.evaluate(), None)
        self.assertFalse(r.is_resolved())
        self.assertEqual(r.first_msg(), "Error in script: TIMEOUT")

    def test_ExecException(self):
        res = Resolver(["<(",
            "try:",
            "  return 0 / 0",
            "except ZeroDivisionError as z:",
            "  return 'divide by zero'"
        ]).evaluate()
        self.assertEqual(res, 'divide by zero')

    def test_ExecCompound(self):
        r = Resolver({"one two three": "<(return [1, 2, 3]"})

        self.assertFalse(r.evaluated)
        r.evaluate()
        self.assertEqual(r.result, {"one two three": [1, 2, 3]})

    def test_ExecError(self):
        r = Resolver({"one two three": "<(return [1, 2, 3"})

        self.assertFalse(r.evaluated)
        r.evaluate()
        self.assertEqual(r.first_msg(), 'Error in script: invalid syntax (<string>, line 3)')
        self.assertEqual(r.result, None)

    def test_ExecSectionGen(self):
        res = Resolver(["<(",
            "r = range(65,91)",
            "names = [chr(a)+chr(b) for a in r for b in r]",
            "def valsec(value):",
            "  return { 'value': '#prefix#_{}'.format(value) }",
            "return j2s({",
            "  'sections': { name:valsec(name) for name in names }",
            "})"
        ]).evaluate()
        self.assertEqual(len(res), 21646)

    def test_ResolverContainer(self):
        r = ResolverContainer()
        r.add("stuff", "yes")

        self.assertEqual(r.stuff, "yes")
        self.assertEqual(r["stuff"], "yes")

        r.add("things", "<( 'wo' + 'rm'")

        self.assertEqual(r.things, "worm")
        self.assertEqual(r["things"], "worm")

        r.add("whaaa", "steel", transform=lambda x: x+"y")

        self.assertEqual(r.whaaa, "steely")
        self.assertEqual(r["whaaa"], "steely")

        r.add("whaaa_eval", "<( { 'a' : 'steel', 'b' : 'hammock®' }['a']", transform=lambda x: x+"y")

        self.assertEqual(r.whaaa_eval, "steely")
        self.assertEqual(r["whaaa_eval"], "steely")

        self.assertTrue("stuff" in r)
        self.assertTrue("whaaa_eval" in r)
        self.assertFalse("pickle" in r)

        self.assertEqual(r.to_json(), {'stuff': 'yes', 'things': 'worm', 'whaaa': 'steely', 'whaaa_eval': 'steely'})

        self.assertEqual(r.to_json(True), {'stuff': 'yes',
                                           'things': {'evaluated': True,
                                                      'input': "<( 'wo' + 'rm'",
                                                      'needsEvaluation': True,
                                                      'resolvable': True,
                                                      'resolved': True,
                                                      'result': 'worm',
                                                      'timeline': []},
                                           'whaaa': 'steely',
                                           'whaaa_eval': {'evaluated': True,
                                                          'input': "<( { 'a' : 'steel', 'b' : 'hammock®' }['a']",
                                                          'needsEvaluation': True,
                                                          'resolvable': True,
                                                          'resolved': True,
                                                          'result': 'steel',
                                                          'timeline': []}})

    def test_ResolverCompound(self):
        r = ResolverContainer()
        r.add("stuff", "yes")

        self.assertEqual(r.stuff, "yes")
        self.assertEqual(r["stuff"], "yes")

        r.add("things", "<( 'wo' + 'rm'")

        self.assertEqual(r.things, "worm")
        self.assertEqual(r["things"], "worm")

        r2 = ResolverContainer()
        r2.add("blue", "<( 5 + 27")

        self.assertEqual(r2.blue, 32)

        r.add("sub", r2)

        self.assertEqual(r.to_json(), {'stuff': 'yes', 'sub': {'blue': 32}, 'things': 'worm'})

        self.assertEqual(r.to_json(True), {'stuff': 'yes',
                                           'sub': {'blue': {'evaluated': True,
                                                            'input': '<( 5 + 27',
                                                            'needsEvaluation': True,
                                                            'resolvable': True,
                                                            'resolved': True,
                                                            'result': 32,
                                                            'timeline': []}},
                                           'things': {'evaluated': True,
                                                      'input': "<( 'wo' + 'rm'",
                                                      'needsEvaluation': True,
                                                      'resolvable': True,
                                                      'resolved': True,
                                                      'result': 'worm',
                                                      'timeline': []}})


if __name__ == '__main__':
    unittest.main()
