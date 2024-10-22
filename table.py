import sys
import re
from itertools import product

def check_valid_recursively(expr, declared_vars, declared_ids):
    """
    
    Check the validity of an expression by iteratively check sub-expressions.
    
    """
    def check_valid(expr, declared_vars, declared_ids):

        i = 0
        running = -1   # -1:begin expr, 0: var, 1: and/or, 2: not
        clause = None    # not and or
        while i < len(expr):
            token = expr[i]
            # OPEN parens --> look for matching closing parens
            if token == '(':
                if running == 0:
                    raise Exception(f'Invalid assignment {expr}')
                open_parens = 1
                for j in range(i + 1, len(expr)):
                    if expr[j] == '(':
                        open_parens += 1
                    elif expr[j] == ')':
                        open_parens -= 1
                    if open_parens == 0:
                        # Solve the sub-expr within the parentheses
                        if expr[i + 1:j] == []:
                            raise Exception(f'Empty parentheses at position {i} in <{expr}>')
                        check_valid(expr[i + 1:j], declared_vars, declared_ids)
                        running = 0 # subexpr as if it were a variable
                        i = j  # Move the index to the closing ')'
                        break
                if open_parens > 0:
                    raise Exception(f'Unbalanced parentheses in <{expr}>')
            
            # CLOSING parens
            elif token == ')':
                raise Exception(f'Unmatched closing parenthesis at position {i} in <{expr}>')
            
            # IDENTIFIER / VARIABLE
            elif (expr[i] in declared_vars) or (expr[i] in declared_ids) or (expr[i] in ('True', 'False')):
                if running == 0:
                    raise Exception(f'Invalid syntax at position {i} in <{expr}>')
                running = 0
            
            # NOT
            elif token == 'not':
                if running != -1:
                    raise Exception(f'Invalid syntax at position {i} in <{expr}>')
                if (clause is not None) and (clause != token):
                    raise Exception(f'Conflicts of operators in <{expr}>') 
                clause = token
                running = 2
            
            # AND / OR
            elif token in ('and', 'or'):
                if running != 0:
                    raise Exception(f'Invalid syntax at position {i} in <{expr}>')
                if (clause is not None) and (clause != token):
                    raise Exception(f'Conflicts of operators in <{expr}>')
                clause = token
                running = 1 
            
            else:
                raise Exception(f'Invalid token {token} at position {i} in <{expr}>')
                
            i += 1
        if running > 0:
            raise Exception(f'Invalid assignment {expr}')
        
        return 
    
    return check_valid(expr, declared_vars, declared_ids)

class Node:
    def __init__(self,
                 value=None,
                 children=None):
        self.value = value
        self.children = children if children else []
        self._depth = None
    
    def eval(self, variables):

        if self.value == 'and':
            if len(self.children) < 2:
                raise Exception(f'Invalid number of children in {self}')
            for child in self.children:
                if not child.eval(variables):
                    return False
            return True
        
        elif self.value == 'or':
            if len(self.children) < 2:
                raise Exception(f'Invalid number of children in {self}')
            for child in self.children:
                if child.eval(variables):
                    return True
            return False
        
        elif self.value == 'not':
            if len(self.children) < 1:
                raise Exception(f'Invalid number of children in {self}')
            return not self.children[0].eval(variables)
        
        elif self.value == 'True':
            return True
        
        elif self.value == 'False':
            return False
        
        else:
            return variables[self.value]

    def __repr__(self) -> str:
        return f'<Node> \'{self.value}\' with {len(self.children)} children'

    def depth(self):
        if self._depth is None:
            self._depth = 0 if self.children == [] else 1 + min(self.children, key=lambda x: x.depth()).depth() 
        return self._depth

