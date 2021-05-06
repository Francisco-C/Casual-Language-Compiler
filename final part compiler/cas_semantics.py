__author__ = "Francisco Caldeira, Faculdade de Ciências da Universidade de Lisboa"

import re

class TypeError(Exception):
	pass

class Context(object):

	def __init__(self):
		self.stack = [{}]
		self.def_after_not_decl = []
		self.current_fun = ""

	def get_type(self, name):
		for scope in self.stack:
			if name in scope:
				temp = scope[name]
				if temp[0] == "Declaration" and "_function" in name:
					var = name.replace("_function", "")
					raise TypeError(f"Function {var} is not defined in the context")
				else:
					return scope[name]

		if "_array" in name:
			var = name.replace("_array", "")
			raise TypeError(f"Array {var} is not defined in the context")
		elif "_function" in name:
			var = name.replace("_function", "")
			raise TypeError(f"Function {var} is not defined in the context")
		else:
			raise TypeError(f"Variable {name} is not defined in the context")

	def set_type(self, name, value):
		scope = self.stack[0]
		temp = scope.keys()
		for i in temp:
			if i == name:
				if scope[name][0] == "Definition":
					if value[0] == "Declaration":
						return
			
		scope[name] = value
		
	def has_fun(self, name, assinatura):
		for scope in self.stack:
			if name in scope:
				types1 = scope[name][2]
				types2 = assinatura[2]
				names1 = scope[name][3]
				names2 = assinatura[3]
				types1.sort()
				types2.sort()
				names1.sort()
				names2.sort()			
				if scope[name][0] == assinatura[0]:
					return True, 1
				elif (scope[name][0] != assinatura[0]) and ((scope[name][1] != assinatura[1]) or (len(scope[name][2]) != len(assinatura[2]))):
					return True, 2
				elif (types1 != types2) or (names1 != names2):
					return True, 3
		return False

	def has_var(self, name):
		for scope in self.stack:
			if name in scope:
				return True	
		return False

	def has_var_in_current_scope(self, name):
		return name in self.stack[0]

	def enter_scope(self):
		self.stack.insert(0, {})

	def exit_scope(self):
		self.stack.pop(0)

	def print_types(self, types):
		if types == "Int":
			return "%d"
		elif types == "Float":
			return "%f"
		elif types == "String":
			return "%s"
		elif types == "%d":
			return "Int"
		elif types == "%f":
			return "Float"
		elif types == "%s":
			return "String"
		else:
			return None

RETURN_CODE = "$ret"

