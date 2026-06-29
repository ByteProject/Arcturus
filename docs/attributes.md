# Arcturus standard attributes and properties

The standard attributes and value properties Cosmos defines, with what each does.
An attribute is a boolean flag set by naming it (`fixed`) or clearing it
(`fixed false`); a value property holds a value (`name "brass lamp"`). Both are
read with `is` / the dot and tested in handlers. This is the author reference;
the storage details are in docs/04.

## Standard attributes

| Attribute | Meaning and usage |
|---|---|
| `fixed` | The object cannot be taken; it stays where it is. `take` refuses it. |
| `scenery` | Background detail: still referable for `examine`, but left out of the room's contents listing and not takeable (gives the scenery line). |
| `hidden` | Out of scope entirely until cleared: an undiscovered object, neither listed nor referable. Clear it when the object is revealed. |
| `concealed` | In scope and actable, but omitted from the room's contents listing (a thing present but not spelled out in the description). |
| `wearable` | Can be worn; the `wear` verb accepts it. |
| `worn` | Currently worn. Set by `wear`, cleared by `drop` / `take_off`. Inventory tags it "(worn)". |
| `lit` | Gives light. On a `room`, the room is independently lit; on a thing, the thing glows and lights its location. Light is otherwise computed. |
| `edible` | Can be eaten; the `eat` verb consumes it rather than refusing. |
| `named` | A proper-named thing (Linda, Excalibur). Takes no article: `${the noun}` and `${a noun}` print just the name. |
| `an` | The indefinite article is "an", not "a". The compiler derives it from the name's first letter (vowel -> `an`); set `an` or `an false` only for an exception (an hour, a unicorn). |
| `switchable` | Can be switched on and off; the `switch` verb applies. |
| `openable` | Can be opened and closed; the `open` / `close` verbs apply. |
| `open` | Currently open (a container or door). Set by `open`, cleared by `close`. A closed container hides its contents from scope. |
| `lockable` | Can be locked and unlocked with a key (the `lock` / `unlock` verbs). |
| `locked` | Currently locked; blocks `open` until unlocked with the matching key. |
| `visited` | The room has been entered before (Cosmos sets it on entry). Use it to vary a room's description on return. |
| `moved` | Set the first time the player takes an object. While clear, the object shows its `intro` text in a room description instead of the plain listing. |
| `animate` | A living thing (a person or creature). The conversation and give verbs apply only to the animate; the `person` kind sets it by default. |

## Kind attributes

The standard kinds are also attributes under the hood, set by `of <kind>` and
tested with `is <kind>`: `thing`, `room`, `container`, `supporter`, `door`,
`person`. So `if noun is container` and `if here is room` work like any attribute
test. An object carries the attribute of every kind in its chain.

## Standard value properties

| Property | Type | Meaning and usage |
|---|---|---|
| `name` | text | The printed short name ("brass lantern"). Distinct from the object's id and from `words`. |
| `desc` | text | The description shown by `examine` (and on first look at a room). |
| `words` | list | The vocabulary the parser matches: the object's nouns and adjectives, as equal entries. Typed but not printed. |
| `intro` | text | An object's initial appearance in a room, shown as its own paragraph while the object is untouched (`moved` clear). |
| `capacity` | number | How many objects a container or supporter holds. |
| `key` | object | The object that locks/unlocks this one (for `lockable` things). |

`score`, `max_score`, and `turns` are runtime globals, not object properties (see
docs/02 section 2).