def build_tree_recursively(expr):
    
    def build_tree(expr):

        children = []
        node_type = None
        i = 0
        while i < len(expr):
            token = expr[i]
            
            if token == '(':
                # Find the matching closing parenthesis
                open_parens = 1
                for j in range(i + 1, len(expr)):
                    if expr[j] == '(':
                        open_parens += 1
                    elif expr[j] == ')':
                        open_parens -= 1
                    if open_parens == 0:
                        # Solve the sub-expr within the parentheses
                        if expr[i + 1:j] == []:
                            raise Exception(f'Empty parentheses at position {i} in <{expr}>')
                        node = build_tree(expr[i + 1:j])
                        children.append(node)
                        i = j  # Move the index to after the closing ')'
                        break
            elif token == ')':
                raise Exception(f'Unmatched closing parenthesis at position {i} in <{expr}>')
            
            elif token in ('not', 'and', 'or'):
                if (node_type is not None) and (node_type != token):
                    raise Exception(f'Conflicts of operators in <{expr}>') 
                node_type = token if node_type is None else node_type
            else:
                children.append(Node(token))
            i += 1
        
        children = sorted(children, key=lambda x: x.depth())
        if node_type is not None:
            node = Node(node_type, children)
        else:
            node = children[0]
        
        return node
    
    tree = build_tree(expr)
    return tree

