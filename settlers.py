"""
settlers.py

Random setups with constraints for Settlers of Catan.

Constants:
PORT_TO_TERR: Conversion of port types to matching terrain types. (dict)
TERR_TO_PORT: Conversion of terrain types to matching port types. (dict)

Classes:
Hex: A Hexagon in a hexagonal tiling. (object)
CatanHex: A hexagon for the Settlers of Catan boardgame. (Hex)
HexMap: A map made of tessellated hexes. (object)
CatanMap: A Settlers of Catan board. (HexMap)
Catan56Map: A 5/6 player Settlers of Catan board. (CatanMap)

Functions:
good_rock: Make a validator for an ore with at least n pips. (callable)
max_pip: Make a validator for no intersection with more than n pips. (callable)
mean_dev: Calculate the mean and standard deviation of a sequence. (tuple)
no_2_12: Make a validator for 2 and 12 not being neighbors. (callable)
no_6_8: Make a validator for 6 and 8 not being neighbors. (callable)
no_double_6_8: Make a validator for no terrain with two 5 pip tiles. (callable)
max_port_pips: Make a validator for no port with > n of self pips. (callable)
no_num_pairs: Make a validator for no number neighboring itself. (callable)
no_terr_pairs: Make a validator for no terrain neighboring itself. (callable)
no_terr_tri: Make a validator of no triangles of the same terrain. (callable)
percentiles: Calculate and display percentiles for a sequence. (list)
regions: Make a validator requiring pairs of terrain types. (callable)
sample_data: Calculate statistics on simulated Catan set ups. (dict)
"""

import collections
import itertools
import math
import random

PORT_TO_TERR = {'BRICK': 'HILL', 'GRAIN': 'FIELD', 'ROCK': 'MNTN', 'SHEEP': 'PSTR', 
	'WOOD': 'FRST'}

TERR_TO_PORT = {'FIELD': 'GRAIN', 'FRST': 'WOOD', 'HILLS': 'BRICK', 'MNTN': 'ROCK', 
	'PSTR': 'SHEEP'}

class Hex(object):
	"""
	A Hexagon in a hexagonal tiling. (object)

	Attributes:
	id: A unique ID for the hexagon. (int)
	neighbors: The hexes adjacent to this one, by angle. (dict of int: Hex)
	x: An approximate x coordinate. (int)
	y: An approximate y coordinate. (float)

	Class Attributes:
	angles: The possible angles to the edges of the hexagon. (tuple of int)
	angles_xy: The approximate coordiates for each angle. (dict of int: tuple)
	next_id: The ID of the next Hex instance. (int)

	Methods:
	delete_neighbors: Delete the tile's neighbor links, both ways. (None)
	join_neighbors: Make adjacent neigbors link to each other. (None)
	new_neighbor: Link and give coordinates to a new neighbor. (None)
	text_block: Text representation using a grid of characters. (list of str)

	Overridden Methods:
	__init__
	__hash__
	__repr__
	__str__
	"""

	angles = (0, 60, 120, 180, 240, 300)
	angle_xy = {0: (0, -1), 60: (1, -0.5), 120: (1, 0.5), 180: (0, 1),
		240: (-1, 0.5), 300: (-1, -0.5)}
	next_id = 0

	def __init__(self):
		"""Set the ID and default attributes. (None)"""
		self.id = Hex.next_id
		Hex.next_id += 1
		self.x = 0
		self.y = 0
		self.neighbors = {angle: None for angle in self.angles}

	def __hash__(self):
		"""Generate a hash for the hex. (int)"""
		return hash(('Hex', self.id))

	def __repr__(self):
		"""Debugging text representation. (str)"""
		return f'<Hex id = {self.id} ({self.x}, {self.y})>'

	def __str__(self):
		"""Human readable text representation. (str)"""
		lines = [''.join(line) for line in self.text_block()]
		return '\n'.join(lines)

	def delete_neighbors(self):
		"""Delete the tile's neighbor links, both ways. (None)"""
		for angle in self.angles:
			target = self.neighbors[angle]
			if target is not None:
				target.neighbors[(angle + 180) % 360] = None
				self.neighbors[angle] = None

	def join_neighbors(self):
		"""Make adjacent neigbors link to each other. (None)"""
		for angle in self.angles:
			target = self.neighbors[angle]
			join = self.neighbors[(angle + 60) % 360]
			if target is not None and join is not None:
				target.new_neighbor((angle + 120) % 360, join)

	def new_neighbor(self, angle, neighbor):
		"""Link and give coordinates to a new neighbor. (None)"""
		# Link to the neighbor.
		self.neighbors[angle] = neighbor
		neighbor.neighbors[(angle + 180) % 360] = self
		# Give it coordinates based on the angle of the link.
		dx, dy = self.angle_xy[angle]
		neighbor.x = self.x + dx
		neighbor.y = self.y + dy

	def text_block(self):
		"""Text representation using a grid of characters. (list of str)"""
		lines = ['  _____']
		lines.append(r' /     \ ')
		lines.append(f'/ {self.id:^5} \\ ')
		lines.append(r'\       /')
		lines.append(r' \_____/')
		return lines

