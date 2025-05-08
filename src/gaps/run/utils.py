def extract_arguments(method_arg):
    i = 0
    args = []
    isArray = False
    while i < len(method_arg):
        # class or interface
        if method_arg[i] == "L":
            if method_arg[i - 1] == "[":
                isArray = True

            # check array
            if isArray:
                args.append(
                    "[L" + method_arg[i + 1 : method_arg.find(";")] + ";"
                )
                isArray = False
            else:
                args.append(method_arg[i + 1 : method_arg.find(";")])

            i = method_arg.find(";") + 1
            method_arg = method_arg.replace(";", " ", 1)

            continue

        # Int
        if method_arg[i] == "I":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[I")
                isArray = False
            else:
                args.append("int")

        # Boolean
        if method_arg[i] == "Z":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[Z")
                isArray = False
            else:
                args.append("boolean")

        # Float
        if method_arg[i] == "F":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[F")
                isArray = False
            else:
                args.append("float")

        # Long
        if method_arg[i] == "J":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[J")
                isArray = False
            else:
                args.append("long")

        # Double
        if method_arg[i] == "D":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[D")
                isArray = False
            else:
                args.append("double")

        # Char
        if method_arg[i] == "C":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[C")
                isArray = False
            else:
                args.append("char")

        # Byte
        if method_arg[i] == "B":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[B")
                isArray = False
            else:
                args.append("byte")

        # Short
        if method_arg[i] == "S":
            if method_arg[i - 1] == "[":
                isArray = True

            if isArray:
                args.append("[S")
                isArray = False
            else:
                args.append("short")

        i += 1

    return args


def create_javascript(class_method):
    if class_method == "CONDITIONAL":
        return ""
    javascript = "Java.perform(function() {\n"

    full_class_name = class_method.split(";->")[0][1:].replace("/", ".")
    class_name = "class_hook"
    javascript += (
        "    var " + class_name + " = Java.use('" + full_class_name + "');\n\n"
    )
    # extract method
    full_method_name = class_method.split(";->")[1]
    method_name = full_method_name.split("(")[0]
    if method_name == "<init>":
        method_name = "$init"
    method_arg = full_method_name.split("(")[1].split(")")[0]

    # args extract
    if len(method_arg) == 0:  # args is not exist
        javascript += (
            "    "
            + class_name
            + "."
            + method_name
            + ".overload().implementation = function(){\n"
        )
        javascript += (
            "        send('[Method] "
            + full_class_name
            + "."
            + method_name
            + "() reached');\n"
        )

        # create retval
        javascript += "        var retval = this." + method_name + "();\n"
        # return method
        javascript += "        return retval;\n"

        javascript += "    };\n\n"

    else:  # args exist
        args_list = extract_arguments(method_arg)

        args_string = ""
        args_len = len(args_list)
        args_quota_added = []

        for i in range(args_len):
            # replace / to .
            args_list[i] = args_list[i].replace("/", ".")
            args_quota_added.append("'" + args_list[i] + "'")
            # arg string create
            args_string += "arg" + str(i)
            # if last arg
            if i != args_len - 1:
                args_string += ","

        javascript += (
            "    "
            + class_name
            + "."
            + method_name
            + ".overload("
            + ",".join(args_quota_added)
            + ").implementation = function("
            + args_string
            + "){\n"
        )

        # print hook method name
        javascript += (
            "        send('[Method] "
            + full_class_name
            + "."
            + method_name
            + "("
            + ",".join(args_list)
            + ") reached');\n"
        )

        # create retval
        javascript += (
            "        var retval = this."
            + method_name
            + "("
            + args_string
            + ");\n"
        )

        # return method
        javascript += "        return retval;\n"

        javascript += "    };\n\n"

    javascript += "});\n"
    return javascript


def to_java_signature(smali_sig):
    # Split the smali signature into class, method, and parameters
    class_and_method, params_and_return = smali_sig.split(";->")
    class_name = class_and_method[1:].replace(
        "/", "."
    )  # Remove 'L' and replace '/' with '.'
    method_name, params_and_return = params_and_return.split("(")
    params, return_type = params_and_return.split(")")

    # Convert parameters from smali to Java format
    java_params = []
    i = 0
    while i < len(params):
        if params[i] == "[":
            array_type = ""
            while params[i] == "[":
                array_type += "[]"
                i += 1
            if params[i] == "L":
                end = params.index(";", i)
                java_params.append(
                    params[i + 1 : end].replace("/", ".") + array_type
                )
                i = end + 1
            else:
                java_params.append(
                    java_to_dalvik_type_reverse(params[i]) + array_type
                )
                i += 1
        elif params[i] == "L":
            end = params.index(";", i)
            java_params.append(params[i + 1 : end].replace("/", "."))
            i = end + 1
        else:
            java_params.append(java_to_dalvik_type_reverse(params[i]))
            i += 1

    # Convert return type from smali to Java format
    java_return_type = java_to_dalvik_type_reverse(return_type)

    # Format the final Java signature
    return f"<{class_name}: {java_return_type} {method_name}({', '.join(java_params)})>"


def java_to_dalvik_type_reverse(dtype):
    reverse_mapping = {
        "I": "int",
        "V": "void",
        "Z": "boolean",
        "C": "char",
        "B": "byte",
        "S": "short",
        "J": "long",
        "F": "float",
        "D": "double",
    }
    return reverse_mapping.get(dtype, dtype)
