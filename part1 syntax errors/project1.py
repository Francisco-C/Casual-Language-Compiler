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
t_RBRACKET		= r'\]'
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

lexer = lex.lex()

precedence = (
	('left','AND','OR'),
	('nonassoc','EQUALS_EQUALS','NOT_EQUALS','GREATER','LESS','GREATER_EQUAL','LESS_EQUAL','NOT_UNARY'),
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE','MOD'),
    ('right','UMINUS'),
    )

names = { }

def p_program(t):
	'''program : declaration program
			   | definition program
			   | declaration
			   | definition'''

def p_declaration(t):
	'''declaration : DECL VARIABLE LPAREN arguments RPAREN type
				   | DECL VARIABLE LPAREN RPAREN type'''

def p_definition(t):
	'''definition : DEF VARIABLE LPAREN arguments RPAREN type block
	              | DEF VARIABLE LPAREN RPAREN type block'''

def p_type(t):
	'''type : COLON TYPE_INT
			| COLON TYPE_FLOAT
			| COLON TYPE_VOID
			| COLON TYPE_STRING
			| COLON TYPE_BOOLEAN'''

def p_empty(t):
	'''empty : '''

def p_arguments(t):
	'''arguments : VARIABLE type
			     | VARIABLE type COMMA arguments'''

def p_arguments_funinvocation(t):
	'''arguments_funinvocation : expression
	                           | expression COMMA arguments_funinvocation'''

def p_statment_repeat(t):
	'''statment_repeat : empty
					   | statment statment_repeat'''

def p_block(t):
	'''block : LBRACE statment_repeat RBRACE'''

def p_statments(t):
	'''statment : return
				| statment_expression
				| if
				| while
				| var_decl
				| var_assign'''

def p_statment_return(t):
	'''return : RETURN SEMICOLON
			  | RETURN expression SEMICOLON'''

def p_statment_expression(t):
	'''statment_expression : expression SEMICOLON'''

def p_statment_if(t):
	'''if : IF expression block else'''

def p_statment_else(t):
	'''else : empty
			| ELSE block'''

def p_statment_while(t):
	'''while : WHILE expression block'''

def p_statment_vardecl(t):
	'''var_decl : VARIABLE type EQUALS expression SEMICOLON'''

def p_statment_varassign(t):
	'''var_assign : VARIABLE EQUALS expression SEMICOLON'''

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

def p_expression_uminus(t):
    '''expression : MINUS expression %prec UMINUS'''

def p_expression_group(t):
    '''expression : LPAREN expression RPAREN'''

def p_expression_float(t):
	'''expression : FLOAT'''

def p_expression_int(t):
	'''expression : INT'''

def p_expression_string(t):
	'''expression : STRING'''

def p_expression_var(t):
	'''expression : VARIABLE'''

def p_expression_boolean(t):
	'''expression : TRUE
				  | FALSE'''

def p_expression_notunary(t):
	'''expression : NOT_UNARY expression'''

def p_expression_index(t):
	'''expression : VARIABLE LBRACKET expression RBRACKET
				  | GETARRAY LBRACKET expression RBRACKET'''

def p_expression_funinvocation(t):
	'''expression : VARIABLE LPAREN arguments_funinvocation RPAREN
	              | VARIABLE LPAREN RPAREN'''

def find_column(input, t):
	line_start = input.rfind('\n', 0, t.lexpos) + 1
	return (t.lexpos - line_start) + 1

def p_error(t):
	if t is not None:
		column = find_column(code, t)		
		print("Found unexpected character '%s' at line '%s' and column '%s'" % (t.value, t.lineno, column))
	else:
		print("Unexpected end of input!Empty file or syntax error at EOF!")

import ply.yacc as yacc

parser = yacc.yacc()

try:
	if len(sys.argv) < 2:
		print("No file was given as a first argument!")
		print("Use command -> 'bash run.sh 'filename''")
	else:
		file = open(sys.argv[1])
		code = file.read()
		p = parser.parse(code)
except EOFError:
    print("File could not be opened!")