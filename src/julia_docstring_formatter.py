import re
import sys


def format_docstrings(text, thres_len = 92):
    lines_orig = re.split('\n', text)
    lines_edited = []

    iline_docstring_head = -1
    iline_docstring_tail = -1  
    iline = 0

    while iline < len(lines_orig):
        # Detect the first line of a function
        line = lines_orig[iline]
        isfunc = \
            iline_docstring_tail > -1 or \
            re.match('^\s*function', line) is not None or \
            re.match('^\S+\(', line) is not None

        if isfunc:
            if re.match('\s+', line) is not None:
                indent = line[0:re.match('\s+', line).end()]
            else:
                indent = ''
            
            signature, arg_names, arg_types, kwarg_names, kwarg_types, return_types \
                = extract_signature(lines_orig, iline)

            signature, contains_type \
                = shorten_signature(signature, arg_types, kwarg_types, thres_len)

            docstring_lines = make_docstring_lines(
                indent,
                signature,
                not contains_type,  # If the signature contains types, docstring don't contain the types.
                arg_names,
                arg_types,
                kwarg_names,
                kwarg_types,
                return_types,
                lines_orig,
                iline_docstring_head,
                iline_docstring_tail
            )

            lines_edited += docstring_lines
            lines_edited.append(line)

            iline_docstring_head = -1
            iline_docstring_tail = -1
            iline += 1
        else:
            iline_docstring_head = -1
            iline_docstring_tail = -1

            # Detect the first line of a docstring
            if re.match('^\s*"""\s*', lines_orig[iline]) is None:
                lines_edited.append(line)
                iline += 1
                continue

            iline_docstring_head = iline
            iline += 1

            # Proceed to the end of the docstring
            while re.match('^\s*"""\s*', lines_orig[iline]) is None:
                iline += 1

            iline_docstring_tail = iline
            iline += 1
    
    return '\n'.join(lines_edited)
    

def extract_signature(lines, iline):
    line = lines[iline]
    line = re.sub('^\s*function\s+', '', line)

    signature = ''
    return_types = []
    stack = 0
       
    while True:
        for i in range(0, len(line)):
            c = line[i]
            signature += c
            if c == '(':
                stack += 1
            if c == ')':
                stack -= 1
                if stack == 0:
                    return_types = extract_return_types(line[i+1:])
                    break             
        if stack == 0:
            break
        iline += 1
        line = re.sub('^\s+', '' if line[len(line)-1] == '(' else ' ', lines[iline])

    if signature[len(signature)-2:] == ',)':
        signature = signature[:len(signature)-2] + ')'

    arg_names, arg_types, kwarg_names, kwarg_types = extract_arguments(signature)
    
    return signature, arg_names, arg_types, kwarg_names, kwarg_types, return_types


def extract_return_types(line):
    return_types = []
    
    if line[0:len('::')] == '::':
        # Ignore outermost 'Tuple'
        line = line[len('::Tuple{'):] \
            if line[0:len('::Tuple{')] == '::Tuple{' \
            else line[len('::'):]
        
        return_type = ''
        stack = 0

        for c in line:
            if stack == 0 and c == '}':
                break
            
            if stack == 0 and len(return_type) > 0 and c in {',', ' ', '='}:
                return_types.append(return_type)
                return_type = ''
                continue
                
            if len(return_type) > 0 or c not in {',', ' ', '='}:
                return_type += c
              
            if c == '{':
                stack += 1
            if c == '}':
                stack -= 1
        
        if len(return_type) > 0:
            return_types.append(return_type)
    
    return return_types


def extract_arguments(signature):
    body = signature[signature.find('(') + 1:signature.rfind(')')]

    arg_names = []
    arg_types = {}
    kwarg_names = []
    kwarg_types = {}
    
    arg_name = ''
    arg_type = ''
    has_colon = False
    has_semicolon = False
    stack = 0
    
    for c in body:
        if len(arg_name) == 0 and c == ' ':
            continue
        elif c == ':':
            has_colon = True
        elif c == ';':
            arg_names.append(arg_name)
            arg_types[arg_name] = arg_type
            arg_name = ''
            arg_type = ''
            has_colon = False
            has_semicolon = True
        elif c in {'(', '{'}:
            arg_type += c
            stack += 1
        elif c in {')', '}'}:
            arg_type += c
            stack -= 1
        elif stack == 0 and c == ',':
            if has_semicolon:
                kwarg_names.append(arg_name)
                kwarg_types[arg_name] = arg_type
            else:
                arg_names.append(arg_name)
                arg_types[arg_name] = arg_type                
            arg_name = ''            
            arg_type = ''
            has_colon = False
        elif has_colon:
            arg_type += c
        else:
            arg_name += c

    if has_semicolon:
        kwarg_names.append(arg_name)
        kwarg_types[arg_name] = arg_type
    else:
        arg_names.append(arg_name)
        arg_types[arg_name] = arg_type
    
    return arg_names, arg_types, kwarg_names, kwarg_types


