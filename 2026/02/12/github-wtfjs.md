# [Funny and tricky JavaScript examples](https://github.com/denysdovhan/wtfjs/blob/master/README.md)

This readme was referenced by [an article on JavaScript](../../../2025/12/06/arstechnica-javascript-turns-30.md). It answered seven questions about this programming language.

## Why is it that an empty array equal not empty array in JavaScript?

```js
[] == ![]; // -> true
```

Because both are cast to the same type (number) before being compared (that's how non-strict comparisons are done in JS), and both sides happen to arrive at the same number: 0.

> The abstract equality operator converts both sides to numbers to compare them, and both sides become the number 0 for different reasons.

Cast to a number, an empty array is 0. Not empty array is a boolean false, which also happens to cast to 0.

```js
+[] == +![];
0 == +false;
0 == 0;
true;
```

## Why is it that NaN does not equal NaN in JavaScript?

NaN is unequal to any value in JS, including itself.

```js
NaN === NaN; // -> false
```

The presence of NaN signifies an invalid numeric result, so it was determined that comparisons involving it should return false. If you need to know if both numeric results returned NaN, use Object.is(NaN, NaN).

## Are 0 and -0 strictly equal?

Not in JavaScript.

```js
Object.is(-0, 0); // -> false
```

However, JavaScript does recognize that 0 and -0 have the same value.

```js
-0 === 0; // -> true
```

## Are truthy values always equal to true in JavaScript? 

No, an empty array is truthy but not true.

```js
!![]       // -> true
[] == true // -> false
```

A truthy value selects the if-path (rather than the else-path) in a conditional statement whereas true is a symbol. Null is another example of truthy ≠ true.

```js
!!null; // -> false
null == false; // -> false
```

It shouldn't be surprising that falsy values similarly aren't always equal to false in JavaScript, but there are counterexamples.

```js
0 == false; // -> true
"" == false; // -> true
```

## In JavaScript, if null > 0 is false and null >= 0 is true, does that mean that null == 0 is true? 

No, null == 0 is false. Abstract equality comparisons (==) are different from relational comparisons (>, <, >=, <=) in JS.

> The number conversion doesn't actually happen on a side that is null or undefined. Therefore, if you have null on one side of the equal sign, the other side must be null or undefined for the expression to return true. Since this is not the case, false is returned. Next, the relational comparison null > 0. The algorithm here, unlike that of the abstract equality operator, will convert null to a number.

null > 0 and null < 0 both evaluate to false because, unlike in the == case, the interpreter will case null to a number here. Consequently, null <= 0 and null >= 0 will both evaluate to true because they're implemented as negations of null > 0 and null < 0, respectively.

## Is passing undefined to a JavaScript function the same as not passing an argument at all? 

No, depending on the function, you may get a different result for an undefined argument vs. no argument.

```js
Number(); // -> 0
Number(undefined); // -> NaN
```

## Why is it invalid to call 27.toString() in JavaScript? 

Because JS treats a period after a number as a decimal. At the decimal, you haven't finished specifying a number yet, so a call to one of its member methods is invalid there. 

> The . character presents an ambiguity. It can be understood to be the member operator, or a decimal, depending on its placement. The specification's interpretation of the . character in that particular position is that it will be a decimal.

# Next

* [In 1995, a Netscape employee wrote a hack in 10 days that now runs the Internet](../../../2025/12/06/arstechnica-javascript-turns-30.md)
