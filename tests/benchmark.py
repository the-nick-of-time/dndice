from dndice import basic, verbose
from dndice.lib.evaltree import EvalTree

if __name__ == '__main__':
    testCases = [
        "1d4+1",
        "1d4-1",
        "2d20h1",
        "2d20l1",
        "40d20r1h1",
        "10d4r1",
        "10d4R1",
        "1d4d4d4",
        "-5",
        "+1d4",
        "2*-1d4",
        "-2^1d4",
        "8d6/2",
        "1+(1+4)d6",
        "(1d6)!",
        "1d6!",
        "1d100<14",
        "1d100<=18",
        "8d6f2",
        "1d20+5>10",
        "5d20r<15",
        "5d20R<15",
        "(1d4-1)&(1d3-2>0)",
        "(1d4-1)|(1d3-2>0)",
        "1dc8+1dc4+3",
        "1dm6+1d6",
        "2d4c2",
        "2da6",
        "3da6",
        "2d10%2",
        "1d4=4|1d4=3",
        "1d8>=6",
        "10d8r>4",
        "10d8R>4",
        "10d[3,3,3,5]",
        "10d[3, 3, 3, 5]",
        "15d6t5",
        "15d6T1",
    ]
    for expr in testCases:
        tree = EvalTree(expr)
        print('EVALUATING ' + expr)
        print('EVALUATING USING TREE DIRECTLY')
        print(tree.evaluate())
        print('EVALUATING USING ROLL FUNCTION')
        print(basic(expr))
        print('EVALUATING USING ROLL FUNCTION IN VERBOSE MODE')
        print(verbose(expr))
        print('EVALUATING USING ROLL FUNCTION AND MODIFIER')
        print(basic(expr, modifiers=3))
        print('EVALUATING USING ROLL FUNCTION IN VERBOSE MODE AND MODIFIER')
        print(verbose(expr, modifiers=3))
        print()
