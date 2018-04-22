# Test Harness for 601.[346]28 Compilers 🎉

**A crowdsourced collection of test cases for @phf's compiler's course.**


## How Do I Use It?

```
$ git clone https://github.com/baileyparker/phf-compilers-tests integration_tests
$ ./integration_tests/bin/run_harness
```

The second command will run the test harness against the `./sc` compiler. If
you can't run your compiler with `./sc` from the current directory you can
add the `--sc` argument to let the test harness know where your compiler is:

```
$ ./integration_tests/bin/run_harness --sc ../../path/to/my/sc
```

For convenience, I recommend adding a target to your `Makefile` to run this:

```
integration-test:
	./integration_tests/bin/run_harness

.PHONY: integration-test
```

Don't forget if you've cloned this repo into your own repo (for versioning
your compiler) to add `integration_tests/` to your `.gitignore`.


### Getting the Latest Test Cases

This repo's `master` should always be safe, so you can just pull:

```
$ git -C 'integration_tests' pull origin master
```


### Advanced Usage

You can run the test suites for only certain phases of the compiler by
specifying them as arguments to `run_harness`. The phases so far are:

  - `scanner`
  - `cst`
  - `st` (symbol table)
  - `ast`
  - `interpreter`

For example, to run just the scanner and symbol table:

```
$ ./integration_tests/bin/run_harness scanner ast
```

#### Optional Flags

##### Skipping Semantically Invalid CST Fixtures
For assignments after the CST, if your compiler is implemented in such a way
that even if the `-c` is passed the semantic analysis (symbol table and AST)
are still run, those later phases may find semantic errors in a CST fixture
(that alone would pass `-c`, because it is syntactically valid, but would fail
semantic analysis and thus fail the test). Although you should design your
compiler in a way that these phases can be turned off, that may be more trouble
than it's worth. So, to prevent false negatives, pass `--skip-cst-passes`
(after the CST assignment):

```
$ ./integration_tests/bin/run_harness --skip-cst-passes
```

##### Symbol Table `5`s
For the Symbol Table assignment (before the AST assignment), your symbol table
should replace all constant integer values with `5`. But then for the AST
assignment and after, the constants should be the proper (constant folded)
values. For the Symbol Table assignment, you should run the harness with
`--st-all-fives` to assert that all constant integers values are indeed `5`:

```
$ ./integration_tests/bin/run_harness --st-all-fives
```

## Contributing New Test Cases

