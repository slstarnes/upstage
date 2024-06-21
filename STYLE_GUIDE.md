# Python Code Style Guide

## Credit and Primer

- Based on Trey Hunner's [Style Guide](https://github.com/TruthfulTechnology/style-guide).
- Recommend you watch Trey's [presentation](https://www.youtube.com/watch?v=NvkC5UBJqeY) at PyCon 2017.

## Baseline

- We try to abide by strong recommendations in [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- We use [Flake8](http://flake8.pycqa.org) for some automated style checks

## Variables

Sometimes you need to name things.

### Naming

We tend to use long variable names: whole words and often multiple words.

We will sometimes use a single letter variable name for a looping variable, but usually we'll try to use a longer name even if it means we need to split the line up for readability.

### Naming Indexes

Whenever we see something like `some_variable[0]` or `some_variable[2]`, we treat this as an indication that we should be relying on iterable unpacking.

Instead of this:

``` python
do_something(things[0], things[1])
```

We would rather see this:

``` python
first, second = things
do_something(first, second)
```

Instead of this:

``` python
do_something(things[0], things[1:-1], things[-1])
```

We would rather see this:

``` python
head, *middle, tail = things
do_something(head, middle, tail)
```

### Unused Variables

We try to avoid making variables we'll never use.

There are two times we sometimes find we need to make a variable even though we'll never use it: iterable unpacking and a list comprehension over a `range`:

``` python
head, *unused_middle, tail = things
do_something(head, tail)
matrix = [[0] * 3 for unused_index in range(3)]
```

We tend to prefer using ``_`` for these variables which are never used:

``` python
head, *_, tail = things
do_something(head, tail)
matrix = [[0] * 3 for _ in range(3)]
```

## Compacting Assignments

We sometimes use iterable unpacking to compact multiple assignment statements onto one line.  We only do this when the assignments are very tightly related:

``` python
word1, word2 = word1.upper(), word2.upper()
x, y, z = (a1 - a2), (b1 - b2), (c1 - c2)
```

## Defining Functions

Sometimes you need to write your own functions.

### Function Naming

We use lowercase function names, with whole words separated by underscores.  We rarely shorten words or smash words together without a separating underscore.

We typically prefer to name functions with a verb (even if it means putting ``get_`` or ``find_`` in front of the function name).

### Line Wrapping

We tend to wrap function definitions with many arguments like this:

``` python
    def function_with_many_args(first_arg, second_arg, third_arg,
                                fourth_arg, optional_arg1=None,
                                optional_arg2=None, *, keyword_arg1,
                                keyword_arg2, keyword_arg3):
```

Note that this style differs from the style we use for calling functions with many arguments.

We do not use a special notation to distinguish positional arguments, arguments with default values, or keyword-only arguments in function definitions.

### Arguments

We prefer to limit the number of arguments my functions accept.  If a function accepts more than a couple arguments, we usually prefer to make some or all arguments keyword only:

``` python
    def function_with_many_args(first_arg, second_arg, *, keyword_arg1=None,
                                keyword_arg2=None, keyword_arg3=None):
```

We prefer not to write functions that require more than a few arguments.  We see many required arguments is an indication that there's a missing collection/container/data type.

## Calling Functions

What good is defining a function if you never call it?

### Spacing

We do not use whitespace before the opening parenthesis of a function call nor inside the parenthesis of a function call:

``` python
def __str__(self):
    return " ".join((self.first_name, self.last_name))
```

We never do this:

``` python
def __str__(self):
    return " ".join ((self.first_name, self.last_name))
```

and we never do this:

``` python
def __str__(self):
    return " ".join( (self.first_name, self.last_name) )
```

### Line Wrapping Functions

When line-wrapping a function call that includes all keyword arguments, **we prefer the following code style**:

``` python
def __repr__(self):
    return "{class_name}({first_name}, {last_name}, {age})".format(
        class_name=type(self).__name__,
        first_name=repr(self.first_name),
        last_name=repr(self.last_name),
        age=self.age,
    )
```

We put the opening parenthesis at the end of the first line and the closing parenthesis on its own line aligned with the beginning of the initiating line.  Each keyword argument goes on its own line which ends in a comma, including the final one.  The keyword arguments are indented 4 spaces (one indentation level) from the initiating line.  This makes the code history cleaner as new lines do not need to change the list argument by adding the comma and return line.

We prefer not to put the closing parenthesis on the same line as the final keyword argument:

``` python
def __repr__(self):
    return "{class_name}({first_name}, {last_name}, {age})".format(
        class_name=type(self).__name__,
        first_name=repr(self.first_name),
        last_name=repr(self.last_name),
        age=self.age)
```

We also do not like to see multiple arguments on one line:

``` python
def __repr__(self):
    return "{class_name}({first_name}, {last_name}, {age})".format(
        class_name=type(self).__name__, first_name=repr(self.first_name),
        last_name=repr(self.last_name), age=self.age)
```

We also prefer not to adhere to this (also very common) code style:

``` python
def __repr__(self):
    return "{cls}({first}, {last}, {age})".format(cls=type(self).__name__,
                                                    first=repr(self.first_name),
                                                    last=repr(self.last_name),
                                                    age=self.age)
```

## Looping

### While Loops

We use ``while`` loops very rarely.  If we need an infinite loop, we'll use ``while True``:

``` python
while True:
    print("do something forever")
```

Typically if we find we are using a ``while`` loop, we'll consider whether we could either:

1. Rewrite the loop as a ``for`` loop
2. Create a generator function that hides the ``while`` loop and loop over the generator with a ``for`` loop

### Looping with Indexes

We never want to see this in my code:

``` python
for i in range(len(colors)):
    print(colors[i])
```

If we ever see ``range(len(colors))``, we consider whether we actually need an index.

If we are using an index to loop over multiple lists at the same time, we'll use ``zip``:

``` python
for color, ratio in zip(colors, ratios):
    print("{}% {}".format(ratio * 100, color))
```

If we do really need an index, we'll use ``enumerate``:

``` python
for num, name in enumerate(presidents, start=1):
    print("President {}: {}".format(num, name))
```

### Embrace Comprehensions

Whenever we have a loop that converts one iterable into another, we try to convert it to a comprehension instead.

This is how we usually start:

``` python
doubled_odds = []
for n in numbers:
    if n % 2 == 1:
        doubled_odds.append(n)
```

This is what we prefer to refactor that to:

``` python
doubled_odds = [
    n * 2
    for n in numbers
    if n % 2 == 1
]
```

If we can think up a way to rewrite a loop as mapping an iterable to an iterable, we will attempt to do so and see whether we like the output.

## Comprehensions

We like list comprehensions.

### Line Wrapping Comprehensions

We prefer to write list comprehensions, set comprehensions, dictionary comprehensions, and generator expressions on multiple lines.

We like to add line breaks between the mapping, looping, and (optional) conditional parts of a comprehension:

``` python
doubled_odds = [
    n * 2
    for n in numbers
    if n % 2 == 1
]
```

We do not like to wrap my comprehensions in places besides between the three parts:

``` python
doubled_odds = [
    n * 2 for n
    in numbers if
    n % 2 == 1
]
```

My preferred wrapping style for list comprehensions is very similar to the style we prefer for wrapping function calls.

We wrap dictionary comprehensions like this:

``` python
flipped = {
    value: key
    for key, value in original.items()
}
```

``` python
flattened = [
    n
    for row in matrix
    for n in row
]
```

When we use generator expressions inside a function call, we only use one set of parenthesis and we prefer to wrap them over multiple lines:

``` python
sum_of_squares = sum(
    n ** 2
    for n in numbers
)
```

For a very short comprehension, we often find it acceptable to use just one line of code:

``` python
sum_of_squares = sum(n**2 for n in numbers)
```

We almost always use multiple lines when there's an conditional section or when the mapping or looping sections are not very short.

## Conditionals

We do not use parenthesis around conditional expressions in ``if`` statements unless they wrap over multiple lines.

### Inline If Statements

Consider using inline ifs if assigning to or returning two things.

Instead of this:

``` python
if name:
    greeting = "Hello {}".format(name)
else:
    greeting = "Hi"
```

Consider using this:

``` python
greeting = "Hello {}".format(name) if name else "Hi"
```

Also consider splitting inline ``if`` statements over multiple lines for improved readability:

``` python
greeting = (
    "Hello {}".format(name)
    if name
    else "Hi"
)
```

### Truthiness

Instead of checking emptiness through length or other means:

``` python
if len(results) == 0:
    print("No results found.")

if len(failures) > 0:
    print("There were failures during processing.")
```

Rely on truthiness to check for emptiness:

``` python
if not results:
    print("No results found.")

if failures:
    print("There were failures during processing.")
```

Do not rely on truthiness for checking zeroness or non-zeroness though.

Instead of this:

``` python
if n % 2:
    print("The given number is odd")

if not step_count:
    print("No steps taken.")
```

Do this:

``` python
if n % 2 == 1:
    print("The given number is odd")

if step_count == 0:
    print("No steps taken.")
```

### Conversion to bool

If you ever see code that sets a variable to ``True`` or ``False`` based on a condition:

``` python
if results:
    found_results = True
else:
    found_results = False

if not failures:
    success = True
else:
    success = False
```

Rely on truthiness by converting the condition to a ``bool`` instead, either explicitly for the truthy case or implicitly using ``not`` for the falsey case:

``` python
found_results = bool(results)

success = not failures
```

Keep in mind that sometimes no conversion is necessary.

The condition here is already a boolean value:

``` python
if n % 2 == 1:
    is_odd = True
else:
    is_odd = False
```

So type-casting to a ``bool`` would be redundant.  Instead simply set the variable equal to the expression:

``` python
is_odd = (n % 2 == 1)
```

### Long if-elif chains

Instead of using many ``elif`` statements, consider using a dictionary.  This alternative is often (but not always) possible.

``` python
words_to_digits = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
}
numbers.append(translation.get(n, " "))
```

## Strings

In Python 3.6+, we use f-strings for combining multiple strings.

We usually prefer f-strings or the ``format`` method over string concatenation.

If we am joining a list of values together, we use the ``join`` method instead.

For string literals with line breaks in them, we often prefer to use a multi-line string combined with ``textwrap.dedent``.  We may occasionally use ``'\n'.join()`` instead.

## Regular Expressions

Avoid using regular expressions if there's a simpler and equally accurate way of expressing your target search/transformation.

Unless your regular expression is extremely simple, always use a multi-line string and ``VERBOSE`` mode when representing your regular expression.

## Docstrings

Docstrings must follow the ``google`` documentation [style guide](https://google.github.io/styleguide/pyguide.html).

More information can be found [here](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html).

## Testing

The project uses ``flake8`` to check for style in code and docstrings.  Please review the output of the style report in the pipeline before submitting a pull request.

The ``flake8`` report is not a guarantee that the style of the code and the documentation abides by the rules of this style guide.

Style errors are considered unit test errors, this includes tests for the examples in docstrings.  Docstring example code tests are executed using [doctest](https://docs.python.org/3/library/doctest.html).