class CatanHex(Hex):
	"""
	A hexagon for the Settlers of Catan boardgame. (Hex)

	Attributes:
	terr: The terrain of the hex. (str)
	pips: The frequency of the hex's production. (int)
	port: A flag for the hex being a port hex. (bool)

	Properties:
	num: The number that causes the hex to produce. (int)

	Overridden Methods:
	__init__
	text_block
	"""

	def __init__(self, terr = 'NONE', num = 0, port = False):
		"""Set up the attributes of the hex. (None)"""
		# Set the Catan-specific attributes.
		self.terr = terr
		self.num = num
		self.port = port
		# Set the standard Hex attributes.
		super().__init__()

	def text_block(self):
		"""Text representation using a grid of characters. (list of str)"""
		if self.port:
			n = 3 if self.terr == 'ANY' else 2
			lines = ['', '', f'  {self.terr:^5}', f'   {n}:1']
		else:
			lines = ['  _____']
			lines.append(r' /     \ ')
			lines.append(f'/ {self.terr:^5} \\ ')
			if self.num:
				lines.append(f'\\ {self.num:^5} /')
			else:
				lines.append(r'\       /')
			lines.append(r' \_____/')
		return [list(line) for line in lines]

	@property
	def num(self):
		"""Make num a property (int)"""
		return self._num

	@num.setter
	def num(self, value):
		"""
		Modify the pips whenever the num is changed. (None)

		Parameters:
		value: The new value of the num property. (int)
		"""
		self._num = value
		self.pips = 6 - abs(7 - value)
	

