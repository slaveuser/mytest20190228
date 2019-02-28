import sys, os, re
from data_dict import comment_symbols_dict, file_ext_dict, class_decorator_dict

def count_files(directory):
	file_count = 0

	for (dirpath, dirnames, filenames) in os.walk(directory):
		filenames = [fname for fname in filenames if '.git' not in fname] # remove any git files e.g. '.gitignore'
		if '.git' not in dirpath:
			file_count += len(filenames)

	return str(file_count)

# https://github.com/rrwick/LinesOfCodeCounter
def countLinesOfCode(language, directory):
	code_size_data = {}

	try:
		commentSymbols = comment_symbols_dict[language.lower()]
		file_extensions = file_ext_dict[language.lower()]
	except KeyError:
		return
		
	# functionOperators = (r'function.*\(', '=>')

	filesToCheck = []
	for root, _, files in os.walk(directory):
		for f in files:
			fullpath = os.path.join(root, f)
			if '.git' not in fullpath:
				for extension in file_extensions:
					if fullpath.endswith(extension):
						filesToCheck.append(fullpath)

	if not filesToCheck:
		return code_size_data

	lineCount = 0
	totalBlankLineCount = 0
	totalCommentLineCount = 0
	totalFunctionCount = 0

	for fileToCheck in filesToCheck:
		with open(fileToCheck) as f:

			fileLineCount = 0
			fileBlankLineCount = 0
			fileCommentLineCount = 0
			fileFunctionCount = 0

			for line in f:

				lineCount += 1
				fileLineCount += 1

				# if any(re.compile(substring).search("".join(line.split())) for substring in functionOperators):
				# 	fileFunctionCount += 1

				lineWithoutWhitespace = line.strip()
				if not lineWithoutWhitespace:
					totalBlankLineCount += 1
					fileBlankLineCount += 1
				elif lineWithoutWhitespace.startswith(commentSymbols):
					totalCommentLineCount += 1
					fileCommentLineCount += 1
			
			filename = os.path.basename(fileToCheck)
			# totalFunctionCount += fileFunctionCount
			
			# data[filename] = {'lines': fileLineCount, 'comment_lines': fileCommentLineCount, 'code_lines':fileLineCount - fileBlankLineCount - fileCommentLineCount}

	# data['totals'] = {'lines': lineCount, 'comment_lines': totalCommentLineCount, 'code_lines':lineCount - totalBlankLineCount - totalCommentLineCount}

	code_size_data = {'files': len(filesToCheck), 'lines': lineCount/len(filesToCheck), 'comment_lines':totalCommentLineCount/len(filesToCheck), \
	'code_lines':(lineCount - totalBlankLineCount - totalCommentLineCount)/len(filesToCheck)}
	return code_size_data

def countFunctions(language, directory):

	functions_data = {}

	try:
		file_extensions = file_ext_dict[language.lower()]
	except KeyError:
		return
	functionOperators=()

	if language.lower() == 'java':
		file_extensions = ['.java']
		functionOperators = (r'\b(?:public|private|protected|default)\b (static )?[a-zA-Z0-9-_<>\(\)]* *[a-zA-Z0-9-_]* *\([a-zA-Z0-9-_,=<> ]*\)')
	elif language.lower() == 'javascript':
		file_extensions = ['.js']
		functionOperators = (r'function.*\(', '=>')

	filesToCheck = []
	for root, _, files in os.walk(directory):
		for f in files:
			fullpath = os.path.join(root, f)
			if '.git' not in fullpath:
				for extension in file_extensions:
					if fullpath.endswith(extension):
						filesToCheck.append(fullpath)

	if not filesToCheck:
		return functions_data

	totalFunctionCount = 0
	singleFileMax = [0,'']

	for fileToCheck in filesToCheck:
		with open(fileToCheck) as f:

			fileFunctionCount = 0

			for line in f:

				if language.lower() == 'java':
					if re.compile(functionOperators).search(line):
						fileFunctionCount += 1
				elif language.lower() == 'javascript':
					if any(re.compile(substring).search("".join(line.split())) for substring in functionOperators):
						fileFunctionCount += 1

			filename = os.path.basename(fileToCheck)
			totalFunctionCount += fileFunctionCount

			if fileFunctionCount > singleFileMax[0]:
				singleFileMax[0] = fileFunctionCount
				singleFileMax[1] = filename

	functions_data = {'total_functions': totalFunctionCount, 'avg_per_file': totalFunctionCount/len(filesToCheck), 'single_file_max':singleFileMax }
	return functions_data

def countClasses(language, directory):

	classes_data = {}

	try:
		file_extensions = file_ext_dict[language.lower()]
		classDeclarators = class_decorator_dict[language.lower()]
	except KeyError:
		return


	filesToCheck = []
	for root, _, files in os.walk(directory):
		for f in files:
			fullpath = os.path.join(root, f)
			if '.git' not in fullpath:
				for extension in file_extensions:
					if fullpath.endswith(extension):
						filesToCheck.append(fullpath)

	if not filesToCheck:
		return classes_data

	totalClassCount = 0
	singleFileMax = [0,'']

	for fileToCheck in filesToCheck:
		with open(fileToCheck) as f:

			fileClassCount = 0

			for line in f:
				if any(re.compile(substring).search(line) for substring in classDeclarators):
					fileClassCount += 1

			filename = os.path.basename(fileToCheck)
			totalClassCount += fileClassCount

			if fileClassCount > singleFileMax[0]:
				singleFileMax[0] = fileClassCount
				singleFileMax[1] = filename

	classes_data = {'total_classes': totalClassCount, 'avg_per_file': totalClassCount/len(filesToCheck), 'single_file_max':singleFileMax }
	return classes_data