def check_semantic(ctx:Context, node):
	if node["nt"] == 'Program':
		for Decls_Defs in node["Decls_Defs"]:
			name = Decls_Defs["name"]
			name += "_function"
			assinatura = (Decls_Defs["nt"], Decls_Defs["type"], [arg["type"] for arg in Decls_Defs["arguments"]], [arg["name"] for arg in Decls_Defs["arguments"]])

			for i in assinatura[2]:
				if i == "Void":
					assinatura[2].remove(i)
			if ctx.has_fun(name, assinatura):
				names = name.replace("_function", "")
				if ctx.has_fun(name, assinatura)[1] == 2 or ctx.has_fun(name, assinatura)[1] == 3:
					raise TypeError(f"Function {assinatura[0]} '{names}' doesn't match with '{names}' declaration")
				else:
					if assinatura[0] == "Definition":
						raise TypeError(f"Function {assinatura[0]} '{names}' is already defined in the context")
					else:
						raise TypeError(f"Function {assinatura[0]} '{names}' is already declared in the context")

			ctx.def_after_not_decl.append({'name' : name, 'decl_def' : Decls_Defs["nt"]})
			ctx.set_type(name, assinatura)
		
		for Decls_Defs in node["Decls_Defs"]:
			check_semantic(ctx, Decls_Defs)

	elif node["nt"] == "Var_decl":
		name = node["name"]
		var = name + "_array"
		if ctx.has_var_in_current_scope(name) or ctx.has_var_in_current_scope(var):
			raise TypeError(f"Variable '{name}' is alreadyd defined in the context")
		ctx.set_type(name, node["type"])

	elif node["nt"] == "Array_declaration":
		name = node["name"]
		var_type = node["type"]
		size = node["size"]
		var = name + "_array"
		if ctx.has_var_in_current_scope(name) or ctx.has_var_in_current_scope(var):
			raise TypeError(f"Array '{name}' is already defined in the context")
		
		size_type = check_semantic(ctx, size)
		if size_type != "Int":
			raise TypeError(f"Array '{name}' size must be Int but {size_type} was given")
		ctx.set_type(var, var_type)

	elif node["nt"] == "create_array":
		return check_semantic(ctx, node["array_size"])

	elif node["nt"] == "Var_declaration":		
		name = node["name"]
		var_type = node["type"]
		expr = node["expr"]
		expr_type = check_semantic(ctx, expr)

		var = name + "_array"
		if ctx.has_var_in_current_scope(name) or ctx.has_var_in_current_scope(var):
			raise TypeError(f"Variable '{name}' is already defined in the context")
		if var_type != expr_type:
			raise TypeError(f"Variable '{name}' has type '{var_type}' but expression has type '{expr_type}'")
		ctx.set_type(name, node["type"])

	elif node["nt"] == "Definition":
		ctx.enter_scope()
		ctx.set_type(RETURN_CODE, node["type"])

		ctx.current_fun = node["name"]

		for arg in node["arguments"]:
			ctx.set_type(arg["name"], arg["type"])

		for statments in node["block"]:
			if statments != None:
				check_semantic(ctx, statments)
		ctx.exit_scope()

	elif node["nt"] == "Statments":
		for statment in node["Statment"]:
			check_semantic(ctx, statment)

	elif node["nt"] == "Var":
		name = node["name"]
		if not ctx.has_var(name):
			if "_array" in name:
				name.replace("_array", "")
				raise TypeError(f"Array '{name}' is not defined in the context")
			else:
				raise TypeError(f"Variable '{name}' is not defined in the context")
		return ctx.get_type(name)

	elif node["nt"] == "get_array":
		return node["name"]

	elif node["nt"] == "Array":
		name = node["name"]
		if isinstance(name, dict):
			name = check_semantic(ctx, name)
		var = name
		name += "_array"
		var_type = ctx.get_type(name)
		index = node["index_type"]
		index_type = check_semantic(ctx, index)

		if not ctx.has_var(name):
			raise TypeError(f"Array '{var}' is not defined in the context")
		if index_type != "Int":
			raise TypeError(f"Array '{var}' index must be Int but got {index_type}")

		return ctx.get_type(name)

	elif node["nt"] == "Array_assignment":
		name = node["name"]
		var = name
		name += "_array"
		var_type = ctx.get_type(name)
		index = node["index_type"]
		expr = node["expr"]
		index_type = check_semantic(ctx, index)
		expr_type = check_semantic(ctx, expr)

		if not ctx.has_var(name):
			raise TypeError(f"Array '{var}' is not defined in the context")
		if index_type != "Int":
			raise TypeError(f"Array '{var}' index must be Int but got {index_type}")
		if var_type != expr_type:
			raise TypeError(f"Array '{var}' has type '{var_type}' but expression has type '{expr_type}'")

		return ctx.get_type(name)

	elif node["nt"] == "Var_assignment":
		name = node["name"]
		var_type = ctx.get_type(name)
		expr = node["expr"]
		expr_type = check_semantic(ctx, expr)

		if not ctx.has_var(name):
			raise TypeError(f"Variable '{name}' is not defined in the context")
		if var_type != expr_type:
			raise TypeError(f"Variable '{name}' has type '{var_type}' but expression has type '{expr_type}'")
		return ctx.get_type(name)
	
	elif node["nt"] == "Float" or node["nt"] == "Int" or node["nt"] == "String" or node["nt"] == "Boolean" or node["nt"] == "Void":				
		return node["nt"]

	elif node["nt"] == "Return":
		return_type = check_semantic(ctx, node["r_parameters"])		
		expected_return_type = ctx.get_type(RETURN_CODE)
		if return_type != expected_return_type:
			if return_type == "Void":
				raise TypeError(f"Return requires {expected_return_type} expression")
			elif expected_return_type == "Void":
				raise TypeError(f"Return should not have an expression")
			else:
				raise TypeError(f"Return expected {expected_return_type} but got {return_type}")

	elif node["nt"] == "fun_call":
		name = node["name"]
		naming = name
		name += "_function"
		counter = 0
		counter2 = 0
		
		index_decl = None
		index_def = None
		index_curr = None
		current_fun = ctx.current_fun + "_function"
		current_fun2 = ctx.current_fun 
		for decl_def in ctx.def_after_not_decl:
			if decl_def["name"] == name:
				if decl_def["decl_def"] == "Declaration":
					index_decl = ctx.def_after_not_decl.index(decl_def)
				else:
					index_def = ctx.def_after_not_decl.index(decl_def)
			elif decl_def["name"] == current_fun:
				index_curr = ctx.def_after_not_decl.index(decl_def)

		if index_decl == None:
			if index_def > index_curr:
				raise TypeError(f"Function {naming} is defined after function call declare or define it before {current_fun2}")
		else:
			if index_def > index_curr and index_decl > index_curr:
				raise TypeError(f"Function {naming} is defined after function call declare or define it before {current_fun2}")
				
		for j in node["arguments"]:
			counter += 1
			if j["nt"] == "Void":
				counter = 0

		(a, b, c, d) = ctx.get_type(name)
		temp = list((a, b, c, d))
		temp.remove(temp[0])
		temp.remove((temp[2]))
		(expected_return, args_type) = tuple(temp)

		if not args_type:
			args_type.append("Void")
		for k in args_type:
			counter2 += 1
			if k == "Void":
				counter2 = 0

		for (i, (arg, par_t)) in enumerate(zip(node["arguments"], args_type)):
			arg_t = check_semantic(ctx, arg)

			if counter > counter2 or counter < counter2:
				raise TypeError(f"'{naming}' function call needs {counter2} arguments but got {counter}")
			if arg_t != par_t:
				index = i + 1
				raise TypeError(f"Argument number {index} in '{naming}' function call was expecting {par_t} but got {arg_t}")
		
		return expected_return

	elif node["nt"] == "Uminus":
		expr = node["value"]
		expr_type = check_semantic(ctx, expr)

		if not ((expr_type == "Int") or (expr_type == "Float")):
				raise TypeError(f"Unary operator '-' expects Int or Float types but got '{expr_type}'")
		return expr_type

	elif node["nt"] == "Group_expr":
		return check_semantic(ctx, node["value"])

	elif node["nt"] == "Not_Unary":
		expr = node["value"]
		expr_type = check_semantic(ctx, expr)

		if not (expr_type == "Boolean"):
				raise TypeError(f"Unary operator '!' expects Boolean type but got '{expr_type}'")
		return "Boolean"

	elif node["nt"] == "Binop":
		if node["operator"] == "%":
			left = node["value_left"]
			right = node["value_right"]
			left_type = check_semantic(ctx, left)
			right_type = check_semantic(ctx, right)
			
			if not ((right_type == "Int" and left_type == "Int")):
				raise TypeError(f"Binary operator '%' expects Int at both sides but got '{left_type}' and '{right_type}' ")
			return left_type

		elif node["operator"] == "+" or node["operator"] == "-" or node["operator"] == "*" or node["operator"] == "/":
			operator = node["operator"]
			left = node["value_left"]
			right = node["value_right"]
			left_type = check_semantic(ctx, left)
			right_type = check_semantic(ctx, right)

			if not ((right_type == "Int" and left_type == "Int") or (right_type == "Float" and left_type == "Float")):
				raise TypeError(f"Binary operator '{operator}' expects Int or Float at both sides but got '{left_type}' and '{right_type}'")
			return left_type

		elif node["operator"] == ">" or node["operator"] == ">=" or node["operator"] == "<" or node["operator"] == "<=":
			operator = node["operator"]
			left = node["value_left"]
			right = node["value_right"]
			left_type = check_semantic(ctx, left)
			right_type = check_semantic(ctx, right)

			if not ((right_type == "Int" and left_type == "Int") or (right_type == "Float" and left_type == "Float")):
				raise TypeError(f"Binary operator '{operator}' expects Int or Float at both sides but got '{left_type}' and '{right_type}'")
			return "Boolean"

		elif node["operator"] == "==" or node["operator"] == "!=":
			operator = node["operator"]
			left = node["value_left"]
			right = node["value_right"]
			left_type = check_semantic(ctx, left)
			right_type = check_semantic(ctx, right)

			if not ((right_type == "Int" and left_type == "Int") or (right_type == "Float" and left_type == "Float") or (right_type == "Boolean" and left_type == "Boolean")):
				raise TypeError(f"Binary operator '{operator}' expects Int, Float or Boolean at both sides but got '{left_type}' and '{right_type}'")
			return "Boolean"

		elif node["operator"] == "&&" or node["operator"] == "||":
			operator = node["operator"]
			left = node["value_left"]
			right = node["value_right"]
			left_type = check_semantic(ctx, left)
			right_type = check_semantic(ctx, right)

			if not (right_type == "Boolean" and left_type == "Boolean"):
				raise TypeError(f"Binary operator '{operator}' expects Boolean at both sides but got '{left_type}' and '{right_type}'")
			return "Boolean"

	elif node["nt"] == "If" or node["nt"] == "While":
		stat = node["nt"]
		condition = node["condition"]
		if check_semantic(ctx, condition) != "Boolean":
			raise TypeError(f"{stat} condition expected Boolean type but got {check_semantic(ctx, condition)}")

		ctx.enter_scope()
		if node["block"] != None:
			for statment in node["block"]:
				check_semantic(ctx, statment)
		ctx.exit_scope()

	elif node["nt"] == "If_Else":
		stat = node["nt"]
		condition = node["condition"]
		if check_semantic(ctx, condition) != "Boolean":
			raise TypeError(f"{stat} condition expected Boolean type but got {check_semantic(ctx, condition)}")

		ctx.enter_scope()
		if node["if_block"] != None:
			for statment in node["if_block"]:
				check_semantic(ctx, statment)
		ctx.exit_scope()

		ctx.enter_scope()
		if node["else_block"] != None:
			for statment in node["else_block"]:
				check_semantic(ctx, statment)
		ctx.exit_scope()

	elif node["nt"] == "Print":
		string = node["print_str"]
		args = node["print_args"]

		s1 = "%f"
		s2 = "%d"
		s3 = "%s"

		n_float = string.count(s1)
		n_int = string.count(s2)
		n_str = string.count(s3)

		r1 = re.compile('|'.join([s1,s2,s3]))
		str_types = r1.findall(string)
		args_types = []
		n_args_needed = n_float + n_int + n_str
		n_args = 0
		for i in args:
			n_args += 1
			if i["nt"] == "Void":
				n_args = 0
			types = check_semantic(ctx, i)
			args_types.append(ctx.print_types(types))

		if n_args != n_args_needed:
			raise TypeError(f"Print needed {n_args_needed} arguments but {n_args} were given")

		if n_args != 0:
			for str_type, arg_type in zip(str_types, args_types):
				if str_type != arg_type:
					var1 = ctx.print_types(str_type)
					var2 = ctx.print_types(arg_type)
					raise TypeError(f"Print identifier '{str_type}' needs {var1} but {var2} was given")