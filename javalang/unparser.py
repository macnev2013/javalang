import six

from .ast import Node
from . import util
from . import tree

def _get_prefix_str(prefix_operators):
    if prefix_operators is None:
        return ''
    else:
        return ''.join(prefix_operators)

def _get_postfix_str(postfix_operators):
    if postfix_operators is None:
        return ''
    else:
        return ''.join(postfix_operators)

def _get_selector_str(selectors):
    if selectors is None or len(selectors) == 0:
        return ""
    else:
        return "." + ".".join(unparse(e) for e in selectors)

def unparse(node, indent=0, indent_size=4):
    indent_str = ' ' * indent_size * indent
    if isinstance(node, tree.CompilationUnit):
        package_str = indent_str + "package %s;" % node.package.name if node.package else ""
        imports_str = "\n".join(indent_str + unparse(imp, indent=indent) for imp in node.imports)
        types_str = "\n".join(unparse(typ, indent=indent) for typ in node.types)
        return "%s\n\n%s\n\n%s" % (package_str, imports_str, types_str)
    elif isinstance(node, tree.Import):
        if node.static:
            import_prefix = "import static "
        else:
            import_prefix = "import "
        import_prefix = indent_str + import_prefix
        if node.wildcard:
            return import_prefix + node.path + ".*;"
        else:
            return import_prefix + node.path + ";"
    elif isinstance(node, tree.PackageDeclaration):
        return indent_str + "package %s;" % node.name
    elif isinstance(node, tree.ClassDeclaration):
        annotations = indent_str + " ".join(unparse(a) for a in node.annotations)
        modifiers = indent_str + " ".join(sorted(node.modifiers))
        name = node.name
        extends = " extends " + unparse(node.extends) if node.extends else ""
        implements = " implements " + ", ".join(map(unparse, node.implements)) if node.implements else ""
        body = [unparse(m, indent=indent+1) for m in node.body]
        return "%s\n%s class %s%s%s {\n" % (annotations, modifiers, name, extends, implements) + \
            "\n".join(body) + "\n" + indent_str + "}"
    elif isinstance(node, tree.EnumDeclaration):
        annotations = indent_str + " ".join(unparse(a) for a in node.annotations)
        modifiers = indent_str + " ".join(sorted(node.modifiers))
        name = node.name
        implements = " implements " + ", ".join(map(unparse, node.implements)) if node.implements else ""
        body = unparse(node.body, indent=indent+1)
        return "%s\n%s enum %s%s {\n%s\n%s}" % (annotations, modifiers, name, implements, body, indent_str)
    elif isinstance(node, tree.InterfaceDeclaration):
        annotations = indent_str + " ".join(unparse(a) for a in node.annotations)
        modifiers = indent_str + " ".join(sorted(node.modifiers))
        name = node.name
        extends = " extends " + ", ".join(map(unparse, node.extends)) if node.extends else ""
        body = [unparse(m, indent=indent+1) for m in node.body]
        return "%s\n%s interface %s%s {\n" % (annotations, modifiers, name, extends) + \
            "\n".join(body) + "\n" + indent_str + "}"

    elif isinstance(node, tree.BasicType):
        if node.dimensions is not None:
            return node.name + "".join("[]" for _ in range(len(node.dimensions)))
        else:
            return node.name
    elif isinstance(node, tree.ReferenceType):
        if node.sub_type is not None:
            subtype_str = '.' + unparse(node.sub_type)
        else:
            subtype_str = ''
        name_str = node.name + subtype_str
        if node.dimensions is None:
            return name_str
        else:
            return name_str + "".join("[]" for _ in range(len(node.dimensions)))

    elif isinstance(node, tree.Annotation):
        if isinstance(node.element, list):
            return "@%s(%s)" % (node.name, ", ".join(unparse(arg) for arg in node.element))
        elif isinstance(node.element, Node):
            return "@%s(%s)" % (node.name, unparse(node.element))
        elif node.element is None:
            return "@%s" % node.name
    elif isinstance(node, tree.ElementValuePair):
        return "%s = %s" % (node.name, unparse(node.value))

    elif isinstance(node, tree.MethodDeclaration):
        if node.annotations is not None:
            annotations = indent_str + " ".join(unparse(a) for a in node.annotations)
        else:
            annotations = ""
        modifiers = indent_str + " ".join(sorted(node.modifiers))
        return_type = unparse(node.return_type) if node.return_type is not None else "void"
        method_name = node.name
        params = ", ".join(unparse(p) for p in node.parameters)
        throws = " throws " + ", ".join(t for t in node.throws) if node.throws is not None else ""
        if node.body is not None:
            body = "\n".join(unparse(s, indent=indent+1) for s in node.body)
        else:
            body = ";"
        body = "{\n%s\n%s}" % (body, indent_str) if body != ";" else ";"
        return "%s\n%s %s %s(%s)%s %s" % (annotations, modifiers, return_type, method_name, params, throws, body)
    elif isinstance(node, tree.FieldDeclaration):
        modifiers = indent_str + " ".join(sorted(node.modifiers))
        all_dec_str = modifiers + " " + unparse(node.type) + " "
        for var in node.declarators:
            dec_str = unparse(var)
            all_dec_str += dec_str + ', '
        all_dec_str = all_dec_str[:-2] + ';'
        return all_dec_str
    elif isinstance(node, tree.ConstructorDeclaration):
        annotations = indent_str + " ".join(unparse(a) for a in node.annotations)
        modifiers = indent_str + " ".join(sorted(node.modifiers))
        name = node.name
        params = ", ".join(unparse(p) for p in node.parameters)
        throws = " throws " + ", ".join(t for t in node.throws) if node.throws is not None else ""
        body = "\n".join(unparse(s, indent=indent+1) for s in node.body)
        return "%s\n%s %s(%s)%s {\n%s\n%s}" % (annotations, modifiers, name, params, throws, body, indent_str)

    elif isinstance(node, tree.ArrayInitializer):
        return "{%s}" % ", ".join(unparse(e) for e in node.initializers)
    elif isinstance(node, tree.VariableDeclaration) and not isinstance(node, tree.LocalVariableDeclaration):
        all_dec_str = indent_str + unparse(node.type) + " " 
        for var in node.declarators:
            dec_str = unparse(var)
            all_dec_str += dec_str + ', '
        all_dec_str = all_dec_str[:-2] + ';'
        return all_dec_str
    elif isinstance(node, tree.LocalVariableDeclaration):
        if node.modifiers is not None and len(node.modifiers) > 0:
            modifier_str = " ".join(sorted(node.modifiers)) + " "
        else:
            modifier_str = ""
        all_dec_str = indent_str + modifier_str + unparse(node.type) + " " 
        for var in node.declarators:
            dec_str = unparse(var)
            all_dec_str += dec_str + ', '
        all_dec_str = all_dec_str[:-2] + ';\n'
        return all_dec_str
    elif isinstance(node, tree.VariableDeclarator):
        if node.initializer is not None:
            return "%s = %s" % (node.name, unparse(node.initializer))
        else:
            return node.name
    elif isinstance(node, tree.FormalParameter):
        modifier_str = " ".join(sorted(node.modifiers)) + " " if node.modifiers else ""
        return modifier_str + unparse(node.type) + " " + node.name

    elif isinstance(node, tree.IfStatement):
        condition = unparse(node.condition)
        then_statement = unparse(node.then_statement, indent=indent)
        else_statement = unparse(node.else_statement, indent=indent) if node.else_statement is not None else ""
        if len(else_statement) > 0:
            return "%sif (%s) %s else %s" % (indent_str, condition, then_statement, else_statement)
        else:
            return "%sif (%s) %s" % (indent_str, condition, then_statement)
    elif isinstance(node, tree.WhileStatement):
        condition = unparse(node.condition)
        statement = unparse(node.body, indent=indent)
        return "%swhile (%s) %s" % (indent_str, condition, statement)
    elif isinstance(node, tree.DoStatement):
        condition = unparse(node.condition)
        statement = unparse(node.body, indent=indent)
        return "%sdo %s while (%s);" % (indent_str, statement, condition)
    elif isinstance(node, tree.ForStatement):
        forcontrol = unparse(node.control)
        statement = unparse(node.body, indent=indent)
        return "%sfor (%s) %s" % (indent_str, forcontrol, statement)
    elif isinstance(node, tree.AssertStatement):
        return indent_str + "assert(%s);" % unparse(node.condition)
    elif isinstance(node, tree.BreakStatement):
        return indent_str + "break;" # ignoring gotos for now
    elif isinstance(node, tree.ContinueStatement):
        return indent_str + "continue;"
    elif isinstance(node, tree.ReturnStatement):
        return indent_str + "return %s;" % unparse(node.expression) if node.expression is not None else "return;"
    elif isinstance(node, tree.ThrowStatement):
        return indent_str + "throw %s;" % unparse(node.expression)
    elif isinstance(node, tree.SynchronizedStatement):
        block_content = '{\n' + '\n'.join(unparse(s, indent=indent+1) for s in node.block) + '\n' + indent_str + '}'
        return indent_str + "synchronized (%s) %s" % (unparse(node.lock), block_content)
    elif isinstance(node, tree.TryStatement):
        block_stmts = [unparse(stmt, indent=indent+1) for stmt in node.block]
        if node.catches is not None:
            catch_clauses = [unparse(catch, indent=indent) for catch in node.catches]
        else:
            catch_clauses = []
        if node.finally_block is None:
            return "%stry {\n%s\n} %s" % (indent_str, "\n".join(block_stmts), " ".join(catch_clauses))
        else:
            finally_stmts = [unparse(stmt, indent=indent+1) for stmt in node.finally_block]
            return "%stry {\n%s\n} %s finally {%s}" % (indent_str, "\n".join(block_stmts), " ".join(catch_clauses), "\n".join(finally_stmts))
    elif isinstance(node, tree.SwitchStatement):
        expression_str = unparse(node.expression)
        switch_block_str = '\n'.join(unparse(stmt, indent=indent+1) for stmt in node.cases)
        return "%sswitch (%s) {\n%s\n%s}" % (indent_str, expression_str, switch_block_str, indent_str)
    elif isinstance(node, tree.BlockStatement):
        return '{\n%s\n%s}' % ("\n".join(unparse(stmt, indent=indent+1) for stmt in node.statements), indent_str)
    elif isinstance(node, tree.StatementExpression):
        return indent_str + unparse(node.expression) + ";"
    
    elif isinstance(node, tree.CatchClause):
        block_stmts = [unparse(stmt, indent=indent+1) for stmt in node.block]
        return "catch (%s) {\n%s\n%s}" % (unparse(node.parameter), "\n".join(block_stmts), indent_str)
    elif isinstance(node, tree.CatchClauseParameter):
        type_collation = " | ".join(node.types)
        return "%s %s" % (type_collation, node.name)

    elif isinstance(node, tree.SwitchStatementCase):
        indiv_cases = [unparse(case) if isinstance(case, Node) else case for case in node.case]
        if len(indiv_cases) > 0:
            cases_str = '\n'.join([indent_str + ("case %s:" % c if c is not None else "default:")
                                   for c in indiv_cases])
        else:
            cases_str = indent_str + "default:"
        statements_str = "\n".join(unparse(stmt, indent=indent+1) for stmt in node.statements)
        return "%s\n%s" % (cases_str, statements_str)
    elif isinstance(node, tree.ForControl):
        if node.init is not None:
            if type(node.init) == list:
                init = ", ".join(unparse(init) for init in node.init) + ";"
            else:
                init = unparse(node.init)
        else:
            init = ""
        if node.condition is not None:
            cond = unparse(node.condition)
        else:
            cond = ""
        if node.update is not None:
            update = ", ".join(unparse(u) for u in node.update)
        else:
            update = ""
        return "%s %s; %s" % (init, cond, update)
    elif isinstance(node, tree.EnhancedForControl):
        var_dec_without_semicolon = unparse(node.var)[:-1]
        return "%s : %s" % (var_dec_without_semicolon, unparse(node.iterable))

    elif isinstance(node, tree.Assignment):
        return "%s %s %s" % (unparse(node.expressionl), node.type, unparse(node.value))
    elif isinstance(node, tree.TernaryExpression):
        return "%s ? %s : %s" % (unparse(node.condition), unparse(node.if_true), unparse(node.if_false))
    elif isinstance(node, tree.BinaryOperation):
        if hasattr(node, 'prefix_operators'): # prefixes in binary operations aren't documented but exist
            prefix_str = _get_prefix_str(node.prefix_operators)
            return "%s(%s %s %s)" % (prefix_str, unparse(node.operandl), node.operator, unparse(node.operandr))
        else:
            return "%s %s %s" % (unparse(node.operandl), node.operator, unparse(node.operandr))
    elif isinstance(node, tree.Cast):
        if hasattr(node, 'prefix_operators'): # prefixes in Cast operators are something I made up...
            prefix_str = _get_prefix_str(node.prefix_operators)
        else:
            prefix_str = ""
        if hasattr(node, 'selectors'): # casts can have selectors
            selector_str = _get_selector_str(node.selectors)
        else:
            selector_str = ""
        if len(prefix_str) > 0 or len(selector_str) > 0:
            return "%s((%s) %s)%s" % (prefix_str, unparse(node.type), unparse(node.expression), selector_str)
        else:
            return "(%s) %s" % (unparse(node.type), unparse(node.expression))

    elif isinstance(node, tree.Literal):
        prefix_str = _get_prefix_str(node.prefix_operators)
        postfix_str = _get_postfix_str(node.postfix_operators)
        selector_str = _get_selector_str(node.selectors)
        return prefix_str + node.value + selector_str + postfix_str
    elif isinstance(node, tree.This):
        prefix_str = _get_prefix_str(node.prefix_operators)
        postfix_str = _get_postfix_str(node.postfix_operators)
        if node.qualifier is None:
            qualifier_str = ""
        else:
            qualifier_str = node.qualifier + "."
        selector_str = _get_selector_str(node.selectors)
        return prefix_str + qualifier_str + "this" + selector_str + postfix_str
    elif isinstance(node, tree.MemberReference):
        if node.qualifier is not None:
            core_name = node.member if len(node.qualifier) == 0 else node.qualifier + "." + node.member
        else:
            core_name = node.member
        prefix_str = _get_prefix_str(node.prefix_operators)
        postfix_str = _get_postfix_str(node.postfix_operators)
        selector_str = "" if node.selectors is None else "".join(unparse(e) for e in node.selectors) # array result selectors
        return prefix_str + core_name + postfix_str + selector_str
    elif isinstance(node, tree.ExplicitConstructorInvocation):
        return "this(%s)" % (", ".join(unparse(e) for e in node.arguments))
    elif isinstance(node, tree.SuperConstructorInvocation):
        return "super(%s)" % (", ".join(unparse(e) for e in node.arguments))
    elif isinstance(node, tree.MethodInvocation):
        prefix_str = _get_prefix_str(node.prefix_operators)
        mname = node.member if node.qualifier is None or len(node.qualifier) == 0 else node.qualifier + "." + node.member
        args = ", ".join(unparse(arg) for arg in node.arguments)
        selector_str = _get_selector_str(node.selectors)
        return prefix_str + mname + "(" + args + ")" + selector_str
    elif isinstance(node, tree.SuperMethodInvocation):
        prefix_str = _get_prefix_str(node.prefix_operators)
        args = ", ".join(unparse(arg) for arg in node.arguments)
        selector_str = _get_selector_str(node.selectors)
        return prefix_str + "super." + node.member + "(" + args + ")" + selector_str
    elif isinstance(node, tree.ArraySelector):
        return "[%s]" % unparse(node.index)
    elif isinstance(node, tree.ClassReference):
        prefix_str = _get_prefix_str(node.prefix_operators)
        selector_str = _get_selector_str(node.selectors)
        return "%s%s.class%s" % (prefix_str, unparse(node.type), selector_str)

    elif isinstance(node, tree.ArrayCreator):
        dim_str = ''.join([f'[{unparse(e)}]' if e is not None else '[]' for e in node.dimensions])
        init_str = unparse(node.initializer) if node.initializer is not None else ''
        return f'new {unparse(node.type)}{dim_str}{init_str}'
    elif isinstance(node, tree.ClassCreator):
        args = ", ".join(unparse(arg) for arg in node.arguments)
        assert node.selectors is None or len(node.selectors) <= 1 # unsure what is happening here
        if node.selectors is None or len(node.selectors) == 0:
            selector_str = ""
        else:
            selector_str = "." + unparse(node.selectors[0])
        if node.body is not None:
            body_str = '\n'.join(unparse(e, indent=indent+1) for e in node.body)
            body_str = ' {\n' + body_str + '\n' + indent_str + '}'
        else:
            body_str = ""
        return "new %s(%s)%s%s" % (unparse(node.type), args, selector_str, body_str)
    elif isinstance(node, tree.InnerClassCreator):
        args = ", ".join(unparse(arg) for arg in node.arguments)
        return "new %s(%s)" % (unparse(node.type), args)
    
    elif isinstance(node, tree.EnumBody):
        constants_str = ",\n".join(indent_str + unparse(c) for c in node.constants)
        declarations_str = "\n".join(unparse(d, indent=indent) for d in node.declarations)
        return constants_str + "\n" + declarations_str
    elif isinstance(node, tree.EnumConstantDeclaration):
        assert node.body is None, 'I dunno what this looks like :('
        if node.arguments is None or len(node.arguments) == 0:
            arg_str = ""
        else:
            arg_str = "(%s)" % ", ".join(unparse(a) for a in node.arguments)

        return node.name+arg_str
    
    ## Weird fellows
    elif isinstance(node, tree.Statement):
        # only-semicolon lines?
        return ";"
    elif isinstance(node, list):
        # seems to be a static block? I'm unsure what this is. (found in SegmentedTimelineTests.java of Chart)
        statement_str = "\n".join(unparse(stmt, indent=indent+1) for stmt in node)
        return "%sstatic {\n%s\n%s}" % (indent_str, statement_str, indent_str)
    else:
        raise NotImplementedError("Unparser for %s is not implemented at location %s" % (type(node), node._position))