class HexMap(object):
	"""
	A map made of tessellated hexes. (object)

	The build and arrange methods are meant to be overridden to make the map 
	and then group the hexes together in ways that are helpful for later
	processing. The _explore method is *NOT* meant to be overwritten, and sets 
	up data needed for printing the map.

	The start_hex, grow_foo, and surround_foo methods are meant to make it 
	easier to build maps when overridding the build method. See the CatanMap
	and Catan56Map classes for examples.
	
	Attributes:
	_base_hex: The default class for hexes on the map. (type)
	_base_params: Keyword parameters for initializing new hexes. (dict)
	hexes: All of the hexes in the map. (list of Hex)
	grow_hex: Grow neighbors for a hex in specified directions. (list of Hex)

	Methods:
	_explore: Set the boundaries of the map. (None)
	arrange: Group the hexes as needed for later processing. (None)
	build: Build the map by adding hexes to it. (None)
	find_hex: Find a particluar hex using its coordinates. (Hex)
	grow_hex: Grow neighbors for a hex in specified directions. (list of Hex)
	grow_map: Grow neighbors for each hex in the specified directions. (list)
	start_hex: Create a hex on the map. (Hex)
	surround_hex: Surround a hex with new hexes. (None)
	surround_map: Surround the map with a border of new hexes. (None)

	Overridden Methods:
	__init__
	__str__
	"""

	def __init__(self):
		"""Build the hexes for the map. (None)"""
		# Set the default attributes.
		self.hexes = []
		self._base_hex = Hex
		self._base_params = {}
		# Build the hexes in the map.
		self.build()
		# Analyze and orgainize the hexes on the map.
		self._explore()
		self.arrange()

	def __str__(self):
		"""Human readable text representation. (str)"""
		if self.hexes:
			# Create a grid of spaces big enough for all the hexes.
			width = self.bounds['right'] - self.bounds['left'] + 1
			height = int(self.bounds['bottom'] - self.bounds['top'] + 1.5)
			grid = [[' '] * (width * 7 + 2) for row in range(height * 4 + 1)]
			for tile in self.hexes:
				# Figure out where each hex goes.
				start_x = (tile.x - self.bounds['left']) * 7
				start_y = int((tile.y - self.bounds['top']) * 4)
				# Get the sub-grid of characters for that hex.
				text_block = tile.text_block()
				# Put the non-whitespace sub-grid character in at the right locations.
				for dy, row in enumerate(text_block):
					for dx, char in enumerate(row):
						if char != ' ':
							grid[start_y + dy][start_x + dx] = char
			# Join the rows of the grid into strings.
			rows = [''.join(row) for row in grid]
			# Eliminate blank rows at the top and bottom of the text image.
			while not rows[0].strip():
				rows = rows[1:]
			while not rows[-1].strip():
				rows.pop()
			# Return the remaining rows as a string.
			return '\n'.join(rows)
		else:
			# Return a blank string for empty maps.
			return ''

	def _explore(self):
		"""Set the boundaries of the map. (None)"""
		self.bounds = {'top': 0, 'left': 0, 'right': 0, 'bottom': 0}
		for tile in self.hexes:
			self.bounds['left'] = min(tile.x, self.bounds['left'])
			self.bounds['right'] = max(tile.x, self.bounds['right'])
			self.bounds['top'] = min(tile.y, self.bounds['top'])
			self.bounds['bottom'] = max(tile.y, self.bounds['bottom'])

	def arrange(self):
		"""Group the hexes as needed for later processing. (None)"""
		pass

	def build(self):
		"""Build the map by adding hexes to it. (None)"""
		pass

	def find_hex(self, x, y):
		"""
		Find a particluar hex using its coordinates. (Hex)

		Parameters:
		x: The x coordinate of the hex. (int)
		y: The y coordinate of the hex. (float)
		"""
		match = [tile for tile in self.hexes if tile.x == x and tile.y == y]
		if match:
			return match[0]
		else:
			raise ValueError(f'There is no hex at ({x}, {y})')

	def grow_hex(self, tile, angles, hex_class = None, hex_params = None):
		"""
		Grow neighbors for a hex in specified directions. (list of Hex)

		If not give (or None) the hex_class and hex_params default to the base hex
		class and hex params of the map.

		Parameters:
		tile: The hex to add neighbors to. (Hex)
		angles: The angles to add the neighbors in. (tuple of int)
		hex_class: The class for the new hexes. (type)
		hex_params: The keyword parameters of the new hexes. (dict)
		"""
		hex_class = self._base_hex if hex_class is None else hex_class
		hex_params = self._base_params if hex_params is None else hex_params
		new_hexes = []
		for angle in angles:
			if tile.neighbors[angle] is None:
				new_hex = hex_class(**hex_params)
				tile.new_neighbor(angle, new_hex)
				new_hexes.append(new_hex)
		tile.join_neighbors()
		self.hexes.extend(new_hexes)
		return new_hexes

	def grow_map(self, angles, hex_class = None, hex_params = None):
		"""
		Grow neighbors for each hex in the in specified directions. (list of Hex)

		If not give (or None) the hex_class and hex_params default to the base hex
		class and hex params of the map.

		Parameters:
		angles: The angles to add the neighbors in. (tuple of int)
		hex_class: The class for the new hexes. (type)
		hex_params: The keyword parameters of the new hexes. (dict)
		"""
		hex_class = self._base_hex if hex_class is None else hex_class
		hex_params = self._base_params if hex_params is None else hex_params
		new_hexes = []
		# Loop through a copy b/c grow_hex will change self.hexes.
		for tile in self.hexes[:]:
			new_hexes.extend(self.grow_hex(tile, angles, hex_class, hex_params))
		return new_hexes

	def start_hex(self, hex_class = None, hex_params = None):
		"""
		Create a hex on the map. (Hex)

		The hex_class and hex_params arguments change the base hex and base params
		used for hexes created by other methods.

		Parameters
		hex_class: The class for the new hexes. (type)
		hex_params: The keyword parameters of the new hexes. (dict)
		"""
		if hex_class is not None:
			self._base_hex = hex_class
		if hex_params is not None:
			self._base_params = hex_params
		tile = self._base_hex(**self._base_params)
		self.hexes.append(tile)
		return tile

	def surround_hex(self, tile, hex_class = None, hex_params = None):
		"""
		Surround a hex with new hexes. (None)

		Already existing hexes are *NOT* over written.

		Parameters:
		tile: The hex to add neighbors to. (Hex)
		angles: The angles to add the neighbors in. (tuple of int)
		hex_class: The class for the new hexes. (type)
		hex_params: The keyword parameters of the new hexes. (dict)
		"""
		hex_class = self._base_hex if hex_class is None else hex_class
		hex_params = self._base_params if hex_params is None else hex_params
		return self.grow_hex(tile, hex_class.angles, hex_class, hex_params)

	def surround_map(self, hex_class = None, hex_params = None):
		"""
		Surround the map with a border of new hexes. (None)

		Parameters:
		angles: The angles to add the neighbors in. (tuple of int)
		hex_class: The class for the new hexes. (type)
		hex_params: The keyword parameters of the new hexes. (dict)
		"""
		hex_class = self._base_hex if hex_class is None else hex_class
		hex_params = self._base_params if hex_params is None else hex_params
		return self.grow_map(hex_class.angles, hex_class, hex_params)

