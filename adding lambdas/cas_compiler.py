__author__ = "Francisco Caldeira, Faculdade de Ciências da Universidade de Lisboa"

import struct

class TypeError(Exception):
	pass

class Emitter(object):
	def __init__(self):
		self.stack = [{}]
		self.id_stack = [{}]
		self.current_fun = ("", "")
		self.count = 0
		self.lines = []
		self.labels = []
		self.unary = False
		self.unary_count = 0
		self.isDeclared = False
		self.array_type = []
		self.OR = False
		self.AND = False
		self.current_lambda = ("", "")
		self.current_lambda_call = ""
		self.lambda_call_counter = 0
		self.lambda_array_size = 0
		self.isLambda = False
		self.isLambdaArgs = False
		self.isClosure = False
		self.lambda_var_arg = []
		self.lambda_args = []
		self.lambda_llvm = []
		self.all_lambdas = []
		self.environment = []

	def store_label(self, label):
		self.labels.append(label)

	def get_label(self):
		var = self.labels
		return var

	def update_labels(self):
		self.labels = []

	def set_id_name(self, name, value):
		scope = self.id_stack[0]
		scope[name] = value

	def get_id_name(self, name):
		for scope in self.id_stack:
			if name in scope:
				return scope[name]

	def set_type(self, name, value):
		scope = self.stack[0]
		scope[name] = value

	def get_type(self, name):
		for scope in self.stack:
			if name in scope:
				return scope[name]

	def get_count(self):
		self.count += 1
		return self.count

	def get_id(self):
		id = self.get_count()
		return f"cas_{id}"

	def __lshift__(self, v):
		self.lines.append(v)

	def get_code(self):
		return "\n".join(self.lines)

	def get_pointer_name(self, n):
		return f"%point_{n}"

	def get_emitter_type(self, tipo):
		if tipo == "Int":
			tipo = "i32"
		elif tipo == "Float":
			tipo = "float"
		elif tipo == "Boolean":
			tipo = "zeroext i1"
		elif tipo == "String":
			tipo = "i8*"
		elif tipo == "Void":
			tipo = "void"
		return tipo

	def get_emitter_align(self, tipo):
		align = ""
		if tipo == "Int" or tipo == "i32":
			align = "align 4"
		elif tipo == "Float" or tipo == "float":
			align = "align 4"
		elif tipo == "Boolean":
			align = "align 1"
		elif tipo == "String" or tipo == "i8*":
			align = "align 8"
		elif tipo == "Void":
			align = ""
		return align

