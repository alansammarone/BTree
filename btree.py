#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
	Implements a node of a order M BTree.
	A node is a list of values, which are themselves tuples of the form (key, value).
	An order M node can have at most M-1 values and M chidren, and must have at least (M-1)/2 values and M/2 children.
'''


class BTreeNode:

	def __init__(self, order, values=None):
		self.order = order

		self.separators = []
		self.values = []

		self.children = []
		self.parent = None

		self.is_root = None

		if values:
			self.set_values(values)


	def search(self, key):

		separator_to_follow = self.separators[-1] # Initialize with last separator,

		for i, (k, v) in enumerate(self.values):
			if key < k:
				separator_to_follow = i           # Because if not found until the end, must be last.
				break
			elif key == k:
				return v
		if self.is_leaf():
			return None # Key not found
		else:
			return self.children[separator_to_follow].search(key)

	def set_values(self, values):
		self.values = values
		if not self.separators or self.separators[-1] != len(values):
			self.separators = range(len(values) + 1)


	def get_successor(self, key):

		for i, (k, v) in enumerate(self.values):
			if key < k:
				if self.is_leaf():
					return (k, v)
				else:
					return self.children[i].get_successor(key)
			elif key == k:
				if self.is_leaf():
					raise Exception("Something wrong - should not need to find sucessor of leaf node.")
				else:
					return self.children[i+1].get_successor(key)

		return self.children[-1].get_successor(key) #must be last


	def set_children(self, children):
		self.children = children
		if children:
			self.separators = range(len(children))
		else:
			self.separators = range(len(self.values) + 1)

	# Inserts value into node ignoring restrictions
	def insert_to_values(self, (key, value), index=None):


		if not self.values:
			self.set_values([(key, value)])
		else:
			if not index:
				index = self.separators[-1] # Initialize with last separator,
				for i, (k, v) in enumerate(self.values):
					if key < k:
						index = i           # Because if not found until the end, must be last.
						break

			self.values.insert(index, (key, value))
			self.separators = range(len(self.values)+1) # Just add one new separator


	# Puts (k2, v2) in the place of (k1, v1)
	def substitute_value(self, (k1, v1), (k2, v2)):

		for i, (k, v) in enumerate(self.values):

			if k == k1:
				self.values[i] = (k2, v2)
				return
			elif k > k1:
				self.children[i].substitute_value((k1, v1), (k2, v2))
				return


		return self.children[-1].substitute_value((k1, v1), (k2, v2))

	# Walks all the way down to leafs, restructuring over-filled nodes along the way, and then inserts.
	def insert(self, (key, value)):

		if not self.values:
			self.insert_to_values((key, value))
		else:
			assert self.separators[-1] == len(self.values), "%s %s" %( self.values , self.separators)
			if self.is_overflowing():
				if self.is_root:
					self.create_new_root()
				self.split()
				self.parent.insert((key, value))
			else:
				separator_to_insert = self.separators[-1] # Initialize with last separator,
				for i, (k, v) in enumerate(self.values):
					if key < k:
						separator_to_insert = i           # Because if not found until the end, must be last.
						break
				if self.is_leaf():
					self.insert_to_values((key, value), separator_to_insert)
				else:
					return self.children[separator_to_insert].insert((key, value))



	# Removes keys ignoring rebalancing rules - assumes it was already done
	def remove_from_values(self, key):

		for i, (k, v) in enumerate(self.values):

			if k == key:
				self.values.pop(i)
				self.separators.pop()
				return
			elif k > key:

				self.children[i].remove_from_values(key)
				return
		return self.children[-1].remove_from_values(key)

	def split(self):

		# Moves median up
		self.parent.insert_to_values(self.values[len(self.values)/2])
		key_gone_up = self.values[len(self.values)/2][0]
		del self.values[len(self.values)/2]
		self.separators.pop()

		new_right_child = BTreeNode(self.order)
		new_right_child.parent = self.parent
		new_right_child.set_values(self.values[len(self.values)/2:])
		new_right_child.set_children(self.children[len(self.children)/2:])
		for c in new_right_child.children:
			c.parent = new_right_child

		self.set_values(self.values[:len(self.values)/2])	#Current node becomes new left node
		self.set_children(self.children[:len(self.children)/2])

		if self.parent.children:
			index_of_new_child = self.parent.separators[-1]
			for i, c in enumerate(self.parent.children):
				if c == self:
					index_of_new_child = i + 1
					break

			self.parent.children.insert(index_of_new_child, new_right_child)
			self.parent.separators = range(len(self.parent.values) + 1)

		else:
			self.parent.set_children([self, new_right_child])

	#Splits current root into two subtrees, and set them to be children of a new root
	def create_new_root(self):

		self.is_root = False
		self.parent = BTreeNode(self.order)
		self.parent.is_root = True

	def remove(self, key):

		if (not self.is_root) and self.is_underflowing(): # First get balacing right, later remove desired key
			if not self.stole_key_from_sibling():
				self.fuse_with_sibling()
			if self.parent:
				self.parent.remove(key)
			else:
				self.remove(key)
			return
		else:

			for i, (k, v) in enumerate(self.values):
				if k == key:
					if self.is_leaf():
						self.remove_from_values(key)
						return
					else:
						successor = self.get_successor(key)
						self.remove(successor[0])
						self.substitute_value((k, v), successor)
						return
				elif k > key:
					return self.children[i].remove(key)


			return self.children[-1].remove(key) # Must be last


	def fuse_with_sibling(self):

		left_sibling, right_sibling = self.get_siblings()

		if right_sibling: #Fuse self with right sibling, pulling down one parent key
			for i, c in enumerate(self.parent.children):
				if c == self:
					index_to_pull_down, key_to_pull_down = i+1, self.parent.values.pop(i)
					break

			self.values.append(key_to_pull_down)

			for v in right_sibling.values:
				self.values.append(v)

			for c in right_sibling.children:
				c.parent = self
				self.children.append(c)

			self.parent.children.pop(index_to_pull_down)
			self.parent.separators.pop()

			self.separators = range(len(self.values) + 1)


		elif left_sibling: #Fuse left sibling with self, pulling down one parent key
			for i, c in enumerate(self.parent.children):
				if c == self:
					index_to_pull_down, key_to_pull_down = i-1, self.parent.values.pop(i-1)
					break

			self.values.insert(0, key_to_pull_down)

			for v in list(reversed(left_sibling.values)):
				self.values.insert(0, v)

			for c in list(reversed(left_sibling.children)):
				c.parent = self
				self.children.insert(0, c)

			self.parent.children.pop(index_to_pull_down)
			self.parent.separators.pop()

			self.separators = range(len(self.values) + 1)


		if self.parent.is_root and len(self.parent.values)==0: # Tree decreases its height
			self.is_root = True
			self.parent.is_root = False
			self.parent = None


	# Returns true if its posible to steal a key from either a left or a right sibling. Otherwise, returns false.
	def stole_key_from_sibling(self):

		left_sibling, right_sibling = self.get_siblings()



		if left_sibling and not left_sibling.is_underflowing():

			#right rotation
			left_sibling_last_key, left_sibling_last_child = left_sibling.values.pop(), left_sibling.children.pop() if left_sibling.children else None
			left_sibling.separators.pop()

			for i, c in enumerate(self.parent.children):
				if id(c) == id(self):
					parent_index_to_go_down = i - 1
					break
			new_value = self.parent.values.pop(parent_index_to_go_down)


			self.values.insert(0, new_value)
			self.parent.values.insert(parent_index_to_go_down, left_sibling_last_key)


			self.separators = range(len(self.values) + 1)


			if left_sibling_last_child:
				left_sibling_last_child.parent = self
				self.children.insert(0, left_sibling_last_child)

			return True

		elif right_sibling and not right_sibling.is_underflowing():

			# left rotation
			right_sibling_first_key, right_sibling_first_child = right_sibling.values.pop(0), right_sibling.children.pop(0) if right_sibling.children else None
			right_sibling.separators.pop()

			for i, c in enumerate(self.parent.children):
				if id(c) == id(self):
					parent_index_to_go_down = i
					break

			new_value = self.parent.values.pop(parent_index_to_go_down)
			self.values.append(new_value)
			self.parent.values.insert(parent_index_to_go_down, right_sibling_first_key)
			self.separators = range(len(self.values) + 1)

			if right_sibling_first_child:
				right_sibling_first_child.parent = self
				self.children.append(right_sibling_first_child)

			return True

		return False

	def get_siblings(self):

		for i, c in enumerate(self.parent.children):
			if c == self:
				if i == 0:
					return None, self.parent.children[i+1]
				elif i == len(self.parent.children) - 1:
					return self.parent.children[i-1], None
				else:
					return self.parent.children[i-1], self.parent.children[i+1]

		return None, None

	def is_underflowing(self):
		return len(self.separators) == self.order/2

	def is_overflowing(self):
		return len(self.separators) == self.order


	def is_leaf(self):
		return not bool(self.children)



'''
	Implements an order M BTree.
	Each node will have between (M-1)/2 and M-1 values (included). Each value is a tuple (key, entry).
	All leafs are at the same depth. Search, insertion and deletion can be done in logarithmic time.