You are too kind 😄! The process is pretty straightforward (it's the standard
[open source pull request](https://www.digitalocean.com/community/tutorials/how-to-create-a-pull-request-on-github)
workflow):

  1. Fork [this repo](https://github.com/baileyparker/phf-compilers-tests)
  2. `git clone https://github.com/YOUR-USERNAME/phf-compilers-tests`
  3. Create a branch describing the test cases you're adding:
     `git checkout -b bogosort-scanner-fixture`
  4. Add, commit, and push your changes: `git add simple_test/fixtures`,
     `git commit -m "Add bogosort scanner fixture"`,
     `git push origin bogosort-scanner-fixture`
  5. [Create a pull request](https://help.github.com/articles/creating-a-pull-request/)
     from Github

### Structure of Test Cases

There are fixtures in `simple_test/fixtures`. A fixture is a pair of two files
that provide input to the compiler and describe the expected output:

  1. A `*.sim` file (called the **input file**) that will be given to the
     compiler under test
  2. A `*.{scanner|cst|st|ast}` file (called the **phase file**) that described
     what the expected output of running the compiler under test in the phase
     described by its file extension against the `*.sim` file of the same name

In a line (*if you trust your compiler!*), a fixture for the scanner can be
created like so (assuming `quicksort.sim` exists):

```
./sc -s simple_test/fixtures/quicksort.sim 2>&1 > simple_test/fixtures/quicksort.scanner
```

Notice how the name of the files (without the extension) matches. This is how
the test harness knows to feed the input sim file in to the compiler under test
and expect the output `*.scanner` file. The test harness derives the phase to run
the compiler in from the extension of the second file, currently the phases are:

  - `*.scanner` - `./sc -s`
  - `*.cst` - `./sc -c`
  - `*.st` - `./sc -t` (**do not** replace all `INTEGER` values with `5`s in
    these files!)
  - `*.ast` - `./sc -a`
  - `*.*.run` - `./sc -i` (see **About Runs** below)

More will be added with future assignments.

Note that one input `*.sim` file can have multiple expected outputs for
different compiler phases (ex. `random.scanner` and `random.cst` are two
phase files that describe the expected output for `./sc -s`, the scanner, and
`./sc -c`, the parser, respectively when given the input `random.sim`).

The second file should contain both the expected stdout and stderr from running
the simple compiler on the input `*.sim` file. An example of this file is:

```
identifier<ics142>@(4, 9)
:@(10, 10)
ARRAY@(12, 16)
integer<5>@(18, 18)
OF@(20, 21)
identifier<INTEGER>@(23, 29)
;@(30, 30)
eof@(32, 32)
```

Lines in this file that begin with `error: ` are not expected to be present in
stdout. Instead, it signals to the test harness that the compiler should print
at least one error to stderr. Note that while we can append a description to
these error lines (to make the fixture clearer to anyone reading it to
understand why their compiler fails for it), the test harness will not check if
the line exactly matches.

So a `foobar.scanner` file like this:

```
identifier<ics142>@(4, 9)
:@(10, 10)
error: bad character ';' at line 1, col 11
```

Will accept output from the simple compiler under test with a different message
(as long as the error is in the same place):

```
identifier<ics142>@(4, 9)
:@(10, 10)
error: unexpected `;`@(11, 11)
```

The test will fail though if the output looks like this (note how the error is
too early):

```
identifier<ics142>@(4, 9)
error: unexpected ';' at (11, 11)
```

#### About Runs

The interpreter and later assignments pose a different paradigm than previous
assignments and therefore require some specialized testing machinery. Whereas
before tests only had to invoke the compiler and then assert that the output
matches, the interpreter introduces a two step process wherein the input is
fed into the compiler and then the program (running in the interpreter) is
interacted with (while output and errors are asserted). To facilitate this,
`*.*.run` files have been introduced.

Run files encapsulate the input, output, and errors of one interactive session
running a simple program. Imagine if did `./sc -i some_file.sim` and then
captured all of the your input and the output/errors—that would be the run
file.

A run file named `name.subname.run` has two parts: the sim name and run name.
The sim name ties a run to a `*.sim` file. The run name allows you to create
multiple runs (with descriptive names) for one `*.sim` file.

For example, `matrix_multiply.small.run` is a run file that represents input
and expected output/errors of running `./sc -i matrix_multiply.sim`. The
run name (`small`) names the run and tells you that this run probably exercises
the program with small matrices as input. Because of the run name, you can
additionally create `matrix_multiply.identity.run` and
`matrix_multiply.large.run` (both of which are associated with
`matrix_multiply.sim`) to test different inputs on your program.

The anatomy of a run file is very similar to normal phase files. They should be
treated as a list of sequential actions/expectations. Any line starting with a
number is an expectation that the program will next `WRITE` a line containing
that number. Any line beginning with `error: ` indicates that the program is
expected to error at this point and exit with a non-zero status code. Run files
add an additional syntax for input: `> 123` means that at this point the number
`123` should be written to the program's `stdin`.

For organization, run files also support Python-style line comments (starting
with `#`) and empty lines.

##### Compile Time Errors

This assignment also supports asserting that certain compile time errors
occurred for either just the decent code generator or both the decent and silly
code generators. The syntax uses a line containing `-----` to separate the
different times that an error can occur.

```
error: this error must occur for only the decent code generator (1)
-----
error: this error must occur also for the silly code generator (2)
-----
# Normal run file from here down...
> 1   # interpreter runs until it hits the error
1
2
error: this error occurred at runtime (3)
```

You should specify errors for all cases so that the run file will work with all
three phases of tests.

If, for example, you have a compile time error that you only expect to occur
for the decent code generator you can do:

```
error: constant array index out of bounds
-----
-----
# Normal run file from here down...
> 1   # interpreter/silly codegen runs until it hits the error
1
2
error: array index of out bounds
```

If there are no compile time errors, you can omit the `-----` sections. Having
none of them is equivalent to having two empty compilation error sections:

```
-----
-----
> 5
1
2
3
4
5
```

##### Example

**binary_search.small.run:**


```
> 10  # input the size of the array

# Input each element in the array
> 88
> 1
> 13
> 14
> 50
> 21
> 18
> 14
> 75
> 10

10   # the length of the array is echoed back

# Then the array is printed in sorted order
1
10
13
14
14
18
21
50
75
```


**multiply\_and\_divide.by_zero.run:**

```
> 10  # input a
> 0   # input b

0     # a * b

# a DIV b
error: division by 0
```

#### Some Housekeeping

  - Test fixtures must have `snake_case_names`.
  - There should not be duplicate input files (`*.sim` files). If `a.sim` and
    `b.sim` are identical, then you should merge their phase files.

### Running the Test Harness Tests

To ensure a bug free harness, I've written tests for the test harness itself
(I know, [so meta](https://www.xkcd.com/917/), right?). To run them, you need
[pipenv](https://docs.pipenv.org/) to pull in the required dependencies (a
simple `python3 -m pip install pipenv` should suffice, although you may need
to `sudo apt install python3-pip` first).

To run the tests:

```
$ pipenv run python3 setup.py test
```

In a very opinionated new pattern that I'm trying, linting and mypy static
checks are two of the test cases. If the code fails typechecking or linting,
the tests fail.

To get test coverage reports:

```
$ pipenv run python3 setup.py coverage
```

To ensure the test harness really works, there are some very comprehensive
integration tests that test all components together against a faked compiler.
This, of course, involves a lot of file I/O and takes a decent amount of time
to run (about 30 seconds on a 2017 MBP). You can of course run tests
individually with (for example):

```
$ pipenv run python3 -m tests.simple_test.test_main
```

But you can also pass the environment variable `SLOW_TESTS=0` to exclude these
slow integration tests (as well as linting, which also takes a few seconds):

```
$ SLOW_TESTS=0 pipenv run python3 setup.py coverage
```


## Requirements

  - Peter's Lubuntu VM (Lubuntu 16.04)
  - Python 3.5 (already on the VM)
  - Pipenv (to run the meta tests, the tests that test the test harness)


## Contributors

Harness made by [Bailey Parker](https://github.com/baileyparker). Special
thanks to these wonderful people who contributed test cases:

  - [Nicholas Hale](https://github.com/nhaleft)
  - [Sam Beckley](https://github.com/sobeckley)
  - [Peter Lazorchak](https://github.com/lazorchakp)
  - [Rachel Kinney](https://github.com/rkinney4)
  - [Andrew Rojas](https://github.com/amrojas)
  - [Tristan Orton-Urbina](https://github.com/Solian42)
  - Your name could be here!


## Reporting Bugs

If you find a bug in the test harness or in one of the fixtures, please
[file an issue](https://github.com/baileyparker/phf-compilers-tests/issues).
