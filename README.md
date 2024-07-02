# settlers.py

This is a Python program for generating layouts for the Settlers of Catan board game. Settlers of Catan is copyright 2020 by Catan GmbH and Catan Studio. I have no association with either organization. This settlers.py code is copyright 2024 by Craig "Ichabod" O'Brien, and is released under the [GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

## Usage

For standard layouts, just make an instance of the CatanMap class, call its layout function, and print the instance.

```python
board = CatanMap()
board.layout()
print(board)
```

The layout method has parameters for using different layout rules:

* num: How the numbers are arranged. Can be 'beginner' for the beginner layout, 'standard' for the standard number spiral, or 'shuffle' for random placement.
* terr: How the terrain hexes are arranged. Can be 'beginner' for the beginner layout or 'shuffle' for random placement.
* port: How the ports are arranged. Can be 'beginner' for the beginner layout or 'shuffle' for random placement.

The default is the variable set up. 

There is also the validate parameter to the layout method. This can be used to constrain the board layout to meet certain critera. The value for this is a tuple of validator functions. Several functions are provided to create validator functions for common layout house rules.

* good_rock(n): There must be a mountain hex with at least n pips. 
* max_pip(n): No intersection may have more than n pips.
* no_2_12(): The 2 and the 12 may not be next to each other.
* no_6_8(): No two five pip numbers (6 or 8) may be next to each other.
* no_double_6_8(): No single terrain type can have two five pip numbers.
* max_port_pips(n): No port can be next to more than n pips of its own production.
* no_num_pairs(): Two of the same number may not be next to each other.
* no_terr_pairs(t): Two of the same terrain type may not be next to each other.
* no_terr_tri(): No intersection may be three of the same terrain type.
* regions(t): All terrain hexes must be next to another of the same type, except terrain in t (typically 'DSRT', to avoid infinite loops).

For example, the following code creates a layout following the Catan 3D layout rules:

```python
board = CatanMap()
valid = (no_6_8(), no_num_pairs())
board.layout(num = 'shuffle', validate = valid)
print(board)
```

### Other Boards

A Catan56Map class is provided for 5/6 player layouts. Normally, this puts a space between each port. However, later editions of the game use a frame, which space out the ports differently. To get the frame layout, you need to create the instance with the use_frame parameter being True:

```python
board = Catan56Map(use_frame = True)
board.layout()
print(board)
```

## Advanced Usage

### Criteria Functions

If you want to add criteria, the criterian functions should accept a single parameter. The return value should be False for a layout not meeting the criteria, and True for a layout meeting the criteria. 

None of the functions given in settlers.py are criteria functions, they return criteria functions. This was done for consistent usage with functions like max_pip(n), which needs a parameter to define the criteria function.

### Other Hex Arrangements

The HexMap class that CatanMap is based on allows for creating arbitrary hex maps for whatever Settlers scenario you might want. It has a build method meant to be overridden for making different maps. HexClass has several helper methods for doing building maps: start_hex, grow_hex, grow_map, surround_hex, and surround_map. See CatanMap.build and Catan56Map.build for examples.

There is the HexMap.arrange method. This is used in CatanMap to define the columns and spiral used in the standard layout for ordering the tiles and numbers, respectively. You may need to override that for particularly odd layouts.
