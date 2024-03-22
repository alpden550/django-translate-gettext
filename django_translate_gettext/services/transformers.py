import ast
from _ast import stmt
from contextlib import suppress


class ClassDefTransformer(ast.NodeTransformer):
    @staticmethod
    def build_new_call_node(*, constant: str) -> ast.Call:
        return ast.Call(func=ast.Name(id="_", ctx=ast.Load()), args=[ast.Constant(constant)], keywords=[])

    def build_args_node(self, *, args: list[ast.Dict | ast.Constant | ast.expr]) -> list[ast.Dict | ast.Constant]:
        if args and isinstance(args[0], ast.Dict):
            dict_args: ast.Dict = args[0]
            param = dict_args.values[0]

            if hasattr(param, "func"):
                return args

            new_node = self.build_new_call_node(constant=param.value)
            args[0].values[0] = new_node
            return args
        if args and isinstance(args[0], ast.Constant):
            constant = args[0]
            new_node = self.build_new_call_node(constant=constant.value)
            args[0] = new_node
        return args

    def build_keywords_node_for_arg(self, *, keywords: list[ast.keyword], arg_name: str) -> list[ast.keyword]:
        if not keywords:
            return keywords
        message = next((keyword for keyword in keywords if keyword.arg == arg_name), None)
        if message and isinstance(message.value, ast.Constant):
            constant = message.value
            new_node = self.build_new_call_node(constant=constant.value)
            message.value = new_node
        return keywords

    def generate_tuple_gettext(self, *, value: ast.Tuple | stmt) -> ast.Tuple:
        last_constant = value.elts[-1]
        if isinstance(last_constant, ast.Constant):
            value.elts[-1] = self.build_new_call_node(constant=last_constant.value)
        return value

    def generate_class_boby_gettext(self, *, body: ast.Assign, instance: ast.ClassDef | stmt):
        if isinstance(body.value, ast.Constant):
            constant = body.value.value
            new_node = self.build_new_call_node(constant=constant)
            body.value = new_node

        if isinstance(body.value, ast.Tuple) and body.value.elts:
            if instance.name == "Meta":
                return None
            body.value = self.generate_tuple_gettext(value=body.value)

        return body

    def generate_class_gettext(self, *, instance: ast.ClassDef | stmt) -> ast.ClassDef:
        for body in instance.body:
            if not isinstance(body, ast.Assign) or body.targets[-1].id == "abstract":
                continue
            if instance.name == "Meta" and not body.targets[-1].id.startswith("verbose"):
                continue

            self.generate_class_boby_gettext(body=body, instance=instance)

        return instance

    def append_verbose_name(self, *, instance: ast.Assign | stmt) -> ast.Assign:
        constant = instance.targets[-1]
        new_node = self.build_new_call_node(constant=constant.id.title())
        instance.value.keywords.insert(0, ast.keyword(arg="verbose_name", value=new_node))

        return instance

    def generate_fk_gettext(self, *, instance: ast.Assign | stmt) -> ast.Assign:
        verbose = next((keyword for keyword in instance.value.keywords if keyword.arg == "verbose_name"), None)
        if verbose is None:
            self.append_verbose_name(instance=instance)
        else:
            constant = verbose.value
            if not isinstance(constant, ast.Constant):
                return instance
            new_node = self.build_new_call_node(constant=constant.value)
            verbose.value = new_node
        return instance

    def generate_assign_args_gettext(self, *, instance: ast.Assign | stmt) -> ast.Assign:
        if not instance.value.args and not instance.value.keywords:
            constant = instance.targets[-1]
            new_node = self.build_new_call_node(constant=constant.id.title())
            instance.value.args.append(new_node)
            return instance

        if instance.value.args:
            instance.value.args = self.build_args_node(args=instance.value.args)
        return instance

    def generate_keyword_gettext(self, *, keyword: ast.keyword) -> ast.keyword:
        if keyword.arg in ("verbose_name", "help_text"):
            constant = keyword.value
            if not isinstance(constant, ast.Constant):
                return keyword
            new_node = self.build_new_call_node(constant=constant.value)
            keyword.value = new_node
        return keyword

    def generate_assign_keywords_gettext(self, *, instance: ast.Assign | stmt) -> ast.Assign:
        if not instance.value.keywords:
            return instance

        for keyword in instance.value.keywords:
            self.generate_keyword_gettext(keyword=keyword)

        verbose = next((keyword for keyword in instance.value.keywords if keyword.arg == "verbose_name"), None)
        if not instance.value.args and verbose is None:
            self.append_verbose_name(instance=instance)

        return instance

    def generate_assign_gettext(self, *, instance: ast.Assign | stmt) -> ast.Assign:
        if instance.targets[-1].id == "objects":
            return instance

        with suppress(AttributeError):
            f_keys = ("ForeignKey", "ManyToManyField", "OneToOneField")
            func = instance.value.func
            if (hasattr(func, "attr") and func.attr in f_keys) or hasattr(func, "id"):
                self.generate_fk_gettext(instance=instance)
                return instance

        if isinstance(instance.value, ast.Tuple) and not instance.value.dims:
            instance.value = self.generate_tuple_gettext(value=instance.value)
            return instance

        try:
            self.generate_assign_args_gettext(instance=instance)
        except AttributeError:
            return instance

        self.generate_assign_keywords_gettext(instance=instance)

        return instance

    def generate_decorator_gettext(self, *, decorator: ast.Call | stmt, instance_name: str) -> ast.Call:
        for keyword in decorator.keywords:
            if keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                constant = keyword.value
                new_node = self.build_new_call_node(constant=constant.value.title())
                keyword.value = new_node

        description = next((keyword for keyword in decorator.keywords if keyword.arg == "description"), None)
        if description is None:
            decorator.keywords.append(
                ast.keyword(
                    arg="description",
                    value=self.build_new_call_node(constant=instance_name.replace("_", " ").title()),
                )
            )
        return decorator

    def generate_display_decorator_gettext(self, *, instance: ast.FunctionDef | stmt) -> ast.FunctionDef:
        decorators = instance.decorator_list
        for decorator in decorators:
            if not isinstance(decorator, ast.Call) and (
                hasattr(decorator, "func") and decorator.func.attr != "display"
            ):
                continue
            self.generate_decorator_gettext(decorator=decorator, instance_name=instance.name)

        return instance

    def generate_elt_gettext(self, *, elts: list[ast.Call]) -> list[ast.Call]:
        for elt in elts:
            if elt.args:
                elt.args = self.build_args_node(args=elt.args)
            elif elt.keywords:
                elt.keywords = self.build_keywords_node_for_arg(keywords=elt.keywords, arg_name="message")
        return elts

    def generate_raise_gettext(self, *, instance: ast.Raise | stmt) -> ast.Raise:
        exc = instance.exc

        if hasattr(exc, "elts") and exc.elts:
            self.generate_elt_gettext(elts=exc.elts)
        if hasattr(exc, "args") and exc.args:
            exc.args = self.build_args_node(args=exc.args)
            return instance
        if hasattr(exc, "keywords") and exc.keywords:
            exc.keywords = self.build_keywords_node_for_arg(keywords=exc.keywords, arg_name="message")
            return instance

        return instance

    def generate_funcdef_raising_gettext(self, *, instance: ast.FunctionDef | stmt) -> ast.FunctionDef:
        for body in instance.body:
            for item in body.body:
                if not isinstance(item, ast.Raise):
                    continue
                self.generate_raise_gettext(instance=item)

        return instance

    @staticmethod
    def insert_getetxt_import(node: ast.Module) -> ast.Module:
        aliases = [body.names[-1].name for body in node.body if isinstance(body, ast.ImportFrom)]
        if "gettext_lazy" in aliases:
            return node

        counted_imports = len([
            import_node for import_node in node.body if isinstance(import_node, (ast.ImportFrom, ast.Import))
        ])

        import_node = ast.ImportFrom(
            module="django.utils.translation",
            names=[ast.alias(name="gettext_lazy", asname="_")],
            level=0,
        )
        node.body.insert(counted_imports, import_node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:  # noqa: N802
        match node:
            case ast.ClassDef(bases=[ast.Attribute(attr="ModelAdmin")]):
                for instance in node.body:
                    match instance:
                        case ast.FunctionDef(decorator_list=[ast.Call(keywords=[*_])]):
                            self.generate_display_decorator_gettext(instance=instance)

            case ast.ClassDef(bases=[ast.Attribute(attr="TextChoices")]):
                return self.generate_class_gettext(instance=node)

            case ast.ClassDef(bases=[ast.Name(id=_), *_]):
                for instance in node.body:
                    match instance:
                        case ast.ClassDef():
                            self.generate_class_gettext(instance=instance)
                        case ast.Assign():
                            self.generate_assign_gettext(instance=instance)
                        case ast.FunctionDef(body=[ast.If()]):
                            self.generate_funcdef_raising_gettext(instance=instance)
                        case ast.FunctionDef(decorator_list=[ast.Call(keywords=[*_])]):
                            self.generate_display_decorator_gettext(instance=instance)

            case ast.ClassDef(bases=[ast.Attribute(attr=a)]) if a == "Model":
                for instance in node.body:
                    match instance:
                        case ast.Assign():
                            self.generate_assign_gettext(instance=instance)

        return node
