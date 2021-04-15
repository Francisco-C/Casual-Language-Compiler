__author__ = "Francisco Caldeira, Faculdade de Ciências da Universidade de Lisboa"

tokens = ('VARIABLE', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'LPAREN', 'RPAREN', 'EQUALS', 'NOT_EQUALS', 'EQUALS_EQUALS', 'AND', 'OR', 
		  'SEMICOLON', 'COLON', 'COMMA', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET','GREATER', 'LESS', 'GREATER_EQUAL', 'LESS_EQUAL',
		  'NOT_UNARY', 'TRUE', 'FALSE', 'WHILE', 'IF', 'ELSE', 'DECL', 'DEF', 'RETURN', 'INT', 'FLOAT', 'STRING', 'TYPE_INT', 'TYPE_FLOAT',
		  'TYPE_VOID', 'TYPE_STRING', 'TYPE_BOOLEAN', 'GETARRAY')

t_PLUS    		= r'\+'
t_MINUS   		= r'-'
t_TIMES   		= r'\*' 
t_DIVIDE  		= r'/'
t_MOD			= r'%'
t_LPAREN  		= r'\('
t_RPAREN  		= r'\)'
t_SEMICOLON		= r';'
t_COLON 		= r':'
t_COMMA 		= r','
t_LBRACE		= r'\{'
t_RBRACE		= r'\}'
t_LBRACKET		= r'\['
t_RBRACKET		= r']'
t_EQUALS  		= r'='
t_NOT_EQUALS 	= r'!='
t_EQUALS_EQUALS = r'=='
t_AND			= r'&&'
t_OR			= r'\|\|'
t_GREATER 		= r'\>'
t_LESS 			= r'\<'
t_GREATER_EQUAL = r'\>='
t_LESS_EQUAL	= r'\<='
t_NOT_UNARY		= r'!'
t_STRING		= r'"(([a-zA-Z]*)|[a-zA-Z]+([\\][a-zA-Z]+)+)"'
t_VARIABLE 		= r'[a-zA-Z_][a-zA-Z0-9_]*'


def t_FLOAT(t):
	r'\d*\.\d+'
	try:
		t.value = float(t.value)
	except ValueError:
		print("Float value too large %d", t.value)
		t.value = 0
	return t

def t_INT(t):
    r'\d[\d_]*\d|\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

def t_TRUE(t):
	r'true'
	return t

def t_FALSE(t):
	r'false'
	return t

def t_WHILE(t):
	r'while'
	return t

def t_IF(t):
	r'if'
	return t

def t_ELSE(t):
	r'else'
	return t

def t_RETURN(t):
	r'return'
	return t

def t_DECL(t):
	r'decl'
	return t

def t_DEF(t):
	r'def'
	return t

def t_TYPE_INT(t):
 	r'Int'
 	return t

def t_TYPE_FLOAT(t):
 	r'Float'
 	return t

def t_TYPE_VOID(t):
 	r'Void'
 	return t

def t_TYPE_STRING(t):
 	r'String'
 	return t

def t_TYPE_BOOLEAN(t):
	r'Boolean'
	return t

def t_GETARRAY(t):
	r'get_array()'
	return t

t_ignore = " \t"
t_ignore_COMMENT = r'\#.*'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

import ply.lex as lex
import sys
from collections.abc import Iterable

#sys.tracebacklimit = 0

lexer = lex.lex()

precedence = (
	('left','AND','OR'),
	('nonassoc','EQUALS_EQUALS','NOT_EQUALS'),
	('nonassoc','GREATER','LESS','GREATER_EQUAL','LESS_EQUAL','NOT_UNARY'),
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE','MOD'),
    ('right','UMINUS'),
    )

names = { }

start = 'program'

def p_program_helper(t):
	'''program_helper : declaration program_helper
	                  | definition program_helper
	                  | declaration
	                  | definition'''
	if len(t) == 2:
		t[0] = [t[1]]
	else:
		t[0] = [t[1], t[2]]

def p_program(t):
	'''program : program_helper'''
	t[0] = {'nt': 'Program', 'Decls_Defs': list(list_helper(t[1]))}

def p_declaration(t):
	'''declaration : DECL VARIABLE LPAREN arguments RPAREN type
				   | DECL VARIABLE LPAREN empty_args RPAREN type'''
	if len(t) == 7:
		t[0] = {'nt': 'Declaration', 'name': t[2], 'arguments': list(list_helper([t[4]])), 'type': t[6]}
	else:
		t[0] = {'nt': 'Declaration', 'name': t[2], 'arguments': list(list_helper([t[4]])), 'type': t[6]}	

def p_definition(t):
	'''definition : DEF VARIABLE LPAREN arguments RPAREN type LBRACE def_block  return RBRACE
	              | DEF VARIABLE LPAREN empty_args RPAREN type LBRACE def_block return RBRACE'''
	
	t[0] = {'nt': 'Definition', 'name': t[2], 'arguments': list(list_helper([t[4]])), 'type': t[6], 'block': list(list_helper([t[8], t[9]]))}
	
