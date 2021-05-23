__author__ = "Francisco Caldeira, Faculdade de Ciências da Universidade de Lisboa"

import sys
import cas_semantics as s
import cas_compiler as c
import ply.lex as lex
import ply.yacc as yacc
from collections.abc import Iterable
import subprocess

#sys.tracebacklimit = 0

tokens = ('VARIABLE', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'LPAREN', 'RPAREN', 'EQUALS', 'NOT_EQUALS', 'EQUALS_EQUALS', 'AND', 'OR', 
		  'SEMICOLON', 'COLON', 'COMMA', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET','GREATER', 'LESS', 'GREATER_EQUAL', 'LESS_EQUAL',
		  'NOT_UNARY', 'TRUE', 'FALSE', 'WHILE', 'IF', 'ELSE', 'DECL', 'DEF', 'RETURN', 'INT', 'FLOAT', 'STRING', 'TYPE_INT', 'TYPE_FLOAT',
		  'TYPE_VOID', 'TYPE_STRING', 'TYPE_BOOLEAN', 'GETARRAY', 'CREATEARRAY', 'PRINT', 'USING', 'LAMBDA')

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
t_STRING		= r'"(([a-zA-Z% \\]*)|[a-zA-Z% \\]+([\\][a-zA-Z% \\]+)+)"'
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

def t_PRINT(t):
	r'print'
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
	r'array_get'
	return t

def t_CREATEARRAY(t):
	r'array_create'
	return t

def t_USING(t):
	r'using'
	return t

def t_LAMBDA(t):
	r'lambda'
	return t

t_ignore = " \t"
t_ignore_COMMENT = r'\#.*'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

precedence = (
	('left','AND','OR'),
	('nonassoc','EQUALS_EQUALS','NOT_EQUALS'),
	('nonassoc','GREATER','LESS','GREATER_EQUAL','LESS_EQUAL','NOT_UNARY'),
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE','MOD'),
    ('right','UMINUS'),)

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

def p_using(t):
	'''using : USING PRINT SEMICOLON using
		     | USING GETARRAY SEMICOLON using
		     | USING CREATEARRAY SEMICOLON using
		     | empty'''
	if len(t) != 5:
		t[0] = [{'nt': 'Using', 'name': 'void'}]
	else:
		t[0] = [{'nt': 'Using', 'name': t[2]}, t[4]]

def p_program(t):
	'''program : using program_helper'''
	t[0] = {'nt': 'Program', 'Using': list(list_helper(t[1])),'Decls_Defs': list(list_helper(t[2]))}

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
				    | if_else
				    | while
				    | var_decl
				    | var_assign
				    | array_decl
				    | array_assign
				    | print'''
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
				| if_else
				| while
				| var_decl
				| var_assign
				| array_decl
				| array_assign
				| print'''
	t[0] = t[1]

def p_print_helper(t):
	'''print_helper : COMMA expression
	                | COMMA expression print_helper'''
	if len(t) == 3:
		t[0] = [t[2]]
	else:
		t[0] = [t[2], t[3]]

def p_statment_print(t):
	'''print : PRINT LPAREN STRING print_helper RPAREN SEMICOLON
	         | PRINT LPAREN STRING empty RPAREN SEMICOLON'''
	if t[4] != None:
		t[0] = {'nt': 'Print', 'print_str': t[3], 'print_args': list(list_helper(t[4]))}
	else:
		t[0] = {'nt': 'Print', 'print_str': t[3], 'print_args': [{'nt': 'Void', 'value': 'Void'}]}

def p_statment_return(t):
	'''return : RETURN empty_args SEMICOLON
			  | RETURN expression SEMICOLON
			  | RETURN lambda_expression SEMICOLON'''
	if len(t) == 3:
		t[0] = {'nt': 'Return', 'r_parameters': None}
	else:
		t[0] = {'nt': 'Return', 'r_parameters': t[2]}

def p_statment_expression(t):
	'''statment_expression : expression SEMICOLON'''
	t[0] = t[1]

def p_statment_if(t):
	'''if : IF expression block'''
	t[0] = {'nt': 'If', 'condition': t[2], 'block': t[3]}

def p_statment_if_else(t):
	'''if_else : IF expression block ELSE block'''
	t[0] = {'nt': 'If_Else', 'condition': t[2], 'if_block': t[3], 'else_block': t[5]}

def p_statment_while(t):
	'''while : WHILE expression block'''
	t[0] = {'nt': 'While', 'condition': t[2], 'block': t[3]}

