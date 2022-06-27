'''
Evaluate members of self via format specifier in templates:

    {something:any_attr}
    {something:any_method(params)}

where `params` is any positional and keyword arguments.

Anything after colon is evaluated as a pythonic expression.
Expressions are restricted, they should be attribute names or method calls.
Names should not start with underscore.
No function calls are allowed in params.

If params include a substitution, it should be repr-convered:

    {something:my_method('foo', {some_substitution!r}, 'bar')}

:copyright: Copyright 2019-2021 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import ast

class Invoke:
    '''
    Support invocation of methods using format specifier.
    '''
    def __format__(self, format_spec):
        '''
        Invoke method of `self`, passed as `format_spec`.
        '''
        expression = format_spec
        tree = ast.parse(expression, mode='eval')
        _validate_ast(tree, expression)
        name = _get_root_name(tree)
        if name.startswith('_'):
            raise Exception(f'Denied access to {name}')
        code = compile(tree, filename='clabate', mode='eval')
        context = {name: getattr(self, name)}  # populate locals and globals with single value
        return eval(code, context, context)

def _get_root_name(tree):
    '''
    Get the name of attribute or method involved in expression.
    '''
    if isinstance(tree.body, ast.Name):
        return tree.body.id
    else:
        return tree.body.func.id

def _validate_ast(tree, expression):
    '''
    Validate AST.
    '''
    if not isinstance(tree, ast.Expression):
        raise Exception(f'Not an expression: {expression}')

    if not isinstance(tree.body, (ast.Name, ast.Call)):
        raise Exception(f'Invalid expression: {expression}')

    def _check_children(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Call):
                raise Exception(f'Calls are not allowed in parameters: {expression}')
            _check_children(child)

    _check_children(tree.body)
