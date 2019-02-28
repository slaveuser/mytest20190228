# uses tuples rather than lists for use with startswith/endswith function
comment_symbols_dict = {}
comment_symbols_dict['python'] = ('#', '\'\'\'', '"""', '@')
comment_symbols_dict['java'] = ('//', '/*', '*', '*/')
comment_symbols_dict['javascript'] = ('//', '/*', '*', '*/')
comment_symbols_dict['ruby'] = ('#', '=begin', '=end', '#`')
comment_symbols_dict['r'] = ('#')
comment_symbols_dict['tex'] = ('%')
comment_symbols_dict['c'] = ('//', '/*', '*/')
comment_symbols_dict['c++'] = ('//', '/*', '*/')
comment_symbols_dict['c#'] = ('//', '/*', '*/')

file_ext_dict = {}
file_ext_dict['python'] = ('.py', '.pyo')
file_ext_dict['java'] = ('.java')
file_ext_dict['javascript'] = ('.js')
file_ext_dict['ruby'] = ('.rb', '.erb')
file_ext_dict['r'] = ('.r')
file_ext_dict['tex'] = ('.tex')
file_ext_dict['c'] = ('.c', '.cc')
file_ext_dict['c++'] = ('.cpp', '.cxx')
file_ext_dict['c#'] = ('.cs')

class_decorator_dict = {}
class_decorator_dict['python'] = [r'class [a-zA-Z0-9-_]*']
class_decorator_dict['java'] = [r'class [a-zA-Z0-9-_]* [extends|implements] [a-zA-Z0-9-_]* *{*', r'class [a-zA-Z0-9-_]* *{*']
class_decorator_dict['javascript'] = [r'class [a-zA-Z0-9-_]* [extends|implements] [a-zA-Z0-9-_]* *{*', r'class [a-zA-Z0-9-_]* *{*']
class_decorator_dict['ruby'] = []
class_decorator_dict['r'] = []
class_decorator_dict['tex'] = []
class_decorator_dict['c'] = []
class_decorator_dict['c++'] = []
class_decorator_dict['c#'] = []