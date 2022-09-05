import six

from .ast import Node
from . import util
from . import tree

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
        extends = " extends " + node.extends.name if node.extends else ""
        implements = " implements " + ", ".join(map(unparse, node.implements)) if node.implements else ""
        body = [unparse(m, indent=indent+1) for m in node.body]
        return "%s\n%s class %s%s%s {\n" % (annotations, modifiers, name, extends, implements) + \
            "\n".join(body) + "\n" + indent_str + "}"

    elif isinstance(node, tree.BasicType):
        return node.name + "".join("[]" for _ in range(len(node.dimensions)))
    elif isinstance(node, tree.ReferenceType):
        if node.dimensions is None:
            return node.name
        else:
            return node.name + "".join("[]" for _ in range(len(node.dimensions)))

    elif isinstance(node, tree.Annotation):
        if isinstance(node.element, list):
            return "@%s(%s)" % (node.name, ", ".join(unparse(arg) for arg in node.element))
        elif isinstance(node.element, Node):
            return "@%s(%s)" % (node.name, unparse(node.element))
    elif isinstance(node, tree.ElementValuePair):
        return "%s = %s" % (node.name, unparse(node.value))

    elif isinstance(node, tree.MethodDeclaration):
        annotations = indent_str + " ".join(unparse(a) for a in node.annotations)
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
        all_dec_str = ''
        for var in node.declarators:
            dec_str = unparse(var)
            all_dec_str += modifiers + " " + unparse(node.type) + " " + dec_str + ";"
        return all_dec_str

    elif isinstance(node, tree.VariableDeclaration) and not isinstance(node, tree.LocalVariableDeclaration):
        all_dec_str = ''
        for var in node.declarators:
            dec_str = unparse(var)
            all_dec_str += unparse(node.type) + " " + dec_str + ";"
        return all_dec_str
    elif isinstance(node, tree.LocalVariableDeclaration):
        all_dec_str = ''
        for var in node.declarators:
            dec_str = unparse(var)
            all_dec_str += indent_str + unparse(node.type) + " " + dec_str + ";"
        return all_dec_str
    elif isinstance(node, tree.VariableDeclarator):
        if node.initializer is not None:
            return "%s = %s" % (node.name, unparse(node.initializer))
        else:
            return node.name
    elif isinstance(node, tree.FormalParameter):
        return unparse(node.type) + " " + node.name

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
    elif isinstance(node, tree.ReturnStatement):
        return indent_str + "return %s;" % unparse(node.expression) if node.expression is not None else "return;"
    elif isinstance(node, tree.ThrowStatement):
        return indent_str + "throw %s;" % unparse(node.expression)
    elif isinstance(node, tree.TryStatement):
        block_stmts = [unparse(stmt, indent=indent+1) for stmt in node.block]
        catch_clauses = [unparse(catch, indent=indent) for catch in node.catches]
        if node.finally_block is None:
            return "%stry {\n%s\n} %s" % (indent_str, "\n".join(block_stmts), " ".join(catch_clauses))
        else:
            finally_stmts = [unparse(stmt, indent=indent+1) for stmt in node.finally_block]
            return "%stry {\n%s\n} %s finally {%s}" % (indent_str, "\n".join(block_stmts), " ".join(catch_clauses), "\n".join(finally_stmts))
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

    elif isinstance(node, tree.ForControl):
        if node.init is not None:
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

    elif isinstance(node, tree.Assignment):
        return "%s %s %s" % (unparse(node.expressionl), node.type, unparse(node.value))
    elif isinstance(node, tree.TernaryExpression):
        return "%s ? %s : %s" % (unparse(node.condition), unparse(node.if_true), unparse(node.if_false))
    elif isinstance(node, tree.BinaryOperation):
        return "%s %s %s" % (unparse(node.operandl), node.operator, unparse(node.operandr))
    elif isinstance(node, tree.Cast):
        return "(%s) %s" % (unparse(node.type), unparse(node.expression))

    elif isinstance(node, tree.Literal):
        prefix_str = "" if node.prefix_operators is None else "".join(node.prefix_operators)
        postfix_str = "" if node.postfix_operators is None else "".join(node.postfix_operators)
        return prefix_str + node.value + postfix_str
    elif isinstance(node, tree.This):
        if node.selectors is None or len(node.selectors) == 0:
            return "this"
        else:
            return "this.%s" % (".".join(unparse(e) for e in node.selectors))
    elif isinstance(node, tree.MemberReference):
        if node.qualifier is not None:
            core_name = node.member if len(node.qualifier) == 0 else node.qualifier + "." + node.member
        else:
            core_name = node.member
        prefix_str = "" if node.prefix_operators is None else "".join(node.prefix_operators)
        postfix_str = "" if node.postfix_operators is None else "".join(node.postfix_operators)
        return prefix_str + core_name + postfix_str
    elif isinstance(node, tree.MethodInvocation):
        mname = node.member if node.qualifier is None or len(node.qualifier) == 0 else node.qualifier + "." + node.member
        args = ", ".join(unparse(arg) for arg in node.arguments)
        if node.selectors is None or len(node.selectors) == 0:
            return "%s(%s)" % (mname, args)
        else:
            return "%s(%s).%s" % (mname, args, ".".join(unparse(e) for e in node.selectors))
    elif isinstance(node, tree.ClassReference):
        return "%s.class" % (unparse(node.type))

    elif isinstance(node, tree.ClassCreator):
        args = ", ".join(unparse(arg) for arg in node.arguments)
        return "new %s(%s)" % (unparse(node.type), args)
    else:
        raise NotImplementedError("Unparser for %s is not implemented" % type(node))