class Compiler():
    
    def __init__(self,
                 )->None:    
        
        self.vars = []      # variables declared so far
        self.ids = {}       # identifiers and their boolean expressions assigned so far

        return

    def _tokenize(self,
                 s: str=None,
                 verbose: bool=False
                 )->str:
        '''
        
        Tokenize input.txt converted to string according to tokenization rules.
            
        s:
            <str>:
                the string of raw text to be tokenized
        verbose:
            <bool>:
                whether to print the final tokens.

        Returns a list of tokens, i.e., a <list> of <str>

        '''
        # 1.    Anything on a line after the character “#” is ignored.
        s = re.sub(pattern = r"#.*\n",
                   repl = "",
                   string=s
                   )
        tokens = []
        word = ''
        for char in s:

            # WORDS -- > starts with a letter or an underscore (no digits)
            if re.match(r'[A-Za-z_]', char) and not word:   
                word += char
            elif re.match(r'[0-9]', char) and not word:
                raise Exception('Invalid word starting with a digit')
            
            # WORDS --> any sequence of (one or more) consecutive letters, digits, or underscores
            elif re.match(r'[A-Za-z_0-9]', char) and word:
                word += char
            
            # BLANKS --> spaces, tabs, carriage, newlines mark the end of a word or are ingored
            elif re.match(r'[ \t\n\r]', char):   # [\s] == [\t\n\r' ']
                if word:  
                    tokens.append(word)
                    word = ''
            
            # SPECIAL chars
            elif re.match(r'[()=;]', char):
                if word:    # special char ends a word
                    tokens.append(word)
                    word = ''
                tokens.append(char)
            
            # Anything else
            else:
                raise Exception(f'Invalid character: {char}')
        

        if verbose:
            print(f'Tokenized Input:\n\n{tokens}\n\n')
        return tokens
    
    def _split_instructions(self,
                            tokens: list=None,
                            verbose: bool=None
                            )->list:
        """
        
        Returns the tokens grouped by instructions.
        
        tokens:
            <list>:
                a list of valid tokens.
        
        Returns a list of instructions, each being a list of tokens.
        
        """
        
        if verbose:
            print('Splitting instructions...')

        # SPLIT the tokens into instructions delimited by ';'
        instructions = []
        buffer = []
        for t in tokens:
            if t == ';':
                instructions.append(buffer)
                buffer = []
            else:
                buffer.append(t)
        
        return instructions
    
    def _check_instructions(self,
                            instructions: list=None,
                            verbose: bool=False
                            )->list:
        """
        
        Checks the validity of a list of instructions.
        
        """

        declared_vars = []
        declared_ids = []
        for instr in instructions:
            
            if verbose:
                print(instr)
            
            # Instruction too short
            if len(instr) < 2:
                raise Exception(f'Invalid instruction: {instr}')
            
            # DECLARATION
            elif instr[0] == 'var':
                for t in instr[1:]:
                    if (t in declared_vars) or (t in declared_ids):
                        raise Exception(f"Variable already declared: {t}")
                    if (t in ('(', ')', 'and', 'or', 'not', 'True', 'False', 'var', 'show', 'show_ones', '=')):
                        raise Exception(f"Invalid variable name: {t}")
                    declared_vars.append(t)
                    if len(declared_vars) > 64:
                        raise Exception(f"Too many variables declared: {declared_vars}")
            
            # ASSIGNMENT
            elif (len(instr) >= 3) and (instr[1] == '='):
                if (instr[0] in declared_vars) or (instr[0] in declared_ids):
                    raise Exception(f" already declared: {instr[0]}")
                check_valid_recursively(instr[2:], declared_vars, declared_ids)
                declared_ids.append(instr[0])
            
            # SHOW
            elif (instr[0] == 'show') or (instr[0] == 'show_ones'):
                for t in instr[1:]:
                    if ((t not in declared_ids) and (t not in declared_vars)) or (t in ('(', ')', 'and', 'or', 'not', 'True', 'False')):
                        raise Exception(f"Unknown identifier: {t}")
            
            else:
                raise Exception(f'Invalid instruction: {instr}')

        return instructions
    
    def _execute_instructions(self,
                              instructions: list=None,
                              verbose: bool=False
                              )->None:
        """
        
        Parses the input according to parsing rules.
        Identifies the instructions and executes them.
        Prints the truth tables when required.

        tokens:
            <list>:
                a list of valid tokens.
        verbose:
            <bool>:
                whether to print intermediate steps.

        """
    
        # Process instructions
        for i in instructions:

            # DECLARATION -> store in self.vars
            if i[0] == 'var':
                if verbose:
                    print(f'Declaration: {i}')
                for t in i[1:]:
                    if t == ';':
                        break
                    self.vars.append(t)
            
            # ASSIGNMENT -> store in self.ids as {'z': ['x', 'and', 'y']}
            elif i[1] == '=':
                # re_evaluate = True  # re-evaluate all ids after an assignment
                if verbose:
                    print(f'Assignment: {i}')
                if (i[0] not in self.vars) and (i[0] not in self.ids):
                    self.ids[i[0]] = build_tree_recursively(i[2:])
                else:
                    raise Exception(f"{i[0]} already exists.")
            

            # SHOW
            elif i[0] == 'show' or i[0] == 'show_ones':
                if verbose:
                    print(f'Show: {i}')
                ids_to_show = i[1:]
                
                self._show(ids_to_show, show_ones= i[0] == 'show_ones')
            
            # INVALID
            else:   
                raise Exception(f"Invalid instruction: {i}")
    
    def _show(self,
              ids_to_show: list=None,
              show_ones: bool=False
              )->None:
        """
        
        Evaluates the truth table for a list of identifiers and prints it.

        ids_to_show:
            <list>:
                a list of identifiers to show in the truth table.
        show_ones:
            <bool>:
                whether to show only rows where at least one identifier takes a value of 1.
        
        """
        
        
        print('#' + ' ' + ' '.join(self.vars) + '   ' + ' '.join(ids_to_show))
        
        vars_value = list(product([False, True], repeat=len(self.vars)))
        n = len(self.vars)   
        i = 0
        while i < 2**n:
            vars = dict(zip(self.vars, vars_value[i]))
            row = ' '
            valid_row = not show_ones
            for v in vars:
                row += ' 1' if vars[v] == True else ' 0'
            row += '  '
            # cache = {}

            # Evaluate the row for all ids
            for id in self.ids.keys():
                vars[id] = self.ids[id].eval(vars)
            
            # Print the ones requested
            for id in ids_to_show:
                row += ' 1' if vars[id] == True else ' 0'
                
                # if at least one id is True, the row is valid
                if vars[id] and (not valid_row):
                    valid_row = True
            
            # After completing the row
            if valid_row:
                print(row)
            i += 1
        return
        
    def compile(self,
                f,
                verbose=False
                )->None:
        """
        
        Compiles the input string f by first tokenizing it and then parsing it.
        Always prints the requested truth tables to the console. If required, prints also intermediate steps.

        f:
            <str>:
                the input string to be compiled.
        verbose:
            <bool>:
                whether to print intermediate steps.
        
        """
        
        if verbose:
            print(f"Input:\n\n{f}\n\n")
        
        tokens = self._tokenize(f,
                                verbose=verbose
                                )
        instructions = self._split_instructions(tokens,
                                                verbose=verbose
                                                )
        instructions = self._check_instructions(instructions,
                                                verbose=verbose
                                                )
        self._execute_instructions(instructions,
                                   verbose=verbose
                                   )


with open(sys.argv[1], 'r') as f:

    compiler = Compiler()    
    f = f.read()
    compiler.compile(f, verbose=False)