def p_type(t):
	'''type : COLON TYPE_INT
			| COLON TYPE_FLOAT
			| COLON TYPE_VOID
			| COLON TYPE_STRING
			| COLON TYPE_BOOLEAN'''
	t[0] = t[2]

def p_array_type(t):
	'''array_type : COLON LBRACKET TYPE_INT RBRACKET
				  | COLON LBRACKET TYPE_FLOAT RBRACKET
				  | COLON LBRACKET TYPE_VOID RBRACKET
				  | COLON LBRACKET TYPE_STRING RBRACKET
				  | COLON LBRACKET TYPE_BOOLEAN RBRACKET'''
	t[0] = t[3]

def p_empty(t):
	'''empty : '''

def p_empty_args(t):
	'''empty_args : '''
	t[0] = {'nt': 'Void', 'name': 'Void', 'type': 'Void'}

def p_empty_args_inv(t):
	'''empty_args_inv : '''
	t[0] = {'nt': 'Void', 'value': 'Void'}

def p_argument_helper(t):
	'''args : VARIABLE type COMMA args
	        | VARIABLE type'''
	if len(t) == 3:
		t[0] = {'nt': 'Var_decl', 'name': t[1], 'type': t[2]}
	else:
		t[0] = [{'nt': 'Var_decl', 'name': t[1], 'type': t[2]}, t[4]]

def p_arguments(t):
	'''arguments : args'''
	temp = [t[1]]
	t[0] = list(list_helper(temp))	     

def p_arguments_funinvocation_helper(t):
	'''args_inv : expression COMMA args_inv
	            | expression'''
	if len(t) == 2:
		t[0] = t[1]
	else:
		t[0] = [t[1], t[3]]

def p_arguments_funinvocation(t):
	'''arguments_funinvocation : args_inv
	                           | empty_args_inv'''
	temp = [t[1]]
	t[0] = list(list_helper(temp))

def p_statment_helper(t):
	'''stats : statment
	         | statment stats'''
	if len(t) == 2:
		t[0] = [t[1]]
	else:
		t[0] = [t[1],t[2]]

def p_statments(t):
	'''statments : stats'''
	temp = [{'nt': 'Statments', 'Statment': list(list_helper(t[1]))}]
	t[0] = temp

def p_def_statment_helper(t):
	'''def_stats : def_statment
	             | def_statment def_stats'''
	if len(t) == 2:
		t[0] = [t[1]]
	else:
		t[0] = [t[1],t[2]]

def p_def_statments(t):
	'''def_statments : def_stats'''
	temp = [{'nt': 'Statments', 'Statment': list(list_helper(t[1]))}]
	t[0] = temp

def p_def_statment(t):
	'''def_statment : statment_expression
				    | if
				    | while
				    | var_decl
				    | var_assign
				    | array_decl
				    | array_assign'''
	t[0] = t[1]

def p_block(t):
	'''block : LBRACE statments RBRACE
	         | LBRACE empty RBRACE'''

	t[0] = t[2]

def p_def_block(t):
	'''def_block : def_statments
	             | empty'''
	t[0] = t[1]

def p_statment(t):
	'''statment : return
				| statment_expression
				| if
				| while
				| var_decl
				| var_assign
				| array_decl
				| array_assign'''
	t[0] = t[1]

def p_statment_return(t):
	'''return : RETURN empty_args SEMICOLON
			  | RETURN expression SEMICOLON'''
	if len(t) == 3:
		t[0] = {'nt': 'Return', 'r_parameters': None}
	else:
		t[0] = {'nt': 'Return', 'r_parameters': t[2]}

def p_statment_expression(t):
	'''statment_expression : expression SEMICOLON'''
	t[0] = t[1]

def p_statment_if(t):
	'''if : IF expression block else
	      | IF expression block empty'''
	if t[4] is None:
		t[0] = {'nt': 'If', 'condition': t[2], 'block': t[3]}
	else:
		t[0] = [{'nt': 'If', 'condition': t[2], 'block': t[3]}, t[4]]

def p_statment_else(t):
	'''else : ELSE block'''
	t[0] = {'nt': 'Else', 'block': t[2]}

def p_statment_while(t):
	'''while : WHILE expression block'''
	t[0] = {'nt': 'While', 'condition': t[2], 'block': t[3]}

def p_statment_vardecl(t):
	'''var_decl : VARIABLE type EQUALS expression SEMICOLON'''
	t[0] = {'nt': 'Var_declaration', 'name': t[1], 'type': t[2], 'expr': t[4]}

def p_statment_arraydecl(t):
	'''array_decl : VARIABLE array_type SEMICOLON'''
	t[0] = {'nt': 'Array_declaration', 'name': t[1], 'type': t[2]}

def p_statment_varassign(t):
	'''var_assign : VARIABLE EQUALS expression SEMICOLON'''
	t[0] = {'nt': 'Var_assignment', 'name': t[1], 'expr': t[3]}