class CatanMap(HexMap):
	"""
	A Settlers of Catan board. (HexMap)

	Attributes:
	use_frame: A flag for using the frame spacing of ports. (bool)

	Class Attributes:
	begin_num: The production numbers for the beginner's layout. (list of num)
	begin_terr: The terrain for the beginner's layout. (list of str)
	begin_port: The ports for the beginner's layout. (list of str)
	standard_num: The production numbers for standard variant layout. (list of num)

	Methods:
	analysis: Display an analysis of the board's layout. (None)
	arrange_columns: Arrange the terrain hexes into columns. (None)
	arrange_intersections: Get all of the intersections of terrain hexes. (None)
	arrange_spiral: Arrange the hexes in a spiral from the bottom. (None)
	calc_terr_pips: Calculate production across different terrain. (dict)
	calc_terr_spread: Calculate the spread of each terrain type. (dict)
	layout: Lay out the board for a game of Settlers. (None)
	set_numbers: Set the numbers on the board. (None)
	set_ports: Set the ports around the board. (None)
	set_terrain: Set the terrain tiles making up the board. (None)

	Overwritten Methods:
	__init__
	arrange
	build
	"""

	begin_num = [5, 6, 11, 5, 8, 10, 9, 2, 10, 12, 9, 8, 3, 4, 3, 4, 6, 11, '']
	begin_terr = ['FRST', 'PSTR', 'DSRT', 'MNTN', 'HILLS', 'HILLS', 'FRST', 'FIELD', 'FIELD',
		'PSTR', 'HILLS', 'FRST', 'FRST', 'MNTN', 'PSTR', 'PSTR', 'MNTN', 'FIELD', 'FIELD']
	begin_port = ['ROCK', 'ANY', 'SHEEP', 'ANY', 'ANY', 'BRICK', 'WOOD', 'ANY', 
		'GRAIN']
	standard_num = [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11]

	def __init__(self, use_frame = False):
		"""
		Build the hexes for the map. (None)

		Parameters:
		use_frame: A flag for using the frame spacing of ports. (bool)
		"""
		self.use_frame = use_frame
		super().__init__()

	def analysis(self):
		"""Display an analysis of the board's layout. (None)"""
		# Display how hard it was to get the layout.
		if self.tries == 1:
			print('It took one try to generate this layout.')
		elif self.tries > 1:
			print(f'It took {self.tries} tries to generate this layout.')
		# Display pips per terrain, including per tile numbers.
		print()
		terr_pips = self.calc_terr_pips()
		per_tile_scores = []
		for terr, (n, pips) in terr_pips.items():
			if terr != 'DSRT':
				per_tile = pips / n
				per_tile_scores.append(per_tile)
				print(f'{terr}: {pips} / 36 ({per_tile:.1f} / tile)')
		mean, dev = mean_dev(per_tile_scores)
		print(f'The standard deviation for per tile production is {dev:.1f}')
		# Display the average distance between pairs of tiles.
		print()
		terr_spread = self.calc_terr_spread()
		for terr, area in terr_spread.items():
			if terr != 'DSRT':
				print(f'{terr} has an average distance of {area:.1f}.')
		mean, dev = mean_dev(tuple(terr_spread.values()))
		print(f'The standard deviation for terrain average distances is {dev:.1f}')
		print()
		# Display the pip counts for three terrain intersections.
		tri_pips = self.get_n_pips(3)
		print(f'There are {len(tri_pips)} triple production intersections.')
		mean, std_dev = mean_dev(tri_pips)
		print(f'Three tile pips have a mean of {mean:.1f} and a deviation of {std_dev:.1f}')

	def arrange(self):
		"""Group the hexes as needed for later processing. (None)"""
		self.arrange_columns()
		self.arrange_spiral()
		self.arrange_intersections()

	def arrange_columns(self):
		"""Arrange the terrain hexes into columns. (None)"""
		# Find the top-most hex.
		top = self.hexes[0]
		while True:
			for angle in (0, 60, 300):
				higher = top.neighbors[angle]
				if higher is not None and not higher.port:
					top = higher
					break
			else:
				break
		# Find the top hexes to the left and the right.
		left = [top.neighbors[240]]
		right = [top.neighbors[120]]
		toppers = [top] + right + left
		# Keep looking for top hexes to the left and the right.
		while True:
			count = 0
			# Check the right side.
			if right[-1].neighbors[120] is not None:
				right.append(right[-1].neighbors[120])
				toppers.append(right[-1])
				count += 1
			# Check the left side.
			if left[-1].neighbors[240] is not None:
				left.append(left[-1].neighbors[240])
				toppers.append(left[-1])
				count += 1
			# Stop checking if nothing was found on either side.
			if count == 0:
				break
		# Set the columns by going down from each of the top hexes.
		self.columns = []
		for topper in toppers:
			self.columns.append(topper)
			while True:
				lower = self.columns[-1].neighbors[180]
				if lower is None or lower.port:
					break
				self.columns.append(lower)

	def arrange_intersections(self):
		"""Get all of the intersections of terrain hexes. (None)"""
		self.intersections = set()
		for tile in self.terrain:
			for turn in range(0, 360, 60):
				inter = [tile]
				possible = tile.neighbors[turn]
				if possible is not None and not possible.port:
					inter.append(possible)
				possible = tile.neighbors[(60 + turn) % 360]
				if possible is not None and not possible.port:
					inter.append(possible)
				inter.sort(key = lambda tile: tile.id)
				self.intersections.add(tuple(inter))

	def arrange_spiral(self):
		"""Arrange the hexes in a spiral from the bottom. (None)"""
		# Find the bottom-most hex.
		bottom = self.hexes[0]
		while True:
			for angle in (180, 120, 240):
				lower = bottom.neighbors[angle]
				if lower is not None and not lower.port:
					bottom = lower
					break
			else:
				break
		#print(repr(bottom))
		# Spiral counter clockwise into the center.
		self.spiral = [bottom]
		angle = 60
		# Make sure the spiral gets all of the terrain.
		while len(self.spiral) < len(self.terrain):
			start_angle = angle
			while True:
				target = self.spiral[-1].neighbors[angle]
				# Turn the spiral when you run out of valid hexes.
				if target is None or target in self.spiral or target.port:
					angle = (angle - 60) % 360
					# Check for deadends before finishing.
					if angle == start_angle:
						msg = 'Caught in spiral at {!r} after {} tiles.'
						raise ValueError(msg.format(self.spiral[-1], len(self.spiral)))
				else:
					break
			self.spiral.append(self.spiral[-1].neighbors[angle])

	def build(self):
		"""Build the map by adding hexes to it. (None)"""
		# Start with a center hex.
		start = self.start_hex(CatanHex)
		# Add hexes all around the center.
		mid_loop = self.surround_hex(start)
		# Add hexes all around those hexes.
		edge_hexes = self.surround_map()
		# 1. fill another hex out with ports
		self.terrain = self.hexes[:]
		self.ports = self.surround_map(hex_params = {'port': True})
		# Clean up the ports to make them clockwise from 12 o'clock.
		self.ports.sort(key = lambda tile: math.atan2(tile.x, tile.y), reverse = True)
		#print(self.ports)
		# Eliminate every other port.
		self.ports = self.ports[1::2]
		self.hexes = self.terrain + self.ports

	def calc_terr_pips(self):
		"""
		Calculate production across different terrain. (dict of str: tuple)

		The return value is a dictionary with terrain types for keys, and a list of
		the pips of production and the number of tiles for that terrain.
		"""
		terr_pips = {terr: [0, 0] for terr in set(self.begin_terr)}
		for tile in self.terrain:
			terr_pips[tile.terr][0] += 1
			terr_pips[tile.terr][1] += tile.pips
		return terr_pips

	def calc_terr_spread(self):
		"""
		Calculate the spread of each terrain type. (dict of str: float)

		The spread if each terrain is defined as the average distance in hexes 
		between pairs of that terrain type.
		"""
		# Get the tiles for each terrain
		terr_tiles = {terr: [] for terr in set(self.begin_terr)}
		for tile in self.terrain:
			terr_tiles[tile.terr].append(tile)
		# Calculate all the paired distances for each terrain type.
		terr_spread = {}
		for terr, tiles in terr_tiles.items():
			terr_spread[terr] = 0
			n = 0
			for start, end in itertools.combinations(tiles, 2):
				n += 1
				dist = ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5
				terr_spread[terr] += int(dist)
			# Don't count terrain types with only one tile.
			if n:
				terr_spread[terr] /= n
			else:
				del terr_spread[terr]
		return terr_spread

	def get_n_pips(self, n = 3):
		"""
		Get all pip counts for intersections with n producing tiles. (list of int)

		Parameters:
		n: How many producing tiles each intersection must have. (int)
		"""
		inters = [inter for inter in self.intersections if len(inter) == n]
		pips = [tuple(tile.pips for tile in inter) for inter in inters]
		pips = [sum(sub_pips) for sub_pips in pips if -1 not in sub_pips]
		return pips

	def layout(self, num = 'standard', port = 'shuffle', terr = 'shuffle', validate = ()):
		"""
		Lay out the board for a game of Settlers. (None)

		The num parameter can be 'beginner' for the numbers in the beginner's layout,
		'standard' for the variable set up alphabetical order, or 'shuffle' to 
		randomize the numbers from the standard layout.

		The port parameter can be 'beginner' for the ports in the beginner's layout or
		'shuffle' to mix up those ports. For some maps, the use_frame attribute may
		change where the ports go, but not their order.

		The terr parameter can be 'beginner' for the terrain in the beginner's layout
		or 'shuffle' to mix up the terrain tiles as in the variable set up.

		Functions in the validate parameter should take a CatanMap as a parameter, and
		should return True if the map is a valid map by the criteria the function
		represents.

		Parameters:
		num: How to order the numbers on the board. (str)
		port: How to order the ports around the board. (str)
		terr: How to order the terrain tiles on the board. (str)
		validate: Any functions to validate the layout. (tuple of callable)
		"""
		# Only count tries if there are validation functions.
		if validate:
			self.tries = 1
		else:
			self.tries = 0
		while True:
			# Layout the board.
			self.set_terrain(terr)
			self.set_numbers(num)
			self.set_ports(port)
			# Check the validators
			for validator in validate:
				if not validator(self):
					break
			else:
				break
			self.tries += 1

	def set_numbers(self, order = 'standard'):
		"""
		Set the numbers on the board. (None)

		The order parameter can be 'beginner' for the numbers in the beginner's 
		layout, 'standard' for the variable set up alphabetical order, or 'shuffle' to
		randomize the numbers from the standard layout.

		Parameters:
		order: How to order the numbers on the board. (str)
		"""
		# Get the order of the numbers.
		if order == 'beginner':
			numbers = self.begin_num[:]
		else:
			numbers = self.standard_num[:]
		if order == 'shuffle':
			random.shuffle(numbers)
		# Lay the numbers out in the spiral, skipping deserts.
		numbers = iter(numbers)
		tiles = iter(self.spiral)
		while True:
			try:
				tile = next(tiles)
				if tile.terr != 'DSRT':
					tile.num = next(numbers)
				else:
					tile.num = 0
			except StopIteration:
				break

	def set_ports(self, order = 'shuffle'):
		"""
		Set the ports around the board. (None)

		The order parameter can be 'beginner' for the ports in the beginner's layout
		or 'shuffle' to mix up those ports. For some maps, the use_frame attribute may
		change where the ports go, but not their order.

		Parameters:
		port: How to order the ports around the board. (str)
		"""
		ports = self.begin_port[:]
		if order == 'shuffle':
			random.shuffle(ports)
		for tile, port in zip(self.ports, ports):
			tile.terr = port

	def set_terrain(self, order = 'shuffle'):
		"""
		Set the terrain tiles making up the board. (None)

		The order parameter can be 'beginner' for the terrain in the beginner's layout
		or 'shuffle' to mix up the terrain tiles as in the variable set up.

		Parameters:
		order: How to order the terrain tiles on the board. (str)
		"""
		rezes = self.begin_terr[:]
		if order == 'shuffle':
			random.shuffle(rezes)
		for tile, terr in zip(self.columns, rezes):
			tile.terr = terr

