# popscript-upgrader

Converts the computer-player scripts of *Populous: The Beginning* (the 1998 script language,
`CPSCRnnn.SCR` / `CPSCRnnn.DAT`) to Script4 Lua for Populous: The Beginning 1.5.

The output is plain Lua built on the game's standard library (`std.cpscript`). It is meant to be
read and edited, and it is meant to behave exactly like the script it came from: same decisions,
on the same turns, in the same order.

```lua
ai:run(function()
    if getTurn() == 0 then
        STATE_SET(me, ON, CP_AT_TYPE_FETCH_WOOD)
        attr.EXPANSION = 12
        SET_ATTACK_VARIABLE(me, ai:slot("USER_RESULT"))
    end

    -- Every 512 turns: attack blue if there are enough warriors
    if ai:every(512, 64) then
        if cp.all(PLAYERS_PEOPLE_OF_TYPE(me, M_PERSON_WARRIOR) > 5, G_RANDOM(100) < 70) then
            ATTACK(me, TRIBE_BLUE, 6, ATTACK_BUILDING, M_BUILDING_DRUM_TOWER, 999, M_SPELL_BLAST,
                   M_SPELL_NONE, M_SPELL_NONE, ATTACK_NORMAL, 0, -1, -1, -1)
            v.USER_ATTACKS = v.USER_ATTACKS + 1
        end
    end
end)
```

## What it reads