def p_statment_arrayassign(t):
	'''array_assign : VARIABLE LBRACKET expression RBRACKET EQUALS expression SEMICOLON'''
	t[0] = {'nt': 'Array_assignment', 'name': t[1], 'index_type': t[3], 'expr': t[6]}

def p_expression_binop(t):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression                 
                  | expression MOD expression            
                  | expression AND expression
                  | expression OR expression
                  | expression EQUALS_EQUALS expression
                  | expression NOT_EQUALS expression
                  | expression GREATER expression
                  | expression LESS expression
                  | expression GREATER_EQUAL expression
                  | expression LESS_EQUAL expression'''
    t[0] = {'nt': 'Binop', 'operator': t[2], 'value_left': t[1], 'value_right': t[3]}

def p_expression_uminus(t):
    '''expression : MINUS expression %prec UMINUS'''
    t[0] = {'nt': 'Uminus', 'value': t[2]}

def p_expression_group(t):
    '''expression : LPAREN expression RPAREN'''
    t[0] = {'nt': 'Group_expr', 'value': t[2]}

def p_expression_float(t):
	'''expression : FLOAT'''
	t[0] = {'nt': 'Float', 'value': t[1]}

def p_expression_int(t):
	'''expression : INT'''
	t[0] = {'nt': 'Int', 'value': t[1]}

def p_expression_string(t):
	'''expression : STRING'''
	t[0] = {'nt': 'String', 'value': t[1]}

def p_expression_var(t):
	'''expression : VARIABLE'''
	t[0] = {'nt': 'Var', 'name': t[1]}

def p_expression_boolean(t):
	'''expression : TRUE
				  | FALSE'''
	t[0] = {'nt': 'Boolean', 'value': t[1]}

def p_expression_notunary(t):
	'''expression : NOT_UNARY expression'''
	t[0] = {'nt': 'Not_Unary', 'value': t[2]}

def p_expression_index(t):
	'''expression : VARIABLE LBRACKET expression RBRACKET
				  | GETARRAY LBRACKET expression RBRACKET'''
	t[0] = {'nt': 'Array', 'name': t[1], 'index_type': t[3]}

def p_expression_funinvocation(t):
	'''expression : VARIABLE LPAREN arguments_funinvocation RPAREN'''
	t[0] = {'nt': 'fun_call', 'name': t[1], 'arguments': t[3]}              

def find_column(input, t):
	line_start = input.rfind('\n', 0, t.lexpos) + 1
	return (t.lexpos - line_start) + 1

def p_error(t):
	if t is not None:
		column = find_column(code, t)		
		print("Found unexpected character '%s' at line '%s' and column '%s'" % (t.value, t.lineno, column))
	else:
		print("Unexpected end of input!Empty file or syntax error at EOF!")

def list_helper(lis):
     for item in lis:
         if isinstance(item, Iterable) and not isinstance(item, dict):
             for x in list_helper(item):
                 yield x
         else:        
             yield item

import ply.yacc as yacc

parser = yacc.yacc()

class TypeError(Exception):
	pass

class Context(object):

	def __init__(self):
		self.stack = [{}]

	def get_type(self, name):
		for scope in self.stack:
			if name in scope:
				return scope[name]
		if "_array" in name:
			var = name.replace("_array", "")
			raise TypeError(f"Array {var} is not defined in the context")
		else:
			raise TypeError(f"Variable {name} is not defined in the context")

	def set_type(self, name, value):
		scope = self.stack[0]
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
					return True
				elif (scope[name][0] != assinatura[0]) and ((scope[name][1] != assinatura[1]) or (len(scope[name][2]) != len(assinatura[2]))):
					return True
				elif (types1 != types2) or (names1 != names2):
					return True
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
				if assinatura[0] == "Definition":
					raise TypeError(f"Function {assinatura[0]} '{names}' is already defined in the context")
				else:
					raise TypeError(f"Function {assinatura[0]} '{names}' is already declared in the context")

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
		var = name + "_array"
		if ctx.has_var_in_current_scope(name) or ctx.has_var_in_current_scope(var):
			raise TypeError(f"Array '{name}' is already defined in the context")
		
		ctx.set_type(var, var_type)

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

		for arg in node["arguments"]:
			ctx.set_type(arg["name"], arg["type"])

		ctx.enter_scope()
		for statments in node["block"]:
			if statments != None:
				check_semantic(ctx, statments)
		ctx.exit_scope()
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

	elif node["nt"] == "Array":
		name = node["name"]
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
		value = node["r_parameters"].get("value")
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

	elif node["nt"] == "Else":
		ctx.enter_scope()
		if node["block"] != None:
			for statment in node["block"]:
				check_semantic(ctx, statment)
		ctx.exit_scope()

try:
	if len(sys.argv) < 2:
		print("No file was given as a first argument!")
		print("Use command -> 'bash run.sh 'filename''")
	else:
		file = open(sys.argv[1])
		code = file.read()
		ast = parser.parse(code)
		if ast != None:
			check_semantic(Context(), ast)
except EOFError:
    print("File could not be opened!")