def p_statment_vardecl(t):
	'''var_decl : VARIABLE type EQUALS expression SEMICOLON
				| VARIABLE type EQUALS lambda_expression SEMICOLON'''
	t[0] = {'nt': 'Var_declaration', 'name': t[1], 'type': t[2], 'expr': t[4]}

def p_create_array(t):
	'''create_array : CREATEARRAY LPAREN expression RPAREN'''
	t[0] = {'nt': 'create_array', 'array_size': t[3]}

def p_statment_arraydecl(t):
	'''array_decl : VARIABLE type LBRACKET expression RBRACKET SEMICOLON
	              | VARIABLE type EQUALS create_array SEMICOLON'''
	t[0] = {'nt': 'Array_declaration', 'name': t[1], 'type': t[2], 'size': t[4]}

def p_statment_varassign(t):
	'''var_assign : VARIABLE EQUALS expression SEMICOLON
				  | VARIABLE EQUALS lambda_expression SEMICOLON'''
	t[0] = {'nt': 'Var_assignment', 'name': t[1], 'expr': t[3]}

def p_statment_arrayassign(t):
	'''array_assign : VARIABLE LBRACKET expression RBRACKET EQUALS expression SEMICOLON'''
	t[0] = {'nt': 'Array_assignment', 'name': t[1], 'index_type': t[3], 'expr': t[6]}

def p_lambda_arguments(t):
	'''lambda_args : VARIABLE type
	               | VARIABLE type COMMA lambda_args'''
	if len(t) == 3:
		t[0] = [{'nt': 'arg', 'name': t[1], 'type': t[2]}]
	else:
		t[0] = [{'nt': 'arg', 'name': t[1], 'type': t[2]}, t[4]]

def p_expression_lambda(t):
	'''lambda_expression : LAMBDA lambda_args COLON expression
						 | LAMBDA empty COLON expression'''
	if t[2] is None:
		t[0] = {'nt': 'Lambda', 'arguments': [{'nt': 'Void', 'name': 'Void', 'type': 'Void'}], 'expression': t[4]}
	else:
		t[0] = {'nt': 'Lambda', 'arguments': list(list_helper(t[2])), 'expression': t[4]}

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
    '''expression : LPAREN expression RPAREN
    			  | LPAREN lambda_expression RPAREN'''
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

def p_get_array(t):
	'''get_array : GETARRAY LPAREN VARIABLE RPAREN'''
	t[0] = {'nt': 'get_array', 'name': t[3]}

def p_expression_index(t):
	'''expression : VARIABLE LBRACKET expression RBRACKET
				  | get_array LBRACKET expression RBRACKET'''
	if len(t) == 5:
		t[0] = {'nt': 'Array', 'name': t[1], 'index_type': t[3]}
	else:
		t[0] = {'nt': 'Array', 'name': t[1], 'index_type': t[3]}

def p_expression_funinvocation(t):
	'''expression : VARIABLE LPAREN arguments_funinvocation RPAREN'''
	t[0] = {'nt': 'fun_call', 'name': t[1], 'arguments': t[3]}

def p_expression_double_funinvocation(t):
	'''expression : VARIABLE LPAREN arguments_funinvocation RPAREN LPAREN arguments_funinvocation RPAREN'''
	t[0] = {'nt': 'double_fun_call', 'name': t[1], 'arguments1': t[3], 'arguments2': t[6]}              

def find_column(input, t):
	line_start = input.rfind('\n', 0, t.lexpos) + 1
	return (t.lexpos - line_start) + 1

def p_error(t):
	if t is not None:
		column = find_column(code, t)		
		print("Found unexpected character '%s' at line '%s' and column '%s'" % (t.value, t.lineno, column))
		exit()
	else:
		print("Unexpected end of input!Empty file or syntax error at EOF!")

def list_helper(lis):
	for item in lis:
		if isinstance(item, Iterable) and not isinstance(item, dict):
			for x in list_helper(item):
				yield x
		else:        
			yield item

lexer = lex.lex()

parser = yacc.yacc()


try:
	if len(sys.argv) < 2:
		print("No file was given as a first argument!")
		print("Use command -> 'bash run.sh 'filename''")
	else:
		file = open(sys.argv[1])
		code = file.read()
		ast = parser.parse(code)
		if ast != None:
			s.check_semantic(s.Context(), ast)

			name = sys.argv[1].split(".cas")

			llvm_code = c.compiler(ast)
			print(llvm_code)
			with open(f"{name[0]}.ll", "w") as f:
				f.write(llvm_code)

			r = subprocess.call(f"/lib/llvm-10/bin/llc {name[0]}.ll && clang {name[0]}.s -o {name[0]} && ./{name[0]}",shell=True,)
			#print(r)

except EOFError:
    print("File could not be opened!")