'''

class BTree:

	def __init__(self, order):
		self.order = order
		self.root = None

	def search(self, key):
		return self.root.search(key)

	def insert(self, (key, value)):

		if not self.root:
			self.root = BTreeNode(self.order)
			self.root.is_root = True

		self.root.insert((key, value)) # Try to insert at the root, then go all the way down adjusting over-filled nodes

		if not self.root.is_root:
			self.root = self.root.parent

	def remove(self, key):

		if not self.root:
			return False

		self.root.remove(key)

		if not self.root.is_root:
			self.root = self.root.children[0]



''' 
	Everything below here is not needed, it is used only for testing purposes.
'''

import matplotlib.pyplot as pp
import time
from random import shuffle	

orders_to_test = range(0, 1024, 16)
number_of_operations = 10**2

search_avg_times = []
insertion_avg_times = []
deletion_avg_times = []

for order in orders_to_test:

	BT = BTree(order)

	values_to_test = range(number_of_operations)
	shuffle(values_to_test)

	start_time = time.clock()
	for i in values_to_test:
		BT.insert((i, {"testdata":i}))
	end_time = time.clock()

	average_time = float(end_time - start_time)/number_of_operations
	insertion_avg_times.append(average_time*10**6)
	
	shuffle(values_to_test)

	start_time = time.clock()
	for i in values_to_test:
		BT.search(i)

	end_time = time.clock()

	average_time = (end_time - start_time)/number_of_operations

	search_avg_times.append(average_time*10**6)

	shuffle(values_to_test)

	start_time = time.clock()
	for i in values_to_test:
		BT.remove(i)

	end_time = time.clock()

	average_time = (end_time - start_time)/number_of_operations

	deletion_avg_times.append(average_time*10**6)


pp.subplot(1, 3, 1)
pp.title("Insertion time")
pp.xlabel("BTree Order")
pp.ylabel(u"Average time (µs)")

pp.scatter(orders_to_test, insertion_avg_times)
pp.subplot(1, 3, 2)
pp.title("Search time")
pp.xlabel("BTree Order")
pp.ylabel(u"Average time (µs)")

pp.scatter(orders_to_test, search_avg_times)
pp.subplot(1, 3, 3)
pp.title("Deletion time")
pp.xlabel("BTree Order")
pp.ylabel(u"Average time (µs)")
pp.scatter(orders_to_test, deletion_avg_times)
pp.show()