def shorten_signature(signature, arg_types, kwarg_types, thres_len):
    contains_type = True

    if len(signature) <= thres_len:
        return signature, contains_type

    # Remove types
    contains_type = False
    
    for arg_name, arg_type in arg_types.items():
        if '=' in arg_type:
            signature = signature.replace('::'+ arg_type[0:arg_type.find(' =')], '')
        else:
            signature = signature.replace('::'+ arg_type, '')

    for arg_name, arg_type in kwarg_types.items():
        if '=' in arg_type:
            signature = signature.replace('::'+ arg_type[0:arg_type.find(' =')], '')
        else:
            signature = signature.replace('::'+ arg_type, '')

    if len(signature) <= thres_len:
        return signature, contains_type

    # Replace keywords arguments with '<keyword arguments>', if it's going to be short.
    kwarg_names = kwarg_types.keys()        
    if len(signature) <= thres_len or len(', '.join(kwarg_names)) > len('<keyword arguments>'):
        signature = signature[0:signature.find(';')] + '; <keyword arguments>)'

    if len(signature) <= thres_len:
        return signature, contains_type

    # Remove default values
    for arg_name, arg_type in arg_types.items():
        signature = signature.replace(arg_type[arg_type.find(' ='):], '')

    for arg_name, arg_type in kwarg_types.items():
        signature = signature.replace(arg_type[arg_type.find(' ='):], '')
    
    return signature, contains_type    


def make_docstring_lines(indent, signature, contains_type, arg_names, arg_types, kwarg_names, kwarg_types, return_types, lines_orig, iline_docstring_head, iline_docstring_tail):
    arg_docstrings = {} if iline_docstring_head == -1 \
        else extract_arg_docstrings(lines_orig, iline_docstring_head, iline_docstring_tail, arg_names, kwarg_names)

    docstring_lines = []
    docstring_lines.append(indent +'\"\"\"')
    docstring_lines.append(indent +(' ' * 4) + signature)

    is_signature_line = True

    for iline in range(iline_docstring_head + 1, iline_docstring_tail):
        line = lines_orig[iline][len(indent):]

        if re.match('^# Arguments', line) is not None:
            break

        if re.match('\s+', line) is None:
            is_signature_line = False

        if not is_signature_line:
            docstring_lines.append(indent + line)

    # Insert an empty line before '# Arguments' line.
    if re.match('\S', docstring_lines[len(docstring_lines)-1]) is not None:
        docstring_lines.append(indent)

    docstring_lines.append(indent +'# Arguments')
    
    for arg_name in arg_names:
        docstring = arg_docstrings[arg_name] if arg_name in arg_docstrings else ' '

        arg_type = arg_types[arg_name]
        if contains_type:
            docstring_lines.append(indent +'- `'+ arg_name +'::'+ arg_type +'`:'+ docstring)
        else:
            docstring_lines.append(indent +'- '+ arg_name +':'+ docstring)
            
    for arg_name in kwarg_names:
        docstring = arg_docstrings[arg_name] if arg_name in arg_docstrings else ' '
        
        arg_type = kwarg_types[arg_name]
        if contains_type:
            docstring_lines.append(indent +'- `; '+ arg_name +'::'+ arg_type +'`:'+ docstring)
        else:
            docstring_lines.append(indent +'- ; '+ arg_name +':'+ docstring)
    
    return_docstring_added = False

    for iline in range(iline_docstring_head + 1, iline_docstring_tail):
        line = lines_orig[iline][len(indent):]

        if re.match('^# Returns', line) is None:
            continue

        docstring_lines.append(indent)

        for iline2 in range(iline, iline_docstring_tail):
            line = lines_orig[iline2][len(indent):]
            docstring_lines.append(indent + line)
            return_docstring_added = True
        break

    if not return_docstring_added and len(return_types) > 0:
        docstring_lines.append('')
        docstring_lines.append(indent +'# Returns')
        for return_type in return_types:
            docstring_lines.append(indent +'- '+ return_type +': ')
        
    docstring_lines.append(indent +'\"\"\"')
    return docstring_lines


def extract_arg_docstrings(lines_orig, iline_docstring_head, iline_docstring_tail, arg_names, kwarg_names):
    arg_docstrings = {}

    for iline in range(iline_docstring_head + 1, iline_docstring_tail):
        line = lines_orig[iline]
            
        if re.match('^\s*-\s', line) is None:
            continue
        
        for arg_name in arg_names:
            if re.match('^\s*-\s`?'+ arg_name +':', line):
                i1 = line.rfind('::')
                i2 = line.rfind(':')                
                if i2 > i1 + 1:
                    arg_docstrings[arg_name] = line[line.rfind(':') + 1:]
                break

        for arg_name in kwarg_names:
            if re.match('^\s*-\s`?(; )?'+ arg_name +':', line):
                i1 = line.rfind('::')
                i2 = line.rfind(':')                
                if i2 > i1 + 1:
                    arg_docstrings[arg_name] = line[line.rfind(':') + 1:]
                break

    return arg_docstrings


def main():
    file = sys.argv[1]
    thres_len = int(sys.argv[2]) if len(sys.argv) >= 3 else 92
    
    with open(file, encoding='utf-8') as f:
        text = format_docstrings(f.read(), thres_len)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


if __name__ == '__main__':
    main()