def compiler(node, emitter=None):
	if node["nt"] == "Program":
		emitter = Emitter()

		for using in node["Using"]:
			compiler(using, emitter)

		for Decls_Defs in node["Decls_Defs"]:
			compiler(Decls_Defs, emitter)
		
		return emitter.get_code()

	elif node["nt"] == "Using":
		if node["name"] == "print":
			emitter << "declare i32 @printf(i8*, ...) #1"
		elif node["name"] == "array_create":
			emitter << "declare i32 @array_create(i32) #1"
		elif node["name"] == "array_get":
			emitter << "declare i32 @array_get(i8*) #1"

	elif node["nt"] == "Declaration":
		fun_type = node["type"]
		fun_name = node["name"]
		tipo = emitter.get_emitter_type(fun_type)
		name = fun_name + "_function"
		emitter.set_type(name, tipo)
		emitter.isDeclared = True
		return 

	elif node["nt"] == "Definition":
		fun_type = node["type"]
		fun_name = node["name"]
		emitter.current_fun = (fun_name, fun_type)
		tipo = emitter.get_emitter_type(fun_type)
		args_emitter = ""

		name = fun_name + "_function"
		emitter.set_type(name, tipo)

		for arg in node["arguments"]:
			temp = emitter.get_emitter_type(arg["type"])
			if "i1" in temp:
				temp = "i1 zeroext"
			args_emitter += temp
			pname = emitter.get_pointer_name(arg["name"])
			args_emitter += f" {pname}, "
			if arg["name"] == "Void":
				args_emitter = ""
			else:
				name = arg["name"] + "_var_arg"
				tipo_arg = arg["type"]
				emitter.set_type(name, tipo_arg)

		args_emitter = args_emitter[:-2]
		if emitter.isLambda == True:
			emitter.lambda_llvm.append(f"define {tipo} @{fun_name}({args_emitter}) #0 {'{'}")
		else:
			emitter << f"define {tipo} @{fun_name}({args_emitter}) #0 {'{'}"

		for arg in node["arguments"]:
			if arg["name"] != "Void":
				if arg["type"] == "i32":
					arg["type"] = "Int"
				elif arg["type"] == "float":
					arg["type"] = "Float"
				elif arg["type"] == "i8*":
					arg["type"] = "String"
				arg_tipo = emitter.get_emitter_type(arg["type"])
				pname = emitter.get_pointer_name(arg["name"])
				registo = "%" + emitter.get_id()
				align = emitter.get_emitter_align(arg["type"])
				emitter.set_id_name(pname, registo)
				if "i1" in arg_tipo:
					arg_tipo = "i8"
					temp_reg = "%" + emitter.get_id()
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = alloca {arg_tipo}, {align}")
						emitter.lambda_llvm.append(f"  {temp_reg} = zext i1 {pname} to i8")
						emitter.lambda_llvm.append(f"  store {arg_tipo} {temp_reg}, {arg_tipo}* {registo}, {align}")
					else:
						emitter << f"  {registo} = alloca {arg_tipo}, {align}"
						emitter << f"  {temp_reg} = zext i1 {pname} to i8"
						emitter << f"  store {arg_tipo} {temp_reg}, {arg_tipo}* {registo}, {align}"
				else:
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = alloca {arg_tipo}, {align}")
						emitter.lambda_llvm.append(f"  store {arg_tipo} {pname}, {arg_tipo}* {registo}, {align}")
					else:
						emitter << f"  {registo} = alloca {arg_tipo}, {align}"
						emitter << f"  store {arg_tipo} {pname}, {arg_tipo}* {registo}, {align}"

		for stmt in node["block"]:
			if stmt != None:
				compiler(stmt, emitter)

		if emitter.isLambda == True:
			emitter.lambda_llvm.append("}")
		else:
			emitter << "}"
		return 

	elif node["nt"] == "Return":
		parameters = node["r_parameters"]
		registo = ""
		if parameters["nt"] == "Lambda":
			if parameters["arguments"][0]["nt"] == "Void":
				registo = compiler(parameters["expression"], emitter)
			else:
				if parameters["arguments"][0]["type"] == "Int":
					registo = "i32 0"
				elif parameters["arguments"][0]["type"] == "Float":
					registo = "float 0x0"
				elif parameters["arguments"][0]["type"] == "Boolean":
					registo = "i1 true"
				elif parameters["arguments"][0]["type"] == "String":
					n = emitter.get_count()
					str_decl = f"""@.casual_str_cas_{n} = private unnamed_addr constant [1 x i8] c"\\00", align 1"""
					emitter.lines.insert(0, str_decl)
					registo = f"i8* getelementptr inbounds ([1 x i8], [1 x i8]* @.casual_str_cas_{n}, i64 0, i64 0)"
			name = "$lambda$" + emitter.current_fun[0]
			emitter.current_lambda = (name, emitter.current_fun[1])
			compiler(parameters, emitter)
		else:
			registo = compiler(node["r_parameters"], emitter)
		if "i8" in registo and "*" not in registo:
			temp_reg = "%" + emitter.get_id()
			n = emitter.get_count() - 2
			if emitter.isLambda == True:
				emitter.lambda_llvm.append(f"  {temp_reg} = trunc i8 %cas_{n} to i1")
			else:
				emitter << f"  {temp_reg} = trunc i8 %cas_{n} to i1"
			registo = f"i1 {temp_reg}"
		if emitter.isLambda == True:
			emitter.lambda_llvm.append(f"  ret {registo}")
		else:
			emitter << f"  ret {registo}"

	elif node["nt"] == "Statments":
		for statment in node["Statment"]:
			compiler(statment, emitter)

	elif node["nt"] == "fun_call":
		vname = node["name"]
		name = vname + "_function"
		registo_args = ""
		emitter.isDeclared = False
		tipo = emitter.get_emitter_type(emitter.get_type(name)) 
		pname = emitter.get_pointer_name(vname) + "_" + str(emitter.get_count())

		if emitter.isLambdaArgs == True:
			return

		if emitter.isLambda == False:
			for fun in emitter.all_lambdas:
				if vname == fun["fun"]:
					for name in fun["env"]:
						if isinstance(name, dict):
							if name["nt"] == "Array":
								if name not in node["arguments"]:
									node["arguments"].append(name)
						else:
							arg = {'nt': 'Var', 'name': name}
							if arg not in node["arguments"]:
								node["arguments"].append(arg)

		if "$lambda$" in vname and emitter.isLambda == False:
			emitter.isClosure = True
			emitter.current_lambda_call = vname

		for args in node["arguments"]:
			if args["nt"] == "Void":
				registo_args = ""
			else:
				temp = compiler(args, emitter) + ", "
				if "i1" in temp:
					temp = temp.replace("i1", "i1 zeroext")
				elif "i8" in temp and "*" not in temp:
					var = temp.split(" ")
					var[1] = var[1].replace(",", "")
					temp_reg = "%" + emitter.get_id()
					emitter << f"  {temp_reg} = trunc i8 {var[1]} to i1"
					temp = f"i1 zeroext {temp_reg}, "
				registo_args += temp
		emitter.isClosure = False
		emitter.lambda_call_counter = 0
		registo_args = registo_args[:-2]
		if emitter.isLambda == True:
			if tipo == "void":
				emitter.lambda_llvm.append(f"  call {tipo} @{vname}({registo_args})")
			else:
				emitter.lambda_llvm.append(f"  {pname} = call {tipo} @{vname}({registo_args})")
		else:
			if tipo == "void":
				emitter << f"  call {tipo} @{vname}({registo_args})"
			else:
				emitter << f"  {pname} = call {tipo} @{vname}({registo_args})"

		if "i1" in tipo:
			temp_reg = "%" + emitter.get_id()
			emitter << f"  {temp_reg} = zext i1 {pname} to i8"
			tipo = "i8"
			pname = temp_reg

		return f"{tipo} {pname}"

	elif node["nt"] == "Var_assignment":
		vname = node["name"]
		expr = node["expr"]
		name = vname + "_var"

		if expr["nt"] == "Lambda":
			tipo = emitter.get_type(name)
			emitter.current_lambda = (vname, tipo)
			registo = compiler(expr, emitter)
			return

		registo = compiler(expr, emitter)
		pname = emitter.get_pointer_name(vname)
		tipo = emitter.get_emitter_type(emitter.get_type(name)) 
		align = emitter.get_emitter_align(emitter.get_type(name))

		if tipo == None:
			name = vname + "_var_arg"
			tipo = emitter.get_emitter_type(emitter.get_type(name)) 
			align = emitter.get_emitter_align(emitter.get_type(name))
			pname = emitter.get_id_name(pname)

		emitter << f"  store {registo}, {tipo}* {pname}, {align}"
		return

	elif node["nt"] == "Array_assignment":
		vname = node["name"]
		expr = node["expr"]
		index = node["index_type"]
		name = vname + "_array"

		pname = emitter.get_pointer_name(vname)
		tipo = emitter.get_emitter_type(emitter.get_type(name)) 
		align = emitter.get_emitter_align(emitter.get_type(name))

		arr_type = ""
		for arr in emitter.array_type:
			if arr["name"] == name:
				arr_type = arr["type"]

		registo = compiler(expr, emitter)
		reg = compiler(index, emitter)
		reg2 = reg.split(" ")
		i64_reg = "%" + emitter.get_id()
		temp = "%" + emitter.get_id()
		if "%" in reg2[1]:
			emitter << f"  {i64_reg} = sext {reg} to i64"
			emitter << f"  {temp} = getelementptr inbounds {arr_type}, {arr_type}* {pname}, i64 0, i64 {i64_reg}"
		else:
			emitter << f"  {temp} = getelementptr inbounds {arr_type}, {arr_type}* {pname}, i64 0, i64 {reg2[1]}"

		emitter << f"  store {registo}, {tipo}* {temp}, {align}"

	elif node["nt"] == "create_array":
		return compiler(node["array_size"], emitter)

	elif node["nt"] == "Array_declaration":
		vname = node["name"]
		pname = emitter.get_pointer_name(vname)
		tipo = emitter.get_emitter_type(node["type"])
		align = emitter.get_emitter_align(node["type"])

		name = vname + "_array"
		emitter.set_type(name, node["type"])

		if "i1" in tipo:
			tipo = "i8"

		size = compiler(node["size"], emitter)
		size = size.split(" ")
		if "%" in size[1]:
			raise TypeError(f"Array '{vname}' size must be a number, it can't be an expression, variable or function call")

		emitter << f"  {pname} = alloca [{size[1]} x {tipo}], {align}"
		emitter.array_type.append({"name": name, "type": f"[{size[1]} x {tipo}]"})
		return

	elif node["nt"] == "double_fun_call":
		name = node["name"]
		fun1 = {'nt': 'fun_call', 'name': name, 'arguments': node["arguments1"]}
		compiler(fun1, emitter)
		name = "$lambda$" + name
		fun2 = {'nt': 'fun_call', 'name': name, 'arguments': node["arguments2"]}
		return compiler(fun2, emitter)

	elif node["nt"] == "Lambda":
		index = 0
		for line in emitter.lines:
			if "define" in line:
				index = emitter.lines.index(line)
		
		emitter.lambda_args = []
		emitter.isLambda = True

		for arg in node["arguments"]:
			if arg != "Void":
				emitter.lambda_args.append({'nt': 'Var_decl', 'name': arg["name"], 'type': arg["type"]})

		expr = node["expression"]

		emitter.isLambdaArgs = True
		compiler(expr, emitter)
		emitter.isLambdaArgs = False
		array_types = 0
		counter = 0
		name2 = emitter.current_lambda[0]
		for name in emitter.environment:
			array_types += 1
		for name in emitter.environment:
			if "$" in name:
				var = name.split("$$$")
				location = emitter.get_id_name(emitter.get_pointer_name(var[0]))
			else:
				location = emitter.get_pointer_name(name)
			tipo = ""
			if "$" not in name:
				tipo = emitter.get_type(name + "_var")
			else:
				tipo = emitter.get_type(name)
			emitter_type = emitter.get_emitter_type(tipo)
			registo = "%" + emitter.get_id()
			align = emitter.get_emitter_align(emitter_type)
			emitter << f"  {registo} = load {emitter_type}, {emitter_type}* {location}, {align}"
			emitter << f"  store {emitter_type} {registo}, {emitter_type}* getelementptr inbounds ([{array_types} x {emitter_type}], [{array_types} x {emitter_type}]* @{name2}_args, i64 0, i64 {counter}), {align}"
			counter += 1

		array = f"@{name2}_args = dso_local global [{array_types} x {emitter_type}] zeroinitializer, {align}"
		emitter.lambda_array_size = array_types
		emitter.lines.insert(0, array)

		emitter.all_lambdas.append({"fun": emitter.current_lambda[0], "env": emitter.environment})
		lambda_fun = {'nt': 'Definition', 'name': emitter.current_lambda[0], 'arguments': emitter.lambda_args, \
					  'type': emitter.current_lambda[1], 'block': [None, {'nt': 'Return', 'r_parameters': expr}]}
		
		compiler(lambda_fun, emitter)
		for line in emitter.lambda_llvm:
			emitter.lines.insert(index, line)
			index += 1

		emitter.isLambda = False
		emitter.current_lambda = ("", "")
		emitter.lambda_llvm = []
		emitter.environment = []
		return

	elif node["nt"] == "Var_declaration":
		vname = node["name"]
		expr = node["expr"]
		pname = emitter.get_pointer_name(vname)
		tipo = emitter.get_emitter_type(node["type"])
		align = emitter.get_emitter_align(node["type"])

		if expr["nt"] == "Lambda":
			emitter.current_lambda = (vname, node["type"])
			registo = compiler(expr, emitter)
			return
		
		else:
			registo = compiler(expr, emitter)
			name = vname + "_var"
			emitter.set_type(name, node["type"])

			if "i1" in tipo:
				tipo = "i8"

			emitter << f"  {pname} = alloca {tipo}, {align}"
			
			if "i1" in registo:
				if "true" in registo:
					registo = "i8 1"
				elif "false" in registo:
					registo = "i8 0"

			emitter << f"  store {registo}, {tipo}* {pname}, {align}"
			return

	elif node["nt"] == "Var":
		vname = node["name"]
		name = vname + "_var"

		registo = "%" + emitter.get_id()
		pname = emitter.get_pointer_name(vname)
		if emitter.isLambda == True:
			if emitter.isLambdaArgs == True:
				name = node["name"]
				tipo = emitter.get_type(name + "_var")
				tipo2 = emitter.get_type(name + "_var_arg")
				if tipo != None:
					emitter.environment.append(name)
					arg = {'nt': 'Var_decl', 'name': node["name"], 'type': tipo}
					if arg not in emitter.lambda_args:
						emitter.lambda_args.append(arg)
				elif tipo2 != None:
					name = name + "$$$"
					emitter.environment.append(name)
					arg = {'nt': 'Var_decl', 'name': name, 'type': tipo2}
					if arg not in emitter.lambda_args:
						emitter.lambda_var_arg.append(name)
						emitter.set_type(name, tipo2)
						emitter.lambda_args.append(arg)
			else:
				name = vname + "$$$"
				if name not in emitter.lambda_var_arg:
					name = vname + "_var_arg"
					pname = emitter.get_id_name(pname)
				else:
					pname = emitter.get_id_name(emitter.get_pointer_name(name))
				tipo = emitter.get_emitter_type(emitter.get_type(name)) 
				align = emitter.get_emitter_align(emitter.get_type(name))
				
				if "i1" in tipo:
					tipo = "i8"
				emitter.lambda_llvm.append(f"  {registo} = load {tipo}, {tipo}* {pname}, {align}")
				return f"{tipo} {registo}"

		else:
			if "_function_" in name:
				return
			tipo = emitter.get_emitter_type(emitter.get_type(name)) 
			align = emitter.get_emitter_align(emitter.get_type(name))

			if tipo == None or emitter.isDeclared == True:
				name = vname + "_var_arg"
				pname = emitter.get_id_name(pname)
				if vname in emitter.lambda_var_arg:
					v = vname.split("$$$")
					name = v[0] + "_var_arg"
					pname = emitter.get_id_name(emitter.get_pointer_name(v[0]))				
				tipo = emitter.get_emitter_type(emitter.get_type(name))
				align = emitter.get_emitter_align(emitter.get_type(name))
			if emitter.isClosure == True:
				n = f"lambda_var_{emitter.lambda_call_counter}"
				array_types = emitter.lambda_array_size
				emitter << f"  {registo} = load {tipo}, {tipo}* getelementptr inbounds ([{array_types} x {tipo}], [{array_types} x {tipo}]* @{emitter.current_lambda_call}_args, i64 0, i64 {emitter.lambda_call_counter}), {align}"
				emitter.lambda_call_counter += 1
				return f"{tipo} {registo}"
			if "i1" in tipo:
				tipo = "i8"
			emitter << f"  {registo} = load {tipo}, {tipo}* {pname}, {align}"
			return f"{tipo} {registo}"

	elif node["nt"] == "get_array":
		return node["name"]

	elif node["nt"] == "Array":
		vname = node["name"]
		index = node["index_type"]
		if isinstance(vname, dict):
			vname = compiler(vname, emitter)
		
		name = vname + "_array"
		registo = "%" + emitter.get_id()
		pname = emitter.get_pointer_name(vname)

		if emitter.isLambda == True:
			if emitter.isLambdaArgs == True:
				tipo = emitter.get_type(name)
				if tipo != None:
					emitter.environment.append(node)
					if isinstance(node["name"], dict):
						node["name"] = node["name"]["name"]
					arg = {'nt': 'Var_decl', 'name': node["name"], 'type': tipo}
					if arg not in emitter.lambda_args:
						emitter.lambda_args.append(arg)
			else:
				tipo = emitter.get_emitter_type(emitter.get_type(name)) 
				align = emitter.get_emitter_align(emitter.get_type(name))
				pname = emitter.get_id_name(pname)

				if "i1" in tipo:
					tipo = "i8"

				emitter.lambda_llvm.append(f"  {registo} = load {tipo}, {tipo}* {pname}, {align}")
				return f"{tipo} {registo}"
		else:
			tipo = emitter.get_emitter_type(emitter.get_type(name)) 
			align = emitter.get_emitter_align(emitter.get_type(name))

			arr_type = ""
			for arr in emitter.array_type:
				if arr["name"] == name:
					arr_type = arr["type"]

			if "i1" in tipo:
				tipo = "i8"

			var = compiler(index, emitter)
			var2 = var.split(" ")
			i64_reg = "%" + emitter.get_id()
			temp = "%" + emitter.get_id()
			if "%" in var2[1]:
				emitter << f"  {i64_reg} = sext {var} to i64"
				emitter << f"  {temp} = getelementptr inbounds {arr_type}, {arr_type}* {pname}, i64 0, i64 {i64_reg}"
			else:
				emitter << f"  {temp} = getelementptr inbounds {arr_type}, {arr_type}* {pname}, i64 0, i64 {var2[1]}"

			emitter << f"  {registo} = load {tipo}, {tipo}* {temp}, {align}"
			return f"{tipo} {registo}"

	elif node["nt"] == "Int":
		tipo = emitter.get_emitter_type(node["nt"])
		valor = str(node["value"])
		return f"{tipo} {valor}"

	elif node["nt"] == "Boolean":
		tipo = "i1"
		valor = node["value"]
		return f"{tipo} {valor}"

	elif node["nt"] == "Void":
		return "void"

	elif node["nt"] == "String":
		tipo = emitter.get_emitter_type(node["nt"])
		value = node["value"]
		valor = value.replace('"', '')
		size = 1
		counter = valor.count("\\n")
		size += counter
		value = valor.replace("\\n", "")
		size += len(value)
		valor = valor.replace("\\n", "\\0A")
		id = emitter.get_id()
		str_name = f"@.casual_str_{id}"
		
			
		str_decl = f"""{str_name} = private unnamed_addr constant [{size} x i8] c"{valor}\\00", align 1"""
		emitter.lines.insert(0, str_decl)

		return f"i8* getelementptr inbounds ([{size} x i8], [{size} x i8]* {str_name}, i64 0, i64 0)"

	elif node["nt"] == "Float":
		tipo = emitter.get_emitter_type(node["nt"])
		value = node["value"]
		float_single = struct.unpack('f', struct.pack('f', value))[0]
		valor = hex(struct.unpack('<Q', struct.pack('<d', float_single))[0])
		return f"{tipo} {valor}"

	elif node["nt"] == "Print":
		string = node["print_str"]
		new_node = {'nt': 'String', 'value': string}
		string_reg = compiler(new_node, emitter)
		
		args = ""
		for arg in node["print_args"]:
			if arg["nt"] == "Void":
				args = ""
			else:
				temp = compiler(arg, emitter)
				if "float" in temp:
					reg = "%" + emitter.get_id()
					emitter << f"  {reg} = fpext {temp} to double"
					temp = f"double {reg}"
				args += ","
				args += temp
		
		print_reg = "%" + emitter.get_id()
		emitter << f"  call i32 (i8*, ...) @printf({string_reg}{args})"

	elif node["nt"] == "Group_expr":
		return compiler(node["value"], emitter)

	elif node["nt"] == "If":
		condition = node["condition"]
		block = node["block"]

		emitter.update_labels()

		if_id = emitter.get_id()
		label_start = "if_start_" + if_id
		label_end = "if_end_" + if_id
		
		emitter.store_label(label_start)
		emitter.store_label(label_end)
		emitter.store_label(-1)
		reg = compiler(condition, emitter)

		if "AND" in reg:
			if "1" in reg:
				emitter << f"  br label %{label_end}"
			else:
				if "not" in reg:
					emitter << f"  br label %{label_end}"
				else:
					emitter << f"  br label %{label_start}"
			emitter << f"{label_start}:"
			for stmt in block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_end}:"
		elif "OR" in reg:
			if "1" in reg:
				emitter << f"  br label %{label_start}"
			else:
				if "not" in reg:
					emitter << f"  br label %{label_start}"
				else:
					emitter << f"  br label %{label_end}"
			emitter << f"{label_start}:"

			for stmt in block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_end}:"
		else:
			if "not" in reg:
				reg = reg.split("-")
				emitter << f"  br {reg[1]}, label %{label_end}, label %{label_start}"
			else:
				emitter << f"  br {reg}, label %{label_start}, label %{label_end}"
			emitter << f"{label_start}:"

			for stmt in block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_end}:"
		return

	elif node["nt"] == "If_Else":
		condition = node["condition"]
		if_block = node["if_block"]
		else_block = node["else_block"]

		emitter.update_labels()
	
		if_id = emitter.get_id()
		label_start = "if_start_" + if_id
		label_else = "if_else_" + if_id
		label_end = "if_end_" + if_id

		emitter.store_label(label_start)
		emitter.store_label(label_else)
		emitter.store_label(-1)

		reg = compiler(condition, emitter)

		if "AND" in reg:
			if "1" in reg:
				emitter << f"  br label %{label_else}"
			else:
				if "not" in reg:
					emitter << f"  br label %{label_else}"
				else:
					emitter << f"  br label %{label_start}"

			emitter << f"{label_start}:"
			for stmt in if_block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_else}:"
			for stmt in else_block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_end}:"
		elif "OR" in reg:
			if "1" in reg:
				emitter << f"  br label %{label_start}"
			else:
				if "not" in reg:
					emitter << f"  br label %{label_start}"
				else:
					emitter << f"  br label %{label_else}"
			
			emitter << f"{label_start}:"
			for stmt in if_block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_else}:"
			for stmt in else_block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_end}:"

		else:
			if "not" in reg:
				reg = reg.split("-")
				emitter << f"  br {reg[1]}, label %{label_else}, label %{label_start}"
			else:
				emitter << f"  br {reg}, label %{label_start}, label %{label_else}"
			emitter << f"{label_start}:"

			for stmt in if_block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_else}:"
			for stmt in else_block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_end}"

			emitter << f"{label_end}:"
		return

	elif node["nt"] == "While":
		condition = node["condition"]
		block = node["block"]

		emitter.update_labels()

		while_id = emitter.get_id()
		label_start = "while_start_" + while_id
		label_block = "while_block_" + while_id
		label_end = "while_end_" + while_id

		emitter << f"  br label %{label_start}"
		emitter << f"{label_start}:"

		emitter.store_label(label_block)
		emitter.store_label(label_end)
		emitter.store_label(-1)

		reg = compiler(condition, emitter)

		if "AND" in reg:
			if "1" in reg:
				emitter << f"  br label %{label_end}"
			else:
				if "not" in reg:
					emitter << f"  br label %{label_end}"
				else:
					emitter << f"  br label %{label_block}"

			emitter << f"{label_block}:"
			for stmt in block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_start}"

			emitter << f"{label_end}:"

		elif "OR" in reg:
			if "1" in reg:
				emitter << f"  br label %{label_block}"
			else:
				if "not" in reg:
					emitter << f"  br label %{label_block}"
				else:
					emitter << f"  br label %{label_end}"

			emitter << f"{label_block}:"
			for stmt in block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_start}"

			emitter << f"{label_end}:"

		else:
			if "not" in reg:
				reg = reg.split("-")
				emitter << f"  br {reg[1]}, label %{label_end}, label %{label_block}"
			else:
				emitter << f"  br {reg}, label %{label_block}, label %{label_end}"

			emitter << f"{label_block}:"
			for stmt in block:
				if stmt != None:
					compiler(stmt, emitter)
			emitter << f"  br label %{label_start}"

			emitter << f"{label_end}:"
		return

	elif node["nt"] == "Uminus":
		registo = compiler(node["value"], emitter)
		registo = registo.split(" ")
		return f"{registo[0]} -{registo[1]}"

	elif node["nt"] == "Not_Unary":
		emitter.unary_count += 1
		expr = node["value"]

		if expr["nt"] != "Not_Unary":
			if emitter.unary_count % 2 == 0:
				emitter.unary_count = 0
				reg = compiler(expr["value"], emitter)
				return reg
			else:
				if expr["nt"] == "Group_expr":		
					var = expr["value"]
					if var["operator"] == "&&" or var["operator"] == "||":
						emitter.unary = True

				emitter.unary_count = 0
				reg = compiler(expr, emitter)
				return f"not-{reg}"
		else:
			reg = compiler(expr, emitter)
			return reg
		
	elif node["nt"] == "Binop":
		if node["operator"] == "+":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			if emitter.isLambdaArgs == False:
				registo_r = temp.split(" ")
				registo = "%" + emitter.get_id()
				if registo_r[0] == "float":
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = fadd {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = fadd {registo_l}, {registo_r[1]}"
				else:
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = add nsw {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = add nsw {registo_l}, {registo_r[1]}"
				return f"{registo_r[0]} {registo}"

		elif node["operator"] == "-":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			if emitter.isLambdaArgs == False:
				registo_r = temp.split(" ")
				registo = "%" + emitter.get_id()
				if registo_r[0] == "float":
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = fsub {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = fsub {registo_l}, {registo_r[1]}"
				else:
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = sub nsw {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = sub nsw {registo_l}, {registo_r[1]}"
				return f"{registo_r[0]} {registo}"

		elif node["operator"] == "*":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			if emitter.isLambdaArgs == False:
				registo_r = temp.split(" ")
				registo = "%" + emitter.get_id()
				if registo_r[0] == "float":
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = fmul {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = fmul {registo_l}, {registo_r[1]}"
				else:
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = mul nsw {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = mul nsw {registo_l}, {registo_r[1]}"
				return f"{registo_r[0]} {registo}"

		elif node["operator"] == "/":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			if emitter.isLambdaArgs == False:
				registo_r = temp.split(" ")
				registo = "%" + emitter.get_id()
				if registo_r[0] == "float":
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = fdiv {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = fdiv {registo_l}, {registo_r[1]}"
				else:
					if emitter.isLambda == True:
						emitter.lambda_llvm.append(f"  {registo} = sdiv {registo_l}, {registo_r[1]}")
					else:
						emitter << f"  {registo} = sdiv {registo_l}, {registo_r[1]}"
				return f"{registo_r[0]} {registo}"

		elif node["operator"] == "%":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			if emitter.isLambdaArgs == False:
				registo_r = temp.split(" ")
				registo = "%" + emitter.get_id()
				if emitter.isLambda == True:
					emitter.lambda_llvm.append(f"  {registo} = srem {registo_l}, {registo_r[1]}")
				else:
					emitter << f"  {registo} = srem {registo_l}, {registo_r[1]}"
				return f"{registo_r[0]} {registo}"

		elif node["operator"] == ">":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			registo_r = temp.split(" ")
			registo = "%" + emitter.get_id()
			if registo_r[0] == "float":
				emitter << f"  {registo} = fcmp ogt {registo_l}, {registo_r[1]}"
			else:
				emitter << f"  {registo} = icmp sgt {registo_l}, {registo_r[1]}"
			return f"i1 {registo}"

		elif node["operator"] == "<":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			registo_r = temp.split(" ")
			registo = "%" + emitter.get_id()
			if registo_r[0] == "float":
				emitter << f"  {registo} = fcmp olt {registo_l}, {registo_r[1]}"
			else:
				emitter << f"  {registo} = icmp slt {registo_l}, {registo_r[1]}"
			return f"i1 {registo}"

		elif node["operator"] == ">=":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			registo_r = temp.split(" ")
			registo = "%" + emitter.get_id()
			if registo_r[0] == "float":
				emitter << f"  {registo} = fcmp oge {registo_l}, {registo_r[1]}"
			else:
				emitter << f"  {registo} = icmp sge {registo_l}, {registo_r[1]}"
			return f"i1 {registo}"

		elif node["operator"] == "<=":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			registo_r = temp.split(" ")
			registo = "%" + emitter.get_id()
			if registo_r[0] == "float":
				emitter << f"  {registo} = fcmp ole {registo_l}, {registo_r[1]}"
			else:
				emitter << f"  {registo} = icmp sle {registo_l}, {registo_r[1]}"
			return f"i1 {registo}"

		elif node["operator"] == "!=":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			registo_r = temp.split(" ")

			if "i8" in registo_l:
				reg1 = "%" + emitter.get_id()
				reg2 = "%" + emitter.get_id()
				emitter << f"  {reg1} = trunc {registo_l} to i1"
				emitter << f"  {reg2} = zext i1 {reg1} to i32"
				registo_l = f"i32 {reg2}"
			elif "i1" in registo_l:
				if "true" in registo_l:
					value = 1
				else:
					value = 0
				registo_l = f"i32 {value}"

			if registo_r[0] == "i1":
				if registo_r[1] == "true":
					registo_r[1] = 1
				else:
					registo_r[1] = 0
			elif registo_r[0] == "i8":
				reg1 = "%" + emitter.get_id()
				reg2 = "%" + emitter.get_id()
				emitter << f"  {reg1} = trunc {registo_r[0]} {registo_r[1]} to i1"
				emitter << f"  {reg2} = zext i1 {reg1} to i32"
				registo_r[1] = f"{reg2}"

			registo = "%" + emitter.get_id()
			if registo_r[0] == "float":
				emitter << f"  {registo} = fcmp une {registo_l}, {registo_r[1]}"
			else:
				emitter << f"  {registo} = icmp ne {registo_l}, {registo_r[1]}"
			return f"i1 {registo}"

		elif node["operator"] == "==":
			left = node["value_left"]
			right = node["value_right"]
			registo_l = compiler(left, emitter)
			temp = compiler(right, emitter)
			registo_r = temp.split(" ")
						
			if "i8" in registo_l:
				reg1 = "%" + emitter.get_id()
				reg2 = "%" + emitter.get_id()
				emitter << f"  {reg1} = trunc {registo_l} to i1"
				emitter << f"  {reg2} = zext i1 {reg1} to i32"
				registo_l = f"i32 {reg2}"
			elif "i1" in registo_l:
				if "true" in registo_l:
					value = 1
				else:
					value = 0
				registo_l = f"i32 {value}"

			if registo_r[0] == "i1":
				if registo_r[1] == "true":
					registo_r[1] = 1
				else:
					registo_r[1] = 0
			elif registo_r[0] == "i8":
				reg1 = "%" + emitter.get_id()
				reg2 = "%" + emitter.get_id()
				emitter << f"  {reg1} = trunc {registo_r[0]} {registo_r[1]} to i1"
				emitter << f"  {reg2} = zext i1 {reg1} to i32"
				registo_r[1] = f"{reg2}"

			registo = "%" + emitter.get_id()
			if registo_r[0] == "float":
				emitter << f"  {registo} = fcmp oeq {registo_l}, {registo_r[1]}"
			else:
				emitter << f"  {registo} = icmp eq {registo_l}, {registo_r[1]}"
			return f"i1 {registo}"

		elif node["operator"] == "&&":
			left = node["value_left"]
			right = node["value_right"]
			
			labels = emitter.get_label()
			label_and = "start_and_" + labels[0][9:]
			label_or = labels[1]
			var = emitter.get_count()
			var2 = emitter.get_count()
			temp = ""
			temp_not = ""
			if emitter.unary == True:
				
				reg_l = compiler(left, emitter)
				if "OR" not in reg_l and "AND" not in reg_l:
					if "not" in reg_l:
						reg_l = reg_l.split("-")
						emitter << f"  br {reg_l[1]}, label %{labels[0]}, label %{label_and}_{var}"
					else:
						emitter << f"  br {reg_l}, label %{label_and}_{var}, label %{labels[0]}"
					emitter << f"{label_and}_{var}:"

				reg_r = compiler(right, emitter)
				if "OR" not in reg_r and "AND" not in reg_r:
					if "not" in reg_r:
						reg_r = reg_r.split("-")
						emitter << f"  br {reg_r[1]}, label %{labels[0]}, label %{label_and}_{var2}"
					else:						
						emitter << f"  br {reg_r}, label %{label_and}_{var2}, label %{labels[0]}"
					emitter << f"{label_and}_{var2}:"
				temp_not = "not"
				emitter.unary = False
			else:
				if emitter.OR == True:
					label_or = f"{label_and}_{var2}"

				emitter.AND = True
				reg_l = compiler(left, emitter)
				if "OR" not in reg_l and "AND" not in reg_l:
					if "not" in reg_l:
						reg_l = reg_l.split("-")
						emitter << f"  br {reg_l[1]}, label %{label_or}, label %{label_and}_{var}"
					else:
						emitter << f"  br {reg_l}, label %{label_and}_{var}, label %{label_or}"
					emitter << f"{label_and}_{var}:"

				emitter.AND = False
				reg_r = compiler(right, emitter)
				if "OR" not in reg_r and "AND" not in reg_r:
					if "not" in reg_r:
						reg_r = reg_r.split("-")
						emitter << f"  br {reg_r[1]}, label %{labels[1]}, label %{label_and}_{var2}"
					else:						
						emitter << f"  br {reg_r}, label %{label_and}_{var2}, label %{labels[1]}"
					emitter << f"{label_and}_{var2}:"
			
			if "OR" in reg_r:
				temp = "1"
			return f"AND {temp} {temp_not}"

		elif node["operator"] == "||":
			left = node["value_left"]
			right = node["value_right"]

			labels = emitter.get_label()
			label_and = "start_or_" + labels[0][9:]
			label_and2 = labels[0]
			var = emitter.get_count()
			var2 = emitter.get_count()
			temp = ""
			temp_not = ""

			if emitter.unary == True:
				
				reg_l = compiler(left, emitter)
				if "OR" not in reg_l and "AND" not in reg_l:
					if "not" in reg_l:
						reg_l = reg_l.split("-")
						emitter << f"  br {reg_l[1]}, label %{label_and}_{var}, label %{labels[1]}"
					else:
						emitter << f"  br {reg_l}, label %{labels[1]}, label %{label_and}_{var}"
					emitter << f"{label_and}_{var}:"

				reg_r = compiler(right, emitter)
				if "OR" not in reg_r and "AND" not in reg_r:
					if "not" in reg_r:
						reg_r = reg_r.split("-")
						emitter << f"  br {reg_r[1]}, label %{label_and}_{var2}, label %{labels[1]}"
					else:						
						emitter << f"  br {reg_r}, label %{labels[1]}, label %{label_and}_{var2}"
					emitter << f"{label_and}_{var2}:"

				temp_not = "not"
				emitter.unary = False
			else:
				if emitter.AND == True:
					label_and2 = f"{label_and}_{var2}"

				emitter.OR = True
				reg_l = compiler(left, emitter)
				if "OR" not in reg_l and "AND" not in reg_l:
					if "not" in reg_l:
						reg_l = reg_l.split("-")
						emitter << f"  br {reg_l[1]}, label %{label_and}_{var}, label %{label_and2}"
					else:
						emitter << f"  br {reg_l}, label %{label_and2}, label %{label_and}_{var}"
					emitter << f"{label_and}_{var}:"

				emitter.OR = False
				reg_r = compiler(right, emitter)
				if "OR" not in reg_r and "AND" not in reg_r:
					if "not" in reg_r:
						reg_r = reg_r.split("-")
						emitter << f"  br {reg_r[1]}, label %{label_and}_{var2}, label %{labels[0]}"
					else:						
						emitter << f"  br {reg_r}, label %{labels[0]}, label %{label_and}_{var2}"
					emitter << f"{label_and}_{var2}:"
		
			if "AND" in reg_r:
				temp = "1"
			return f"OR {temp} {temp_not}"