| Input | Notes |
|---|---|
| Bullfrog script text (`.SCR`) | `COMPUTER_PLAYER n`, `BEGIN` / `END`, `IF (( A == 1 ) && ( B > 2 ))` |
| World Editor script text (ALACN's editor) | `{` / `}`, `$variables`, `IF ( $a == 1 && $b > 2 )`, `/* */` comments |
| Compiled scripts (`CPSCRnnn.DAT`) | what the game and most mods actually ship |
| Level headers (`LEVL2nnn.HDR`, or the single-file `LEVL3` `.DAT`) | say which script drives which tribe |

The syntax of a text file is detected automatically. Comments are kept and stay next to the
statement they were written beside.

Give a `.SCR` **and** its `.DAT` and the converter uses both: the compiled script decides what the
program is, the text supplies the variable names and comments. That matters more than it sounds;
see [The compiled script is the authority](#the-compiled-script-is-the-authority).

## Requirements

- Python 3.8 or newer. The converter itself has no dependencies.
- The tests need Lua 5.3 through `pip install lupa`.
- The Lua output needs Populous: The Beginning 1.5 with the standard library (`Scripts/std/v0.0.1`)
  that includes `cpscript.lua`. A copy of that file is in `std/` for reference.

## Use

```text
python -m popscript_upgrader convert CPSCR010.SCR -o ai_p1.lua --tribe 1
python -m popscript_upgrader convert CPSCR010.SCR CPSCR010.DAT -o ai_p1.lua   (text checked against compiled)
python -m popscript_upgrader convert cpscr010.dat -o ai_p1.lua                (compiled only)

python -m popscript_upgrader level 1-25 --game "C:\Games\Populous" -o Scripts\campaign
python -m popscript_upgrader all --game "C:\Mods\MyMod" -o Scripts\mymod

python -m popscript_upgrader custom --header mylevel.hdr --scripts my_scripts -o Scripts\mylevel
python -m popscript_upgrader custom --tribe 1=10 --tribe 2=11 --scripts my_scripts -o Scripts\mylevel

python -m popscript_upgrader check CPSCR010.SCR             (report problems, write nothing)
python -m popscript_upgrader text cpscr010.dat --to worldeditor -o cpscr010.txt   (decompile)
```

`--tribe` is the tribe number the script drives: 1 red, 2 yellow, 3 green.

### Whole levels

`level` and `all` read each level's header, find the script of every computer tribe and write one
folder per level:

```text
Scripts/campaign/lvl01_the_journey_begins/
    ai_p1.lua        the script for tribe 1
    harness.lua      loads the files above
```

Start the level with the harness:

```text
pop3.exe /level 1 /dscript campaign/lvl01_the_journey_begins/harness.lua
```

`--game` is the folder that holds `levels/`. Script text is looked for in `<game>/CpScript` (or
`--scripts DIR`) and compiled scripts in `<game>/levels`. The output folder should be inside the
game's `Scripts` folder; if it is somewhere else, pass `--scripts-root` so the `include()` paths
come out right.

### A custom level, or a pasted header

`custom` takes a header from a file or from text. The text can be a hex dump (with or without
offsets and an ASCII column) or base64, in a file or on standard input:

```text
python -m popscript_upgrader custom --header - --scripts my_scripts -o Scripts\mylevel
(paste the dump, then end the input: Ctrl+Z, Enter on Windows)
```

No header at hand? Name the scripts yourself with `--tribe N=SCRIPT`. Both can be combined;
`--tribe` wins.

## What "exactly like the original" means here

- **Same point in the turn.** The engine calls `OnComputerPlayerScript(tribe)` where that tribe's
  bytecode used to run: tribes in ascending order, each before its own decision pass.
  `std.cpscript` runs the converted script from there and switches the bytecode off.
- **`EVERY`** is the original test, `((turn + tribe + offset - 1) & (period - 1)) == 0`, staggered
  by tribe.
- **Conditions evaluate both sides.** The original had no short-circuit, and reading
  `INT_RANDOM_100` draws a random number. Where Lua's `and` / `or` could skip such a read the output
  uses `cp.all` / `cp.any`.
- **Variables live in the engine**, in the original slots. The engine writes attack results into
  them, and they are part of saved games.
- **Arithmetic** is 32-bit; `DIVIDE` rounds toward zero and gives 0 on division by zero
  (`cp.div`); attributes keep one byte.
- **Every call was checked against the engine source**: the interpreter's handler for the command
  on one side, the Lua function's body on the other, argument by argument. The table is
  `popscript_upgrader/data/language.json`.

### The compiled script is the authority

The 1998 compiler had a bug in how it read numbers: some came out with a stray extra digit.
`EVERY 2048 1088` in the source of level 23's script was compiled as `EVERY 2048 10881`, and that
is what the game has run ever since. It also dropped words it did not recognise without saying so
(a misspelt `MULTPLY` in level 14's script never ran).

So when both files are given, the output follows the `.DAT`, and every place where the text
disagrees is marked in the Lua:

```lua
-- NOTE: the source says EVERY 2048 1088; the compiled script, which is what the game runs,
--       has EVERY 2048 10881 (the 1998 compiler appended a stray digit)
if ai:every(2048, 10881) then
```

Eleven of the original campaign scripts differ from their source this way.

A script given as text only is converted as written.

### What does not convert

- `DO STATE_MED_MAN_DEFEND`: the interpreter has no handler for it; the original script hangs.
- Scripts written for an older version of the language (an `ATTACK` with fewer operands, unknown
  commands). The game cannot run those either. The error names the line.

Some functions act on the local player's screen (messages, camera, tooltips). They follow the
game's `/noscriptmsg` option, which the original scripts ignored for a few of them.

## Tests

```text
python tools/extract_bindings.py <engine>/Source          read the Lua function signatures from the C++
python tools/build_engine_api.py script4_spec.json        check the table against the engine's API
python tests/oracle.py <game>                             parser vs the game's compiled scripts
python tests/oracle_reconcile.py <game> -v                list every source/compiled difference
python tests/differential.py <game>                       generated Lua vs a model of the interpreter
python tests/differential.py <game> --dats <mod>/levels   the same for a mod's compiled scripts
python tests/synthetic.py <game>                          random programs: every command, both syntaxes
python tests/mutation.py <game>                           do the tests notice a broken converter?
python tests/stdlib_helpers.py <game>                     the hand-writing helpers of std.cpscript
```

- **oracle** parses each `CPSCRnnn.SCR` and decodes the matching `CPSCRnnn.DAT`; the two trees must
  be the same program.
- **differential** runs the generated Lua in a real Lua 5.3 on the real `std/cpscript.lua`
  against a mock engine, runs `tests/refinterp.py` (a model of `Source/Script.cpp`) on the same
  script, and compares every state-changing engine call and every variable, turn by turn. The mock
  rejects unknown functions, wrong argument counts and non-integer arguments.
- **synthetic** builds random programs from the language table, prints them in both syntaxes,
  parses them back and runs the differential test on each.
- **mutation** breaks the generator and the library in fourteen ways and requires the tests to
  notice every one.

In the game itself: record a level with the original scripts (`/record`), then replay the
recording with the converted Lua loaded. The replay compares the simulation checksum on every turn
and must stay on rails. Done this way for the 25 campaign levels (about 3,580 turns each, every computer
tribe converted), no turn mismatched; a deliberately altered script fails the same check within
200 turns.

## Layout

```text
popscript_upgrader/
    source.py      text parser, both syntaxes
    compiled.py    .DAT decoder
    reconcile.py   make the text agree with the compiled script
    luagen.py      Lua generator
    printer.py     script text writer (decompile, change syntax)
    level.py       level headers
    project.py     whole levels and mods
    cli.py         command line
    data/language.json   every command, variable and keyword with its Lua equivalent
std/cpscript.lua   copy of the runtime module from the game's standard library
tests/  tools/  examples/
```

`script2_to_script4.py -f IN OUT` and `-b IN_DIR OUT_DIR` still work and call the new converter.