class Catan56Map(CatanMap):
	"""
	A 5/6 player Settlers of Catan board. (CatanMap)

	Class Attribute:
	frame_ports: The spacing between ports on the 5th edition frame. (list of int)

	Overridden Methods:
	board
	"""

	begin_num = [2, 5, 4, 6, 3, 9, 8, 11, 11, 10, 6, 3, 8, 4, 8, 10, 11, 12, 10, 5, 4,
		9, 5, 9, 12, 3, 2, 6]
	begin_port = ['ANY', 'ANY', 'BRICK', 'SHEEP', 'WOOD', 'ANY', 'GRAIN', 'ANY', 'ROCK',
		'ANY', 'SHEEP']
	begin_terr = ['FIELD', 'HILLS', 'FIELD', 'MNTN', 'MNTN', 'HILLS', 'PSTR', 'FRST',
		'HILLS', 'FIELD', 'PSTR', 'MNTN', 'PSTR', 'MNTN', 'FRST', 'FRST', 'PSTR',
		'FIELD', 'HILLS', 'DSRT', 'PSTR', 'FIELD', 'FRST', 'HILLS', 'DSRT', 'FIELD',
		'FRST', 'PSTR', 'MNTN', 'FRST']
	frame_ports = [1, 4, 6, 7, 9, 11, 13, 14, 16, 19, 21]
	standard_num = [2, 5, 4, 6, 3, 9, 8, 11, 11, 10, 6, 3, 8, 4, 8, 10, 11, 12, 10, 5, 4,
		9, 5, 9, 12, 3, 2, 6]

	def build(self):
		"""Build the map by adding hexes to it. (None)"""
		# Start with four center hexes.
		start = self.start_hex(CatanHex)
		self.grow_map((120,))
		self.grow_map((180,))
		# Add hexes all around the center.
		mid_loop = self.surround_map()
		# Add hexes all around those hexes.
		edge_hexes = self.surround_map()
		top = start.neighbors[0].neighbors[0]
		# Fill another hex out with ports
		self.terrain = self.hexes[:]
		self.ports = self.surround_map(hex_params = {'port': True})
		# Clean up the ports to make them clockwise from 12 o'clock.
		self.ports.sort(key = lambda tile: math.atan2(tile.x, tile.y), reverse = True)
		#print(self.ports)
		# Space out the ports.
		if self.use_frame:
			self.ports = [self.ports[index] for index in self.frame_ports]
		else:
			self.ports = self.ports[1::2]
		self.hexes = self.terrain + self.ports

