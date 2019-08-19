# Rolling

This package deals with roll expressions, which are inspired by the syntax D&D uses.
At the most basic, there are expressions like `1d20` which means "roll one 20-sided die".
D&D stops around when modifiers are added, like `1d6+2`.
This package runs with it and introduces these dice expressions to an entire arithmetic framework.
You can add, subtract, multiply, even exponentiate rolls together, not to mention all of the roll-specific operations like taking the highest or lowest rolls or rerolling given a condition.
As these are mathematical expressions just like normal ones, note that they can get arbitrarily complicated.
The only limit is how much resources Python can bring to bear calculating your `(9^9^9^9^9)d10000` or similar ridiculous expression.  

The full specification of what operators are supported and what they do is below.

| Operator | Format          | Meaning
| :------- | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| !        | *x*__!__        | Calculate the factorial of _x_.
| d        | *x*__d__*y*     | Take a _y_-sided die and roll _x_ of them. _y_ can be an integer, and works just as you would expect. It can also be a list of arbitrary numbers (delineated by `[]` and separated with commas), in which case it works as a die with one side labeled with each number in the list.
| da       | *x*__da__*y*    | Take a _y_-sided die and return the average as if _x_ of them had been rolled. This returns an unrounded number.
| dc       | *x*__dc__*y*    | Roll a critical hit, where the number of dice rolled is doubled.
| dm       | *x*__dm__*y*    | Roll the maximum on every die rolled.
| h        | *ROLL*__h__*n*  | After making a roll, discard all but the highest _n_ of the rolls. Hint: 2d20h1 is advantage.
| l        | *ROLL*__l__*n*  | After making a roll, discard all but the lowest _n_ of the rolls. Hint: 2d20l1 is disadvantage.
| f        | *ROLL*__f__*n*  | After making a roll, treat any value that is less than _n_ as _n_.
| c        | *ROLL*__c__*n*  | After making a roll, treat any value that is greater than _n_ as _n_.
| r or ro  | *ROLL*__ro__*n* | After making a roll, look at all of them and reroll any that are equal to _n_, reroll those, and take the result.
| R or Ro  | *ROLL*__Ro__*n* | After making a roll, look at all of them and reroll any that are equal to _n_ and reroll those. If that number comes up again, continue rerolling until you get something different.
| r> or rh | *ROLL*__rh__*n* | After making a roll, look at all of them and reroll any that are strictly greater than _n_, reroll those, and take the result.
| R> or Rh | *ROLL*__Rh__*n* | After making a roll, look at all of them and reroll any that are greater than _n_ and reroll those. If a number greater than _n_ comes up again, continue rerolling until you get something different.
| r< or rl | *ROLL*__rl__*n* | After making a roll, look at all of them and reroll any that are strictly less than _n_, reroll those, and take the result.
| R< or Rl | *ROLL*__Rl__*n* | After making a roll, look at all of them and reroll any that are less than _n_ and reroll those. If a number less than _n_ comes up again, continue rerolling until you get something different.
| t        | *ROLL*__t__*n*  | After making the roll, count the number of rolls that were at least _n_.
| T        | *ROLL*__T__*n*  | After making the roll, count the number of rolls that were at most _n_.
| ^        | *x*__^__*y*     | Raise _x_ to the _y_ power. This operation is right-associative, meaning that the right side of the expression is evaluated before the left. This really only comes up when chained, for example in `2^3^2`. This would not be `(2^3)^2=8^2=64`, but rather `2^(3^2)=2^9=512`.
| *        | *x*__*__*y*     | _x_ times _y_.
| /        | *x*__/__*y*     | _x_ divided by _y_. This returns an unrounded number.
| %        | *x*__%__*y*     | _x_ modulo _y_. That is, the remainder after _x_ is divided by _y_.
| +        | *x*__+__*y*     | _x_ plus _y_.
| -        | *x*__-__*y*     | _x_ minus _y_.
| > or gt  | *x*__>__*y*     | Check if _x_ is greater than _y_. Returns a 1 for yes and 0 for no.
| >= or ge | *x*__>=__*y*    | Check if _x_ is greater than or equal to _y_. Returns a 1 for yes and 0 for no.
| < or lt  | *x*__<__*y*     | Check if _x_ is less than _y_. Returns a 1 for yes and 0 for no.
| <= or le | *x*__<=__*y*    | Check if _x_ is less than or equal to _y_. Returns a 1 for yes and 0 for no.
| =        | *x*__=__*y*     | Check if _x_ is equal to _y_. Returns a 1 for yes and 0 for no.
| &        | *x*__&__*y*     | Check if _x_ and _y_ are both nonzero.
| \|       | *x*__\|__*y*    | Check if at least one of _x_ or _y_ is nonzero.



## Using this package

### As a user or player

Installing this package from PyPI will also install the script `roll` to your path. This is a simple command-line script that allows you to exercise all the powers of this package.
For a GUI that does the same, check out my repository [DnD](https://github.com/the-nick-of-time/DnD) which is a larger project focused around D&D 5e and tracking the 


### As a developer

This entire repository can be used as a package, due to the `__init__.py` file in the root. 
This exposes the entire useful contents of the package at the top level so you can clone this repository anywhere you want to have access.
Of course, you could also install this as a standard python package through PyPI just like normal. 

Install [poetry](https://github.com/sdispater/poetry) for dependency management. There are no runtime dependencies, and the only development dependencies are [sphinx](http://www.sphinx-doc.org/en/master/) for documentation and [nose2](https://nose2.readthedocs.io/en/latest/index.html) for testing. 
