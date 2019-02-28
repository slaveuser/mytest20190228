import sys
import ast
import os

def python_files(path):
	for dirpath, dirname, filenames in os.walk(path):
		for f in filenames:
			fullpath = os.path.join(dirpath, f)
			if fullpath.endswith(".py"):
				yield fullpath

				
from ast import NodeVisitor

class UsageAnalyzer(NodeVisitor):
	def __init__(self, *args, **kwargs):
		self.called_function_names = set()
		self.defined_function_names = set()

		return super(UsageAnalyzer, self).__init__(*args, **kwargs)

	def visit_Call(self, node, *args, **kwargs):
		def get_name(node):
			# function calls
			if hasattr(node.func, 'id'):
				return node.func.id, node.func.ctx

			# method calls
			if hasattr(node.func, 'value'):
				return node.func.attr, node.func.ctx

			if hasattr(node.func, 'func'):
				return get_name(node.func)

		name, ctx = get_name(node)
		self.called_function_names.add(name)

		self.generic_visit(node, *args, **kwargs)

	def visit_ImportFrom(self, node, *args, **kwargs):
		self.generic_visit(node, *args, **kwargs)

	def visit_FunctionDef(self, node, *args, **kwargs):
		self.defined_function_names.add(node.name)

		self.generic_visit(node, *args, **kwargs)

	def find_unused(self):
		return self.defined_function_names - self.called_function_names

def main(paths):
	usage_analyzer = UsageAnalyzer()
	for path in paths:
		for f in python_files(path):
			tree = ast.parse(open(f).read(), f)
			usage_analyzer.visit(tree)
			# print ast.dump(tree)
			# break

	print '\n----- NUM FUNCTIONS -----\n'
	print len(usage_analyzer.defined_function_names)

	print '\n----- NUM USED FUNCTIONS -----\n'
	print len(usage_analyzer.called_function_names)

	print '\n----- UNUSED FUNCTIONS -----\n'
	# for unused_fn in usage_analyzer.find_unused():
		# print unused_fn
	print len(usage_analyzer.find_unused())

	for unused_fn in usage_analyzer.called_function_names:
		print unused_fn
if __name__ == '__main__':
	main([os.getcwd()])