def good_rock(n = 4):
	"""
	Make a validator for at least one ore with at least n pips. (callable)

	Parameters:
	n: The number of pips at least one mountin must have. (int)
	"""
	def gr_criteria(catan):
		max_pip = 0
		for tile in catan.terrain:
			if tile.terr == 'ROCK':
				max_pip = max(max_pip, tile.pips)
		return max_pip >= n

def max_pip(n = 11):
	"""
	Make a validator for no intersection with more than n pips. (callable)

	Parameters:
	n: The maximum number of pips for any intersection. (int)
	"""
	def mp_criteria(catan):
		for settle in catan.intersections:
			if sum(tile.pips for tile in settle) > n:
				return False
		return True
	return mp_criteria

def max_port_pips(n = 3):
	"""
	Make a validator for no port with > n of it's own pips. (callable)

	Parameters:
	n: The maximum pips of self production for a port. (int)
	"""
	def mpp_criteria(catan):
		for port in catan.ports:
			# Skip 3 to 1 ports.
			if port.terr == 'ANY':
				continue
			# Count pips of neighbors with the port's resources.
			pips = 0
			for angle in range(0, 360, 60):
				tile = port.neighbors[angle]
				if tile is not None and tile.terr == PORT_TO_TERR[port.terr]:
					pips += tile.num
			# Check for the maximum.
			if pips > n:
				return False
		return True
	return mpp_criteria

def mean_dev(nums, sample = False):
	"""
	Calculate the mean and standard deviation of a sequence. (tuple)

	Parameters:
	nums: The sequence to calculate for. (list of int)
	sample: A flag for nums being a sample, not a population. (bool)
	"""
	mean = sum(nums) / len(nums)
	var = sum((mean - num) ** 2 for num in nums) / (len(nums) - sample)
	return mean, var ** 0.5

def no_2_12():
	"""Make a validator for 2 and 12 not being neighbors. (callable)"""
	def n2B_criteria(catan):
		for tile in catan.hexes:
			for angle in range(0, 360, 60):
				adj = tile.neighbors[angle]
				if adj is not None:
					if (tile.num, adj.num) in ((2, 2), (2, 12), (12, 2), (12, 12)):
						return False
		return True
	return n68_criteria

def no_6_8():
	"""Make a validator for 6 and 8 not being neighbors. (callable)"""
	def n68_criteria(catan):
		for tile in catan.hexes:
			for angle in range(0, 360, 60):
				adj = tile.neighbors[angle]
				if adj is not None:
					if (tile.num, adj.num) in ((6, 6), (6, 8), (8, 6), (8, 8)):
						return False
		return True
	return n68_criteria

def no_double_6_8():
	"""Make a validator for no terrain with two five pip tiles. (callable)"""
	def nd68_criteria(catan):
		terr = set()
		for tile in catan.terrain:
			if tile.pips == 5:
				if tile.terr in terr:
					return False
				terr.add(tile.terr)
		return True

def no_num_pairs():
	"""Make a validator for no number neighboring itself. (callable)"""
	def nmp_criteria(catan):
		for tile in catan.terrain:
			for angle in range(0, 360, 60):
				adj = tile.neighbors[angle]
				if adj is not None:
					if tile.num == adj.num:
						return False
		return True
	return nmp_criteria

def no_terr_pairs():
	"""Make a validator for no terrain neighboring itself. (callable)"""
	def nrp_criteria(catan):
		for tile in catan.hexes:
			for angle in range(0, 360, 60):
				adj = tile.neighbors[angle]
				if adj is not None:
					if tile.terr == adj.terr:
						return False
		return True
	return nrp_criteria

def no_terr_tri():
	"""Make a validator of no triangles of the same terrain. (callable)"""
	def nrt_criteria():
		for inter in catan.intersections:
			if len(inter) == 3:
				inter = tuple(inter)
				first_match = inter[0].terr == inter[1].terr
				if first_match and inter[1].terr == inter[2].terr:
					return False
		return True
	return nrt_criteria

def percentiles(seq):
	"""
	Calculate and display percentiles for a sequence. (list)

	Parameters:
	seq: The numbers to get percentiles for. (list)
	"""
	seq = sorted(seq)
	count = len(seq)
	quantiles = [seq[0]]
	print(f'min: {quantiles[-1]}')
	for percent in range(1, 11):
		quantiles.append(seq[int(count / 10 * percent)])
		print(f'{percent}0th percentile: {quantiles[-1]}')
	quantiles.append(seq[-1])
	print(f'max: {seq[-1]}')
	return quantiles

def regions(ignore = ('DSRT',)):
	"""
	Make a validator requiring pairs of terrain types. (callable)

	Parameters:
	ignore: The terrains not required to pair. (tuple of str)
	"""
	def reg_criteria(catan):
		for tile in catan.hexes:
			# Skip ignored terrain.
			if tile.terr in ignore:
				continue
			# Check all the neighbors.
			tile_check = False
			for angle in range(0, 360, 60):
				adj = tile.neighbors[angle]
				if adj is not None:
					if tile.terr == adj.terr:
						tile_check = True
						break
			# Invalidate without a matching neighbor.
			if not tile_check:
				return False
		return True
	return reg_criteria

def sample_data(n, map_class = CatanMap, map_params = {}, 
	layout_params = {'num': 'shuffle'}):
	"""
	Calculate statistics on simulated Catan set ups. (dict)

	The data given includes pips of production per terrain, average terrain 
	distance, and pips of production for three resource intersections. For each
	of these the minimum, maximum, mean, and standard deviation are given for
	each board layout.

	Parameters:
	n: The number of boards to generate. (int)
	map_class: The type of board to generate. (type)
	map_params: The parameters to the board's initialization. (dict)
	layout_params: The parameters to the board's layout method. (dict)
	"""
	data = collections.defaultdict(list)
	for trial in range(n):
		board = map_class(**map_params)
		board.layout(**layout_params)
		terr_pips = board.calc_terr_pips()
		per_tile = {terr: data[1] / data[0] for terr, data in terr_pips.items()}
		data['min_terr_pips'].append(min(per_tile.values()))
		data['max_terr_pips'].append(max(per_tile.values()))
		mean, dev = mean_dev(tuple(per_tile.values()))
		data['terr_pips_mean'].append(mean)
		data['terr_pips_dev'].append(dev)
		terr_dist = board.calc_terr_spread()
		data['min_terr_dist'].append(min(terr_dist.values()))
		data['max_terr_dist'].append(max(terr_dist.values()))
		mean, dev = mean_dev(tuple(terr_dist.values()))
		data['terr_dist_mean'].append(mean)
		data['terr_dist_dev'].append(dev)
		tri_pips = board.get_n_pips(3)
		data['min_tri_pips'].append(min(tri_pips))
		data['max_tri_pips'].append(max(tri_pips))
		mean, std_dev = mean_dev(tri_pips)
		data['tri_pips_mean'].append(mean)
		data['tri_pips_dev'].append(dev)
	return data

if __name__ == '__main__':
	board = CatanMap()
	board.layout()
	print(board)
	board.analysis()
